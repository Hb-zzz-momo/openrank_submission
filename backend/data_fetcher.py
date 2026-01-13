# backend/data_fetcher.py
"""
OpenDigger 数据同步模块
负责从 OpenDigger API 拉取数据并存入本地数据库
"""
import json
import shutil
from pathlib import Path
import requests
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
import time
from extensions import db
from models import MetricSeries
from flask import Flask
from datetime import datetime
import json as pyjson
from contextlib import nullcontext

# ✅ 导入统一的工具函数
from metric_utils import mean as _mean, std_population as _std_pop, tail_n_values, calculate_health_score

BACKEND_ROOT = Path(__file__).parent
CONFIG_FILE = BACKEND_ROOT / "config.json"
DATA_DIR = BACKEND_ROOT / "data"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(exist_ok=True)


# ✅ 辅助函数：兼容旧代码
def _tail12(records):
    """获取最近12个月数据的包装函数"""
    return tail_n_values(records, n=12, month_key="month", value_key="count")

def generate_llm_summary_db():
    with ensure_app_context():
        print("--- [SUMMARY] 开始生成 LLM 生态汇总（DB版） ---")

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        repos = config.get("repositories", [])

        summary_items = []

        for repo_info in repos:
            platform = repo_info["platform"]
            org = repo_info["org"]
            repo = repo_info["repo"]
            category = repo_info.get("category", "unknown")
            repo_key = f"{platform}/{org}/{repo}"

            # 从 DB 取 openrank / activity
            row_or = MetricSeries.query.filter_by(platform=platform, entity=org, repo=repo, metric="openrank").first()
            row_act = MetricSeries.query.filter_by(platform=platform, entity=org, repo=repo, metric="activity").first()

            if not row_or or not row_act:
                print(f"--- [WARN] 略过 {repo_key}，openrank 或 activity DB 数据缺失 ---")
                continue

            try:
                or_records = pyjson.loads(row_or.data_json or "[]")
                act_records = pyjson.loads(row_act.data_json or "[]")

                or_vals = _tail12(or_records)
                act_vals = _tail12(act_records)

                if not or_vals or not act_vals:
                    print(f"--- [WARN] 略过 {repo_key}，近12月数据不足 ---")
                    continue

                openrank_mean_12m = _mean(or_vals)
                openrank_std_12m = _std_pop(or_vals)
                activity_mean_12m = _mean(act_vals)

                summary_items.append({
                    "platform": platform,
                    "org": org,
                    "repo": repo,
                    "project_key": repo_key,
                    "category": category,
                    "openrank_mean_12m": float(openrank_mean_12m),
                    "openrank_std_12m": float(openrank_std_12m),
                    "activity_mean_12m": float(activity_mean_12m),
                })

            except Exception as e:
                print(f"--- [WARN] 处理 {repo_key} 汇总失败: {e} ---")

        if not summary_items:
            print("--- [SUMMARY] 没有可用项目生成汇总 ---")
            return

        max_or = max(i["openrank_mean_12m"] for i in summary_items) or 1.0
        max_act = max(i["activity_mean_12m"] for i in summary_items) or 1.0
        max_std = max(i["openrank_std_12m"] for i in summary_items) or 1.0

        for item in summary_items:
            or_norm = item["openrank_mean_12m"] / max_or if max_or > 0 else 0.0
            act_norm = item["activity_mean_12m"] / max_act if max_act > 0 else 0.0
            std_norm = item["openrank_std_12m"] / max_std if max_std > 0 else 0.0
            
            # ✅ 稳定性 = 1 - 波动性归一化值
            stability_norm = 1.0 - std_norm

            # ✅ 使用统一的健康度计算函数
            item["health_score"] = calculate_health_score(or_norm, act_norm, stability_norm)
            
            item["openrank_mean_12m"] = round(item["openrank_mean_12m"], 2)
            item["activity_mean_12m"] = round(item["activity_mean_12m"], 2)
            item["openrank_std_12m"] = round(item["openrank_std_12m"], 2)

        summary_file = DATA_DIR / "llm_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_items, f, ensure_ascii=False, indent=2)

        print(f"--- [SUMMARY] 已生成 LLM 生态汇总: {summary_file} ---")


def ensure_app_context():
    try:
        from flask import current_app
        _ = current_app.name
        return nullcontext()
    except Exception:
        app = Flask("data_fetcher")
        db_path = BACKEND_ROOT / "openrank.db"
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        return app.app_context()
    
