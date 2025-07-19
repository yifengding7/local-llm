# api/auth/jwt_handler.py
"""
JWT认证处理器 - 安全的身份验证和授权
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
import secrets
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list = []

class JWTHandler:
    """JWT处理器"""
    
    def __init__(self):
        # 从环境变量获取配置
        self.secret_key = os.getenv("JWT_SECRET", self._generate_secret_key())
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "30"))
        
        # API密钥管理
        self.api_keys = self._load_api_keys()
    
    def _generate_secret_key(self) -> str:
        """生成安全的密钥"""
        key = secrets.token_urlsafe(32)
        logger.warning(f"Generated new JWT secret key. Please set JWT_SECRET environment variable.")
        return key
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """加载API密钥配置"""
        # 在生产环境中，这应该从数据库或安全存储加载
        return {
            os.getenv("API_KEY", "test-key"): {
                "name": "default",
                "scopes": ["read", "write"],
                "rate_limit": 1000
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        return self.api_keys.get(api_key)
    
    def has_scope(self, token_data: Dict[str, Any], required_scope: str) -> bool:
        """检查权限范围"""
        scopes = token_data.get("scopes", [])
        return required_scope in scopes
    
    def create_api_key(self, name: str, scopes: list = None, rate_limit: int = 1000) -> str:
        """创建新的API密钥"""
        api_key = f"ai-monitor-{secrets.token_urlsafe(32)}"
        
        self.api_keys[api_key] = {
            "name": name,
            "scopes": scopes or ["read", "write"],
            "rate_limit": rate_limit,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 在生产环境中应该持久化到数据库
        logger.info(f"Created new API key for {name}")
        
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """撤销API密钥"""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            logger.info(f"Revoked API key: {api_key[:10]}...")
            return True
        return False

# api/auth/middleware.py
"""
认证中间件
"""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""
    
    def __init__(self, app, jwt_handler: JWTHandler = None):
        super().__init__(app)
        self.jwt_handler = jwt_handler or JWTHandler()
        # 不需要认证的路径
        self.public_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否是公开路径
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # 获取认证信息
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication header"}
            )
        
        try:
            # 支持Bearer Token和API Key
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                
                # 先尝试作为JWT token验证
                try:
                    user_data = self.jwt_handler.verify_token(token)
                    request.state.user = user_data
                except ValueError:
                    # 如果不是JWT，尝试作为API密钥
                    api_key_data = self.jwt_handler.verify_api_key(token)
                    if not api_key_data:
                        raise ValueError("Invalid authentication token")
                    request.state.user = api_key_data
            else:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"}
                )
            
            # 继续处理请求
            response = await call_next(request)
            return response
            
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)}
            )
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error"}
            )