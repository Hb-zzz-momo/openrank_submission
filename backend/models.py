# backend/models.py
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # single / plan
    kind = db.Column(db.String(16), nullable=False, default="single", index=True)

    # 去重键：同一用户同一 uniq_key 只能收藏一次
    uniq_key = db.Column(db.String(300), nullable=False, index=True)

    # single 才需要；plan 允许为空
    full_name = db.Column(db.String(200), nullable=True)   # org/repo
    metric = db.Column(db.String(64), nullable=True)

    platform = db.Column(db.String(32), nullable=True, default="github")
    title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(400), nullable=True)

    # plan/rank/compare 等的 JSON 字符串
    payload = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "uniq_key", name="uq_user_uniq_key"),
    )

    def to_dict(self):
        payload_obj = {}
        if self.payload:
            try:
                payload_obj = json.loads(self.payload)
            except Exception:
                payload_obj = {}

        return {
            "id": self.id,
            "user_id": self.user_id,
            "kind": self.kind,
            "uniq_key": self.uniq_key,
            "full_name": self.full_name,
            "metric": self.metric,
            "platform": self.platform,
            "title": self.title,
            "url": self.url,
            "payload": payload_obj,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
class MetricSeries(db.Model):
    __tablename__ = "metric_series"

    id = db.Column(db.Integer, primary_key=True)

    platform = db.Column(db.String(32), nullable=False, index=True)   # github/gitee
    entity = db.Column(db.String(128), nullable=False, index=True)    # org 或 user
    repo = db.Column(db.String(128), nullable=True, index=True)       # user 数据时可为空
    metric = db.Column(db.String(64), nullable=False, index=True)

    # 存整段序列：[{month:'YYYY-MM', count:xxx}, ...]
    data_json = db.Column(db.Text, nullable=False, default="[]")

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    __table_args__ = (
        db.UniqueConstraint("platform", "entity", "repo", "metric", name="uq_metric_series"),
    )

    def to_records(self):
        try:
            return json.loads(self.data_json) or []
        except Exception:
            return []