def auto_cleanup_repos(config, invalid_repos):
    """
    自动从 config.json 移除无效项目
    在数据同步时自动调用
    """
    if not invalid_repos:
        return
    
    print(f"\n--- [CLEANUP] 开始自动清理 {len(invalid_repos)} 个无效项目 ---")
    
    # 构建无效项目的 key 集合
    invalid_keys = {f"{r['org']}/{r['repo']}" for r in invalid_repos}
    
    # 过滤出有效项目
    valid_repos = [
        r for r in config["repositories"]
        if f"{r['org']}/{r['repo']}" not in invalid_keys
    ]
    
    # 备份原配置
    backup_file = CONFIG_FILE.with_suffix(".json.bak")
    shutil.copy(CONFIG_FILE, backup_file)
    print(f"📦 已备份原配置: {backup_file}")
    
    # 更新配置
    config["repositories"] = valid_repos
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已从 config.json 移除 {len(invalid_repos)} 个无效项目:")
    for r in invalid_repos:
        print(f"   - {r['org']}/{r['repo']}")
    
    # 清理数据库残留
    try:
        with ensure_app_context():
            deleted = 0
            for repo_info in invalid_repos:
                rows = MetricSeries.query.filter_by(
                    platform=repo_info["platform"],
                    entity=repo_info["org"],
                    repo=repo_info["repo"]
                ).all()
                for row in rows:
                    db.session.delete(row)
                    deleted += 1
            db.session.commit()
            if deleted:
                print(f"🗑️  已清理数据库 {deleted} 条残留记录")
    except Exception as e:
        print(f"⚠️  数据库清理跳过: {e}")
    
    print("--- [CLEANUP] 清理完成 ---\n")

def sync_opendigger_data():
    print("--- [FETCH] 开始同步OpenDigger数据 ---")

    with ensure_app_context():
        db.create_all()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            repos = config["repositories"]
            metrics = config["metrics"]
            base_url = config["data_source"]["base_url"]
        except Exception as e:
            print(f"--- [错误] 读取配置失败: {e} ---")
            return

        # 记录每个项目的失败指标
        repo_failures = {}  # key: "org/repo", value: set of failed metrics
        core_metrics = {"openrank", "activity"}  # 核心指标，全部失败才算无效

        for repo_info in repos:
            platform, org, repo = repo_info["platform"], repo_info["org"], repo_info["repo"]
            repo_key = f"{org}/{repo}"
            repo_failures[repo_key] = set()

            for metric in metrics:
                api_url = base_url.format(platform=platform, org=org, repo=repo, metric=metric)

                try:
                    resp = requests.get(api_url, timeout=30, verify=False)
                    resp.raise_for_status()
                    data = resp.json()

                    if not isinstance(data, dict):
                        raise ValueError("数据格式非键值对(dict)")

                    formatted_data = [
                        {"month": k, "count": v}
                        for k, v in data.items()
                        if isinstance(k, str) and len(k) == 7 and "-" in k
                    ]
                    if not formatted_data:
                        raise ValueError("无有效时间数据")

                    row = MetricSeries.query.filter_by(
                        platform=platform, entity=org, repo=repo, metric=metric
                    ).first()

                    payload = pyjson.dumps(formatted_data, ensure_ascii=False)

                    if row:
                        row.data_json = payload
                    else:
                        db.session.add(MetricSeries(
                            platform=platform, entity=org, repo=repo,
                            metric=metric, data_json=payload
                        ))

                    db.session.commit()
                    print(f"✅ 成功写入DB: {platform}/{org}/{repo} - {metric}")

                except requests.HTTPError as e:
                    code = getattr(e.response, "status_code", None)
                    if code == 404:
                        print(f"❌ 跳过 (404): {platform}/{org}/{repo} - {metric}")
                        repo_failures[repo_key].add(metric)
                    else:
                        print(f"❌ HTTP错误: {platform}/{org}/{repo} - {metric} -> {e}")
                except Exception as e:
                    print(f"❌ 处理失败: {platform}/{org}/{repo} - {metric} -> {e}")

        print("--- [FETCH] 数据同步完成 ---")

        # === 自动清理无效项目 ===
        invalid_repos = []
        for repo_info in repos:
            repo_key = f"{repo_info['org']}/{repo_info['repo']}"
            failed_metrics = repo_failures.get(repo_key, set())
            
            # 核心指标全部失败 → 无效项目
            if core_metrics.issubset(failed_metrics):
                invalid_repos.append(repo_info)
                print(f"⚠️  检测到无效项目: {repo_key}")

        if invalid_repos:
            auto_cleanup_repos(config, invalid_repos)

        # 同步完后生成汇总（从DB读）
        try:
            generate_llm_summary_db()
        except Exception as e:
            print(f"--- [WARN] 生成 LLM 生态汇总失败: {e} ---")

def should_sync(ttl_hours: int = 24) -> bool:
    summary_file = DATA_DIR / "llm_summary.json"

    # DB为空或表不存在也要同步
    with ensure_app_context():
        try:
            db.create_all()
            if MetricSeries.query.first() is None:
                return True
        except Exception:
            return True

    if not summary_file.exists():
        return True

    age_seconds = time.time() - summary_file.stat().st_mtime
    return age_seconds > ttl_hours * 3600


def run_sync(force: bool = False, ttl_hours: int = 24):
    """给 Flask 启动时调用的入口"""
    if not force and not should_sync(ttl_hours=ttl_hours):
        print(f"--- [FETCH] 跳过同步：llm_summary.json 在 {ttl_hours}h 内已更新 ---")
        return
    sync_opendigger_data()
if __name__ == "__main__":
    run_sync(force=True)  # 手动运行时强制全量同步