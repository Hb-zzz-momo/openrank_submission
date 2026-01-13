# backend/api/opendigger.py
"""
本文件 = 所有后端接口的蓝图（Blueprint）
路径统一以 /api 开头，例如：
  /api/platforms
  /api/entities/github
  /api/data/github/pytorch/pytorch/openrank
  /api/llm/summary
  /api/llm/report
"""

from flask import Blueprint, jsonify, request
from pathlib import Path
import json
import requests
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
from datetime import datetime, timedelta
from extensions import db
from models import MetricSeries

# ✅ 导入统一的工具函数
from metric_utils import mean as _mean, std_population as _std_pop, tail_n_values, calculate_health_score
from rate_limiter import rate_limit
# OpenAI 客户端
try:
    from openai import OpenAI  # openai>=1.x
    openai_client = OpenAI()   # 会自动读 OPENAI_API_KEY 环境变量
except Exception:
    openai_client = None

# 导入你自己的元数据模块
import metadata as meta

# ==== 基础路径 ====
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = BASE_DIR / "config.json"

# 内存缓存，避免频繁刷新页面时每次都重算
_LLM_SUMMARY_CACHE = {"ts": None, "data": None}
LLM_CACHE_TTL_SECONDS = 300  # 5分钟


# ✅ 辅助函数：获取最近12个月数据（使用统一工具）
def _tail12_values(records):
    """兼容旧代码的包装函数"""
    return tail_n_values(records, n=12, month_key="month", value_key="count")


def compute_llm_summary_from_db():
    """
    从数据库计算 LLM 生态汇总数据
    优化：使用批量查询替代 N+1 查询，显著提升性能
    """
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        raise ApiException(500, f"读取 config.json 失败: {e}")

    repos = config.get("repositories", [])
    
    if not repos:
        raise ApiException(404, "配置文件中没有定义任何仓库")

    # ✅ 优化：一次性批量查询所有需要的 MetricSeries（只执行 1 次 SQL）
    all_series = MetricSeries.query.filter(
        MetricSeries.metric.in_(["openrank", "activity"])
    ).all()
    
    # ✅ 构建内存索引：{(platform, entity, repo, metric): row}
    # 后续查找时间复杂度 O(1)，不再触发 SQL
    series_map = {}
    for row in all_series:
        key = (row.platform, row.entity, row.repo, row.metric)
        series_map[key] = row
    
    summary_items = []

    for repo_info in repos:
        platform = repo_info["platform"]
        org = repo_info["org"]
        repo = repo_info["repo"]
        category = repo_info.get("category", "unknown")
        repo_key = f"{platform}/{org}/{repo}"

        # ✅ 从内存索引中 O(1) 查找，不触发数据库查询
        row_or = series_map.get((platform, org, repo, "openrank"))
        row_act = series_map.get((platform, org, repo, "activity"))

        if not row_or or not row_act:
            continue

        try:
            or_records = json.loads(row_or.data_json or "[]")
            act_records = json.loads(row_act.data_json or "[]")

            or_vals = _tail12_values(or_records)
            act_vals = _tail12_values(act_records)

            if not or_vals or not act_vals:
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
        except Exception:
            continue

    if not summary_items:
        raise ApiException(404, "数据库中没有可用项目数据，请先触发数据同步（run_sync）")

    # 归一化 + health_score
    max_or = max(i["openrank_mean_12m"] for i in summary_items) or 1.0
    max_act = max(i["activity_mean_12m"] for i in summary_items) or 1.0
    max_std = max(i["openrank_std_12m"] for i in summary_items) or 1.0

    for item in summary_items:
        or_norm = item["openrank_mean_12m"] / max_or if max_or > 0 else 0.0
        act_norm = item["activity_mean_12m"] / max_act if max_act > 0 else 0.0
        std_norm = item["openrank_std_12m"] / max_std if max_std > 0 else 0.0
        
        # 稳定性 = 1 - 波动性归一化值
        stability_norm = 1.0 - std_norm

        # 使用统一的健康度计算函数
        item["health_score"] = calculate_health_score(or_norm, act_norm, stability_norm)
        
        item["openrank_mean_12m"] = round(item["openrank_mean_12m"], 2)
        item["activity_mean_12m"] = round(item["activity_mean_12m"], 2)
        item["openrank_std_12m"] = round(item["openrank_std_12m"], 2)

    return summary_items

