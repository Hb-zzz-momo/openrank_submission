# backend/api/auth.py
"""
auth 蓝图：专门处理身份认证相关接口：
  - POST /api/auth/register  注册
  - POST /api/auth/login     登录
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from datetime import datetime, timedelta
import jwt

from extensions import db
from models import User
from api.opendigger import ApiException  # 复用之前定义的异常类
from rate_limiter import rate_limit

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


#--------------接口函数-----------------
@auth_bp.errorhandler(ApiException)
def handle_auth_exception(e: ApiException):
    """在 auth 这个蓝图里也统一把 ApiException 转成 JSON"""
    return jsonify({"detail": e.detail}), e.status_code

@auth_bp.route("/register", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=3600)
def register():
    """
    注册接口：
    请求体 JSON 示例：
    {
      "username": "zbh",
      "email": "xxx@example.com",
      "password": "123456"
    }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    #加一些限制
    # 1. 基础校验
    if not username or not email or not password:
        raise ApiException(400, "用户名、邮箱和密码不能为空")
    
    # 2. 密码强度验证
    if len(password) < 8:
        raise ApiException(400, "密码长度至少为8个字符")
    
    # 3. 邮箱格式验证
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ApiException(400, "邮箱格式不正确")
    
    # 4. 用户名格式验证（仅允许字母、数字、下划线，3-32字符）
    username_pattern = r'^[a-zA-Z0-9_]{3,32}$'
    if not re.match(username_pattern, username):
        raise ApiException(400, "用户名格式不正确（3-32个字符，仅允许字母、数字、下划线）")
    
    # 5. 唯一性检查
    if User.query.filter_by(username=username).first():
        raise ApiException(400, "该用户名已被注册")
    if User.query.filter_by(email=email).first():
        raise ApiException(400, "该邮箱已被注册")
    
    
    
    # 6. 入库
    user = User(
        username=username,
        email=email,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "message": "注册成功",
        "user": user.to_dict()
    }), 201
    
@auth_bp.route("/login", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=300)
def login():
    data = request.get_json(silent=True) or {}

    account = (data.get("username") or "").strip()  # 这里 account 既可以是用户名也可以是邮箱
    password = (data.get("password") or "").strip()

    if not account or not password:
        raise ApiException(400, "用户名/邮箱 和 密码不能为空")

    # 判断是邮箱还是用户名
    if "@" in account:
        user = User.query.filter_by(email=account).first()
    else:
        user = User.query.filter_by(username=account).first()

    if not user:
        return jsonify({"detail": "用户不存在"}), 404

    if not user.check_password(password):
        raise ApiException(400, "密码错误")

    # ✅ identity 只放 user.id（字符串），其他信息放到附加 claims
    additional_claims = {
        "username": user.username,
        "email": user.email
    }
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        "message": "登录成功",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


    
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    获取当前登录用户信息：从 token 中拿出 id，再查数据库
    """
    user_id = get_jwt_identity()        # 这里取出来是字符串
    user = User.query.get(int(user_id))
    if not user:
        raise ApiException(404, "用户不存在或已被删除")

    return jsonify({"user": user.to_dict()}), 200