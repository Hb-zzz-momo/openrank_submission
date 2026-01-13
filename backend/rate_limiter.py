# backend/rate_limiter.py
"""
API 限流器
基于滑动窗口算法，防止接口被恶意刷取
"""
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class RateLimiter:
    """
    线程安全的内存限流器
    
    生产环境建议替换为 Redis 实现，支持分布式部署
    """
    
    def __init__(self):
        self._request_records = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        检查请求是否允许
        
        Args:
            key: 限流键（通常是 IP 或 用户ID）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        
        Returns:
            (是否允许, 剩余可用次数)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        with self._lock:
            # 清理过期记录
            self._request_records[key] = [
                t for t in self._request_records[key] if t > window_start
            ]
            
            current_count = len(self._request_records[key])
            remaining = max_requests - current_count
            
            if current_count >= max_requests:
                return False, 0
            
            # 记录本次请求
            self._request_records[key].append(now)
            return True, remaining - 1
    
    def reset(self, key: str):
        """重置某个键的限流记录"""
        with self._lock:
            self._request_records.pop(key, None)


# 全局限流器实例
_limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60, key_func=None):
    """
    限流装饰器
    
    Args:
        max_requests: 时间窗口内最大请求数，默认 10 次
        window_seconds: 时间窗口大小（秒），默认 60 秒
        key_func: 自定义限流键函数，默认使用客户端 IP
    
    Usage:
        @app.route("/api/expensive")
        @rate_limit(max_requests=5, window_seconds=60)
        def expensive_api():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 确定限流键
            if key_func:
                limit_key = key_func()
            else:
                # 默认使用 IP + 端点路径
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                if client_ip and ',' in client_ip:
                    client_ip = client_ip.split(',')[0].strip()
                limit_key = f"{client_ip}:{request.endpoint}"
            
            allowed, remaining = _limiter.is_allowed(limit_key, max_requests, window_seconds)
            
            if not allowed:
                response = jsonify({
                    "detail": f"请求过于频繁，请 {window_seconds} 秒后重试",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(window_seconds)
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = '0'
                return response
            
            # 执行原函数
            response = f(*args, **kwargs)
            
            # 如果是 Response 对象，添加限流头信息
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
            
            return response
        return wrapper
    return decorator


def rate_limit_by_user(max_requests: int = 10, window_seconds: int = 60):
    """
    基于用户 ID 的限流装饰器（需要 JWT 认证）
    
    Usage:
        @app.route("/api/user-action")
        @jwt_required()
        @rate_limit_by_user(max_requests=5, window_seconds=60)
        def user_action():
            ...
    """
    def key_func():
        from flask_jwt_extended import get_jwt_identity
        try:
            user_id = get_jwt_identity()
            return f"user:{user_id}:{request.endpoint}"
        except Exception:
            # 降级到 IP 限流
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            return f"ip:{client_ip}:{request.endpoint}"
    
    return rate_limit(max_requests=max_requests, window_seconds=window_seconds, key_func=key_func)