def get_llm_summary_cached(force: bool = False):
    if force:
        data = compute_llm_summary_from_db()
        _LLM_SUMMARY_CACHE["ts"] = datetime.utcnow()
        _LLM_SUMMARY_CACHE["data"] = data
        return data

    ts = _LLM_SUMMARY_CACHE["ts"]
    if ts and (datetime.utcnow() - ts).total_seconds() < LLM_CACHE_TTL_SECONDS:
        return _LLM_SUMMARY_CACHE["data"]

    data = compute_llm_summary_from_db()
    _LLM_SUMMARY_CACHE["ts"] = datetime.utcnow()
    _LLM_SUMMARY_CACHE["data"] = data
    return data

# ==== 定义 Blueprint ====
api_bp = Blueprint("api", __name__, url_prefix="/api")


# ==== 自定义异常 + 统一 JSON 返回 ====

class ApiException(Exception):
    """简单的 API 异常：带 status_code 和 detail 字段"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@api_bp.errorhandler(ApiException)
def handle_api_exception(e: ApiException):
    """蓝图级别的错误处理：把 ApiException 转成 JSON"""
    return jsonify({"detail": e.detail}), e.status_code


# ==== 公共工具函数：抓取 & 缓存 OpenDigger 数据 ====

CACHE_TTL_HOURS = 24

def fetch_and_cache_data_db(api_url: str, platform: str, entity: str, repo: str | None, metric: str):
    repo_key = repo or ""  # ⭐ 统一 repo 为空时存 ""

    row = MetricSeries.query.filter_by(
        platform=platform, entity=entity, repo=repo_key, metric=metric
    ).first()

    # 1) 命中缓存且未过期
    if row and row.updated_at:
        if datetime.utcnow() - row.updated_at < timedelta(hours=CACHE_TTL_HOURS):
            if hasattr(row, "to_records"):
                return {"data": row.to_records(), "cached": True}
            return {"data": json.loads(row.data_json or "[]"), "cached": True}

    # 2) 缓存没有/过期：请求 OpenDigger（把上游错误转成 ApiException）
    try:
        resp = requests.get(api_url, timeout=30, verify=False)
        resp.raise_for_status()
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", None)
        if code == 404:
            raise ApiException(404, "OpenDigger 无该指标数据（404）")
        raise ApiException(502, f"OpenDigger 上游 HTTP 错误：{code}")
    except requests.RequestException as e:
        raise ApiException(502, f"请求 OpenDigger 失败：{e}")

    data = resp.json()
    if not isinstance(data, dict):
        raise ApiException(502, "OpenDigger 返回格式异常（非 dict）")

    formatted_data = [
        {"month": k, "count": v}
        for k, v in data.items()
        if isinstance(k, str) and len(k) == 7 and k.count("-") == 1
    ]
    if not formatted_data:
        raise ApiException(404, "无有效月度数据")

    payload = json.dumps(formatted_data, ensure_ascii=False)

    # 3) upsert 写回 DB（repo 用 repo_key）
    if row:
        row.data_json = payload
    else:
        row = MetricSeries(
            platform=platform, entity=entity, repo=repo_key, metric=metric,
            data_json=payload
        )
        db.session.add(row)

    db.session.commit()
    return {"data": formatted_data, "cached": False}

    

# ===========================
# 1. 元数据相关接口（平台 / 实体 / 指标 / 仓库）
# ===========================

@api_bp.route("/platforms", methods=["GET"])
def get_platforms():
    """获取支持的平台列表"""
    return jsonify(meta.get_platforms())


@api_bp.route("/entities/<platform>", methods=["GET"])
def get_entities(platform: str):
    """获取某个平台下的组织/用户列表"""
    if not meta.is_supported_platform(platform):
        raise ApiException(400, f"不支持的平台：{platform}")
    entities = meta.get_entities(platform)
    return jsonify(entities)


@api_bp.route("/metrics/<entity_type>", methods=["GET"])
def get_metrics(entity_type: str):
    """根据类型（org/user）获取指标列表"""
    if entity_type not in ["org", "user"]:
        raise ApiException(400, f"无效的类型：{entity_type}，仅支持 org/user")
    metrics = meta.get_metrics(entity_type)
    return jsonify(metrics)


@api_bp.route("/repos/<platform>/<org>", methods=["GET"])
def get_repos(platform: str, org: str):
    """获取组织下的可查询仓库列表（仅 org 类型可用）"""
    if not meta.is_supported_platform(platform):
        raise ApiException(400, f"不支持的平台：{platform}")
    if not meta.is_valid_entity(platform, org):
        raise ApiException(400, f"平台 {platform} 无该组织：{org}")
    if meta.get_entity_type(platform, org) != "org":
        raise ApiException(400, f"{org} 不是组织类型，无仓库列表")

    repos = meta.get_repos(platform, org)
    if not repos:
        raise ApiException(404, "该组织暂无可查询的仓库")
    return jsonify(repos)


# ===========================
# 2. OpenDigger 指标数据接口
# ===========================

@api_bp.route("/data/<platform>/<entity>/<metric>", methods=["GET"])
def get_user_data(platform: str, entity: str, metric: str):
    if not meta.is_supported_platform(platform):
        raise ApiException(400, "不支持的平台")
    if not meta.is_valid_entity(platform, entity):
        raise ApiException(400, f"平台 {platform} 无该实体：{entity}")

    entity_type = meta.get_entity_type(platform, entity)
    if entity_type != "user":
        raise ApiException(400, f"该实体是 {entity_type}，请使用仓库数据接口")

    api_url = f"https://oss.open-digger.cn/{platform}/{entity}/{metric}.json"
    return jsonify(fetch_and_cache_data_db(api_url, platform, entity, None, metric))



@api_bp.route("/data/<platform>/<entity>/<repo>/<metric>", methods=["GET"])
def get_repo_data(platform: str, entity: str, repo: str, metric: str):
    if not meta.is_supported_platform(platform):
        raise ApiException(400, "不支持的平台")

    api_url = f"https://oss.open-digger.cn/{platform}/{entity}/{repo}/{metric}.json"
    return jsonify(fetch_and_cache_data_db(api_url, platform, entity, repo, metric))



# ===========================
# 3. LLM 汇总 & 排名接口
# ===========================

@api_bp.route("/llm/summary", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60) 
def get_llm_summary():
    # 可选：refresh=1 强制重新计算（跳过缓存）
    refresh = request.args.get("refresh", "0").lower() in ("1", "true", "yes")
    data = get_llm_summary_cached(force=refresh)
    return jsonify({"projects": data})



@api_bp.route("/llm/rank/<metric>", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60) 
def get_llm_rank(metric: str):
    allowed_metrics = {"health_score", "openrank_mean_12m", "activity_mean_12m"}
    if metric not in allowed_metrics:
        raise ApiException(400, f"不支持的排名指标: {metric}")

    top = request.args.get("top", default=10, type=int)
    refresh = request.args.get("refresh", "0").lower() in ("1", "true", "yes")

    data = get_llm_summary_cached(force=refresh)

    sorted_projects = sorted(
        data,
        key=lambda item: item.get(metric, 0.0),
        reverse=True
    )

    return jsonify({
        "metric": metric,
        "top": top,
        "projects": sorted_projects[:top]
    })



# ===========================
# 4. 智能报告接口（OpenAI + 规则兜底）
# ===========================

@api_bp.route("/llm/report", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def generate_llm_report():
    """
    根据前端传来的项目指标，生成一段“分析师风格”的文字报告。
    请求体结构：
      {
        "projects": [
          { "repo": "pytorch/pytorch", "metrics": { "activity": 0.8, ... } },
          ...
        ]
      }
    """
    payload = request.get_json(silent=True) or {}
    projects = payload.get("projects", [])

    if not projects:
        raise ApiException(400, "至少需要一个项目")

    # 1) 计算综合分
    enriched = []
    for p in projects:
        repo = p.get("repo", "unknown")
        metrics = p.get("metrics") or {}
        vals = list(metrics.values())
        score = sum(vals) / len(vals) if vals else 0.0
        enriched.append({"repo": repo, "metrics": metrics, "score": score})

    enriched.sort(key=lambda x: x["score"], reverse=True)

    # 2) 数字总结（给 LLM & 规则模板 都用）
    summary_lines = []
    for idx, p in enumerate(enriched, start=1):
        m = p["metrics"]
        summary_lines.append(
            f"{idx}. {p['repo']} —— 总体得分约 {p['score']:.2f}，"
            f"活跃度 {m.get('activity', 0):.2f}，"
            f"治理质量 {m.get('governance', 0):.2f}，"
            f"多样性 {m.get('diversity', 0):.2f}，"
            f"LLM 适配度 {m.get('llm_fit', 0):.2f}，"
            f"可持续性 {m.get('sustainability', 0):.2f}。"
        )
    numeric_summary = "\n".join(summary_lines)

    # 3) 如果配置了 OpenAI，则调用大模型写报告
    if openai_client is not None:
        try:
            prompt = (
                "下面是一组 LLM 相关开源项目在多个生态指标上的归一化得分（0~1）。"
                "请你用中文写一段 3~5 段落的分析师风格报告，"
                "总结谁更强、各自的优势短板，以及可能的社区演化趋势。"
                "注意面向非技术评委，语言清晰、结构有小标题。\n\n"
                f"{numeric_summary}"
            )

            # 定义更智能的 System Prompt
            system_prompt = """
