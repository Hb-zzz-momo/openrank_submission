from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from extensions import db
from models import Favorite
from api.opendigger import ApiException

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")

@favorites_bp.errorhandler(ApiException)
def handle_exc(e: ApiException):
    return jsonify({"detail": e.detail}), e.status_code

def build_compare_key(repos: list[str]) -> str:
    # 只用 repos 去重
    rs = sorted([r.strip() for r in repos if r and r.strip()])
    return "compare:" + ",".join(rs)

def build_single_key(full_name: str, metric: str, platform: str) -> str:
    return f"single:{platform}:{full_name}:{metric}"
# 查找收藏
@favorites_bp.route("", methods=["GET"])
@jwt_required()
def list_favorites():
    uid = int(get_jwt_identity())
    items = Favorite.query.filter_by(user_id=uid).order_by(Favorite.id.desc()).all()
    return jsonify({"favorites": [x.to_dict() for x in items]}), 200

# 新增收藏
@favorites_bp.route("", methods=["POST"])
@jwt_required()
def add_favorite():
    uid = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    kind = (data.get("kind") or "single").strip()

    # ---------- A) 收藏“方案/榜单/对比结果” ----------
    if kind == "plan":
        payload = data.get("payload") or {}
        uniq_key = (data.get("uniq_key") or "").strip()
        if not uniq_key:
            raise ApiException(400, "plan 收藏必须提供 uniq_key")

        fav = Favorite(
            user_id=uid,
            kind="plan",
            uniq_key=uniq_key,
            title=(data.get("title") or "收藏方案").strip(),
            payload=json.dumps(payload, ensure_ascii=False),
        )
        try:
            db.session.add(fav)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise ApiException(400, "已收藏过该方案/榜单")
        return jsonify({"favorite": fav.to_dict()}), 201

    # ---------- B) 收藏“单仓库 + 单指标” ----------
    full_name = (data.get("full_name") or "").strip()
    metric = (data.get("metric") or "").strip()
    platform = (data.get("platform") or "github").strip()

    if not full_name or not metric:
        raise ApiException(400, "single 收藏需要 full_name 和 metric")

    uniq_key = (data.get("uniq_key") or "").strip()
    if not uniq_key:
        uniq_key = f"single:{platform}:{full_name}:{metric}"

    fav = Favorite(
        user_id=uid,
        kind="single",
        uniq_key=uniq_key,
        full_name=full_name,
        metric=metric,
        platform=platform,
        title=(data.get("title") or "").strip(),
        url=(data.get("url") or "").strip(),
    )
    try:
        db.session.add(fav)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise ApiException(400, "已收藏过该项目指标")

    return jsonify({"favorite": fav.to_dict()}), 201

# 删除收藏
@favorites_bp.route("/<int:fav_id>", methods=["DELETE"])
@jwt_required()
def remove_favorite(fav_id: int):
    uid = int(get_jwt_identity())
    fav = Favorite.query.filter_by(id=fav_id, user_id=uid).first()
    if not fav:
        raise ApiException(404, "收藏不存在")

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "删除成功"}), 200