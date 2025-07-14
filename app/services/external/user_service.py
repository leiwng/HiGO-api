import hashlib
import secrets
from datetime import datetime, timezone
from app.models.user import User
from app.services.storage.mongo_service import MongoService
from app.utils.password_validator import PasswordValidator

class UserService:
    def __init__(self, mongo_service: MongoService):
        self.mongo = mongo_service
        self.users_collection = "users"

    def hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        """使用salt哈希密码"""
        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return password_hash.hex(), salt

    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """验证密码"""
        password_hash, _ = self.hash_password(password, salt)
        return password_hash == hashed_password

    async def get_user_by_username(self, username: str) -> dict | None:
        """根据用户名获取用户信息"""
        user_doc = await self.mongo.find_one(
            self.users_collection,
            {"username": username}
        )
        return user_doc

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """验证用户凭据"""
        user_doc = await self.get_user_by_username(username)
        if not user_doc:
            return None

        # 验证密码
        if not self.verify_password(
            password,
            user_doc["password_hash"],
            user_doc["salt"]
        ):
            return None

        return User(
            id=str(user_doc["_id"]),
            username=user_doc["username"],
            email=user_doc.get("email"),
            is_active=user_doc.get("is_active", True),
            created_at=user_doc.get("created_at"),
            updated_at=user_doc.get("updated_at")
        )

    async def create_user(self, username: str, password: str, email: str | None = None) -> User:
        """创建新用户"""
        # 使用密码验证器验证密码
        is_valid, errors = PasswordValidator.validate(password)
        if not is_valid:
            error_message = "; ".join(errors)
            raise ValueError(error_message)

        # 检查用户是否已存在
        existing_user = await self.get_user_by_username(username)
        if existing_user:
            raise ValueError("用户名已存在")

        # 哈希密码
        password_hash, salt = self.hash_password(password)

        # 创建用户文档
        current_time = datetime.now(timezone.utc)
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "salt": salt,
            "is_active": True,
            "created_at": current_time,
            "updated_at": current_time
        }

        # 保存到数据库
        user_id = await self.mongo.insert_one(self.users_collection, user_doc)

        return User(
            id=user_id,
            username=username,
            email=email,
            is_active=True,
            created_at=current_time,
            updated_at=current_time
        )