你是一名负责开源生态评估的资深分析师。请根据用户提供的数据写一份深度对比报告。

【内容与格式要求】：
1. **结构必须清晰**：报告必须包含 3-4 个明确的 Markdown 小标题（使用 ### 语法），例如：
   ### 📊 总体评分概览
   ### 🚀 各项目核心优势
   ### ⚠️ 潜在风险与短板
   ### 🔮 社区演化趋势

2. **重点灵活高亮**：
   - 请识别报告中的 **关键结论、核心数据对比、或犀利的洞察**。
   - 将这些句子用 Markdown 加粗符号（**...**）包裹。
   - ⚠️ 不需要局限于段落开头，哪里重要就标哪里，但不要全文通篇加粗。

3. **结尾强制总结**：
   - 报告的最后，必须包含一个 Markdown 引用块（使用 > 符号）。
   - 内容必须以 “💡 **分析师建议：**” 开头，针对不同场景给出 1-2 句具体的选型建议。
   - 格式示例：
     > 💡 **分析师建议：** 如果追求稳定性，推荐选择 PyTorch；如果需要快速验证 Agent，LangChain 是更好的选择。

4. **语气风格**：专业、客观、见解独到。
"""

            # 下面这部分保持不变
            resp = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
            )
            content = resp.choices[0].message.content
            return jsonify({"report": content, "from_llm": True})
        except Exception as e:
            print("调用 LLM 失败，将使用规则模板：", e)
    

    # 4) 兜底模板
    text_lines = [
        "【LLM 项目生态概览】",
        "基于最近 12 个月的开源活动数据，我们对当前选择的 LLM 相关项目进行了五维度的生态健康度评估。",
        "",
        "一、综合得分排序",
        numeric_summary,
        "",
        "二、整体观察",
        "从得分情况可以看出，排名靠前的项目在活跃度和治理质量上普遍表现较好，说明社区有稳定的贡献者群体以及较完善的协作流程。",
        "得分相对偏低的项目，通常集中出现在多样性或可持续性维度，可能意味着贡献者结构较集中，或者核心维护者过于少数化。",
        "",
        "三、简单建议",
        "对于综合得分较高的项目，可以进一步关注如何提升新贡献者的进入体验，巩固多样性优势；",
        "对于得分偏低的项目，则建议在文档完善、Issue 反馈响应以及社区运营等方面投入更多精力，以提升长期的可持续发展能力。"
    ]
    return jsonify({"report": "\n".join(text_lines), "from_llm": False})

# ===========================
# LLM 项目树接口（新增）
# ===========================

@api_bp.route("/llm/projects", methods=["GET"])
def get_llm_projects():
    """
    返回 LLM 生态的项目树结构（用于前端选择框）
    从 config.json 的 category_tree 字段读取，并过滤掉不在 repositories 中的项目
    """
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        category_tree = config.get("category_tree", [])
        if not category_tree:
            raise ApiException(404, "配置文件中未定义 category_tree")
        
        # 获取有效项目列表（org/repo 格式）
        valid_repos = {
            f"{r['org']}/{r['repo']}" 
            for r in config.get("repositories", [])
        }
        
        # 过滤树结构，移除无效项目
        def filter_tree(nodes):
            result = []
            for node in nodes:
                if "children" in node and node["children"]:
                    # 非叶子节点：递归过滤子节点
                    filtered_children = filter_tree(node["children"])
                    if filtered_children:  # 只保留有子节点的分类
                        result.append({
                            **node,
                            "children": filtered_children
                        })
                else:
                    # 叶子节点：检查是否在有效列表中
                    if node.get("value") in valid_repos:
                        result.append(node)
            return result
        
        filtered_tree = filter_tree(category_tree)
        
        return jsonify({
            "tree": filtered_tree,
            "total_projects": len(valid_repos)
        })
    except FileNotFoundError:
        raise ApiException(500, "配置文件不存在")
    except json.JSONDecodeError:
        raise ApiException(500, "配置文件格式错误")

# ===========================
# 5. 贡献者健康预警系统（创新功能）
# ===========================

@api_bp.route("/health/contributor-risk/<platform>/<org>/<repo>", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60)
def get_contributor_risk(platform: str, org: str, repo: str):
    """
    贡献者集中度风险分析 API
    
    基于 bus_factor（巴士因子）指标判断项目是否过度依赖少数开发者
    巴士因子 = 最少需要多少核心开发者"被巴士撞了"项目才会停滞
    
    Returns:
        {
            "project": "pytorch/pytorch",
            "bus_factor_avg_6m": 8.5,
            "bus_factor_trend": "stable",
            "risk_level": "low",
            "risk_score": 0.15,
            "message": "✅ 健康：项目有足够的贡献者冗余",
            "suggestion": null,
            "details": {...}
        }
    """
    api_url = f"https://oss.open-digger.cn/{platform}/{org}/{repo}/bus_factor.json"
    
    try:
        result = fetch_and_cache_data_db(api_url, platform, org, repo, "bus_factor")
        records = result["data"]
        
        if not records:
            raise ApiException(404, "该项目暂无 bus_factor 数据")
        
        # 取最近 6 个月和 12 个月的数据做对比
        recent_6m = _tail12_values(records)[-6:] if len(_tail12_values(records)) >= 6 else _tail12_values(records)
        recent_12m = _tail12_values(records)
        
        avg_6m = _mean(recent_6m) if recent_6m else 0
        avg_12m = _mean(recent_12m) if recent_12m else 0
        
        # 计算趋势
        if len(recent_6m) >= 2:
            first_half = _mean(recent_6m[:len(recent_6m)//2])
            second_half = _mean(recent_6m[len(recent_6m)//2:])
            if second_half > first_half * 1.1:
                trend = "improving"
                trend_text = "📈 上升趋势"
            elif second_half < first_half * 0.9:
                trend = "declining"
                trend_text = "📉 下降趋势"
            else:
                trend = "stable"
                trend_text = "➡️ 保持稳定"
        else:
            trend = "unknown"
            trend_text = "❓ 数据不足"
        
        # 风险等级判定
        if avg_6m <= 1.5:
            risk_level = "critical"
            risk_score = 0.95
            message = "🔴 极高风险：项目几乎完全依赖单一开发者！"
            suggestion = "建议立即关注：该项目随时可能因核心开发者离开而停滞。如用于生产环境，请准备替代方案。"
        elif avg_6m <= 3:
            risk_level = "high"
            risk_score = 0.75
            message = "🟠 高风险：项目严重依赖 1-3 位核心开发者"
            suggestion = "建议谨慎：该项目核心贡献者过于集中。关注社区是否有新贡献者培养计划。"
        elif avg_6m <= 5:
            risk_level = "medium"
            risk_score = 0.45
            message = "🟡 中风险：核心开发者数量偏少"
            suggestion = "建议关注：可查看项目的 CONTRIBUTING.md 和社区活跃度，评估长期可持续性。"
        elif avg_6m <= 8:
            risk_level = "low"
            risk_score = 0.2
            message = "🟢 低风险：项目有较好的贡献者分布"
            suggestion = None
        else:
            risk_level = "healthy"
            risk_score = 0.05
            message = "✅ 非常健康：项目有充足的贡献者冗余"
            suggestion = None
        
        # 如果趋势下降，提高风险分数
        if trend == "declining" and risk_level not in ["critical", "high"]:
            risk_score = min(risk_score + 0.15, 0.9)
            message += "（⚠️ 注意：贡献者集中度正在恶化）"
        
        return jsonify({
            "project": f"{org}/{repo}",
            "platform": platform,
            "bus_factor_avg_6m": round(avg_6m, 2),
            "bus_factor_avg_12m": round(avg_12m, 2),
            "bus_factor_trend": trend,
            "bus_factor_trend_text": trend_text,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "message": message,
            "suggestion": suggestion,
            "details": {
                "recent_values": [round(v, 2) for v in recent_6m],
                "min_6m": round(min(recent_6m), 2) if recent_6m else 0,
                "max_6m": round(max(recent_6m), 2) if recent_6m else 0,
            },
            "cached": result.get("cached", False)
        })
        
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(500, f"分析贡献者风险失败: {str(e)}")


@api_bp.route("/health/batch-risk", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def get_batch_contributor_risk():
    """
    批量获取多个项目的贡献者风险（用于对比页面）
    
    请求体：
    {
        "projects": ["pytorch/pytorch", "huggingface/transformers"]
    }
    """
    data = request.get_json(silent=True) or {}
    projects = data.get("projects", [])
    
    if not projects:
        raise ApiException(400, "请提供至少一个项目")
    
    if len(projects) > 10:
        raise ApiException(400, "单次最多查询 10 个项目")
    
    results = []
    
    for proj in projects:
        parts = proj.strip().split("/")
        if len(parts) != 2:
            results.append({
                "project": proj,
                "error": "格式错误，应为 org/repo"
            })
            continue
        
        org, repo = parts
        api_url = f"https://oss.open-digger.cn/github/{org}/{repo}/bus_factor.json"
        
        try:
            result = fetch_and_cache_data_db(api_url, "github", org, repo, "bus_factor")
            records = result["data"]
            recent_6m = _tail12_values(records)[-6:] if records else []
            avg_6m = _mean(recent_6m) if recent_6m else 0
            
            # 简化的风险判定
            if avg_6m <= 2:
                risk_level, risk_score = "high", 0.8
            elif avg_6m <= 5:
                risk_level, risk_score = "medium", 0.5
            else:
                risk_level, risk_score = "low", 0.2
            
            results.append({
                "project": proj,
                "bus_factor_avg_6m": round(avg_6m, 2),
                "risk_level": risk_level,
                "risk_score": round(risk_score, 2)
            })
        except Exception as e:
            results.append({
                "project": proj,
                "error": str(e)
            })
    
    return jsonify({"results": results})