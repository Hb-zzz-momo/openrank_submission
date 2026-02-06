#!/usr/bin/env python3
"""
检测 config.json 中哪些项目在 OpenDigger 没有数据
用于数据治理：找出无效项目并可选择清理

使用方法：
    python check_repos.py          # 检测并询问是否清理
    python check_repos.py --check  # 仅检测，不清理
"""

import json
import requests
import shutil
from pathlib import Path

# 配置
CONFIG_FILE = Path(__file__).parent / "config.json"
BASE_URL = "https://oss.open-digger.cn/{platform}/{org}/{repo}/{metric}.json"
REQUIRED_METRICS = ["openrank", "activity"]  # 必须有的核心指标


def check_repo_availability(platform, org, repo):
    """检查一个项目是否有可用数据"""
    missing_metrics = []
    
    for metric in REQUIRED_METRICS:
        url = BASE_URL.format(platform=platform, org=org, repo=repo, metric=metric)
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 404:
                missing_metrics.append(metric)
        except Exception as e:
            missing_metrics.append(f"{metric}(error)")
    
    return missing_metrics


def cleanup_database(invalid_repos):
    """清理数据库中的无效项目数据"""
    from flask import Flask
    from extensions import db
    from models import MetricSeries
    
    app = Flask("cleanup")
    db_path = Path(__file__).parent / "openrank.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        deleted_count = 0
        for repo_info in invalid_repos:
            platform = repo_info["platform"]
            org = repo_info["org"]
            repo = repo_info["repo"]
            
            # 删除该项目的所有指标数据
            rows = MetricSeries.query.filter_by(
                platform=platform, 
                entity=org, 
                repo=repo
            ).all()
            
            for row in rows:
                db.session.delete(row)
                deleted_count += 1
        
        db.session.commit()
        print(f"🗑️  已从数据库删除 {deleted_count} 条记录")


def cleanup_invalid_repos(invalid_repos, valid_repos):
    """
    从 config.json 中移除无效项目
    同时清理数据库中的残留数据
    """
    if not invalid_repos:
        print("✨ 没有需要清理的项目")
        return
    
    # 1. 更新 config.json
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 用有效项目列表替换
    config["repositories"] = valid_repos
    
    # 备份原文件
    backup_file = CONFIG_FILE.with_suffix(".json.bak")
    shutil.copy(CONFIG_FILE, backup_file)
    print(f"📦 已备份原配置到: {backup_file}")
    
    # 写入新配置
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ config.json 已更新，移除了 {len(invalid_repos)} 个无效项目")
    
    # 2. 清理数据库（可选）
    try:
        cleanup_database(invalid_repos)
    except Exception as e:
        print(f"⚠️  数据库清理跳过（可能缺少依赖）: {e}")


def main(check_only=False, auto_clean=False):
    """
    主函数
    Args:
        check_only: 是否仅检测不清理
    """
    # 读取配置
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    repos = config.get("repositories", [])
    
    print("=" * 60)
    print("🔍 开始检测项目数据可用性...")
    print(f"   共 {len(repos)} 个项目待检测")
    print("=" * 60)
    
    invalid_repos = []
    valid_repos = []
    
    for i, repo_info in enumerate(repos, 1):
        platform = repo_info["platform"]
        org = repo_info["org"]
        repo = repo_info["repo"]
        full_name = f"{org}/{repo}"
        
        print(f"[{i}/{len(repos)}] 检测 {full_name}...", end=" ")
        
        missing = check_repo_availability(platform, org, repo)
        
        if missing:
            print(f"❌ 缺失: {missing}")
            invalid_repos.append(repo_info)
        else:
            print("✅")
            valid_repos.append(repo_info)
    
    # 汇总报告
    print("\n" + "=" * 60)
    print("📊 检测结果汇总")
    print("=" * 60)
    print(f"   有效项目: {len(valid_repos)} 个")
    print(f"   无效项目: {len(invalid_repos)} 个")
    
    if invalid_repos:
        print("\n⚠️  以下项目在 OpenDigger 无数据，建议删除：")
        print("-" * 40)
        for r in invalid_repos:
            print(f"   • {r['org']}/{r['repo']} ({r.get('category', 'unknown')})")
        
        if not check_only:
            if auto_clean:
                # 自动清理模式
                print("\n🤖 自动清理模式，开始清理...")
                cleanup_invalid_repos(invalid_repos, valid_repos)
                print("\n🎉 清理完成！")
            else:
                # 交互确认
                print("\n" + "-" * 60)
                confirm = input("是否立即清理这些无效项目？(y/n): ").strip().lower()
                if confirm == 'y':
                    cleanup_invalid_repos(invalid_repos, valid_repos)
                    print("\n🎉 清理完成！请重新运行 data_fetcher.py 更新数据")
                else:
                    print("已取消清理操作")
    else:
        print("\n🎉 所有项目数据都可用，无需清理！")
    
    return invalid_repos, valid_repos


if __name__ == "__main__":
    import sys
    
    check_only = "--check" in sys.argv
    auto_clean = "--auto" in sys.argv
    
    if check_only:
        print("📋 仅检测模式（不会修改任何文件）\n")
    elif auto_clean:
        print("🤖 自动清理模式（无需确认）\n")
    
    main(check_only=check_only, auto_clean=auto_clean)