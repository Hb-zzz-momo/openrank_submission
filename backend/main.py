# backend/main.py
import os
import secrets
from pathlib import Path
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import threading

# 1) 先加载 .env（必须在导入 opendigger 蓝图之前）
BASE_DIR = Path(__file__).resolve().parent  # backend/
load_dotenv(BASE_DIR / ".env")

from extensions import db, jwt
from api.opendigger import api_bp
from api.auth import auth_bp
from api.favorites import favorites_bp


def create_app():
    app = Flask(__name__)

    # ✅ 安全修复：从环境变量读取密钥，开发环境自动生成随机密钥
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", 
        secrets.token_hex(32)  # 开发时自动生成64字符随机密钥
    )
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY", 
        secrets.token_hex(32)
    )
    
    # ✅ 生产环境强制检查（防止忘记配置）
    if os.getenv("FLASK_ENV") == "production":
        if not os.getenv("SECRET_KEY") or not os.getenv("JWT_SECRET_KEY"):
            raise RuntimeError(
                "❌ 生产环境必须设置 SECRET_KEY 和 JWT_SECRET_KEY 环境变量！\n"
                "请在 .env 文件或系统环境变量中配置。"
            )
    
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

    db_path = os.path.join(BASE_DIR, "openrank.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    jwt.init_app(app)

    CORS(
  app,
  resources={r"/api/*": {"origins": r"^http://(localhost|127\.0\.0\.1):\d+$"}},
  supports_credentials=True
)


    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(favorites_bp)
    return app


def start_background_sync(app):
    def job():
        with app.app_context():
            try:
                from data_fetcher import run_sync
                run_sync(force=False, ttl_hours=24)  # 24小时内不重复拉
            except Exception:
                app.logger.exception("OpenDigger 数据同步失败（后台任务）")
    threading.Thread(target=job, daemon=True).start()


app = create_app()

if __name__ == "__main__":
    DEBUG = True
    with app.app_context():
        db.create_all()
        
    if (not DEBUG) or (os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
        start_background_sync(app)

    app.run(host="0.0.0.0", port=8000, debug=True)