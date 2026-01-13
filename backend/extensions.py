from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# 全局的数据库对象，所有模型都通过它来声明
db = SQLAlchemy()

# 全局唯一的 JWT 管理器
jwt = JWTManager()