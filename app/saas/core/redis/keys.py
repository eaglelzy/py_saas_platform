"""统一 Redis Key 规范，避免跨服务命名分散。"""

from __future__ import annotations


class RedisKeys:
    """封装平台内常用的 Redis Key 生成逻辑。"""

    # 命名空间前缀
    _AUTH_NS = "auth"
    _VERIFY_NS = "verify"
    _RATE_LIMIT_NS = "ratelimit"
    _CACHE_NS = "cache"

    @staticmethod
    def jwt_blacklist(jti: str) -> str:
        """生成访问令牌黑名单的 Key。"""

        return f"{RedisKeys._AUTH_NS}:blacklist:{jti}"

    @staticmethod
    def refresh_session(user_id: str) -> str:
        """记录用户最新 Refresh Token 的 Key。"""

        return f"{RedisKeys._AUTH_NS}:refresh_session:{user_id}"

    @staticmethod
    def verification_code(scene: str, target: str) -> str:
        """验证码正文存储的 Key（支持邮箱、短信等场景）。"""

        normalized_scene = scene.lower().replace(" ", "_")
        return f"{RedisKeys._VERIFY_NS}:{normalized_scene}:{target}"

    @staticmethod
    def verification_attempts(scene: str, target: str) -> str:
        """验证码错误次数计数的 Key。"""

        normalized_scene = scene.lower().replace(" ", "_")
        return f"{RedisKeys._VERIFY_NS}:{normalized_scene}:{target}:attempts"

    @staticmethod
    def rate_limit(scope: str, identifier: str, window: str) -> str:
        """限流计数的 Key，window 需指定如 '1m'、'1h'。"""

        normalized_scope = scope.lower().replace(" ", "_")
        return f"{RedisKeys._RATE_LIMIT_NS}:{normalized_scope}:{identifier}:{window}"

    @staticmethod
    def cache(namespace: str, key: str) -> str:
        """通用缓存数据的 Key，需显式传入业务命名空间。"""

        normalized_namespace = namespace.lower().replace(" ", "_")
        return f"{RedisKeys._CACHE_NS}:{normalized_namespace}:{key}"


__all__ = ("RedisKeys",)
