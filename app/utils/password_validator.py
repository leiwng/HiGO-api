import re
from app.core.config import settings

class PasswordValidator:
    @staticmethod
    def validate(password: str) -> tuple[bool, list[str]]:
        """
        验证密码是否符合要求
        返回: (是否有效, 错误信息列表)
        """
        errors = []

        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"密码长度至少需要{settings.PASSWORD_MIN_LENGTH}位")

        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含至少一个大写字母")

        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("密码必须包含至少一个小写字母")

        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("密码必须包含至少一个数字")

        if settings.PASSWORD_REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含至少一个特殊字符")

        return len(errors) == 0, errors

    @staticmethod
    def get_requirements() -> dict[str, bool | int | str]:
        """获取密码要求"""
        return {
            "min_length": settings.PASSWORD_MIN_LENGTH,
            "require_uppercase": settings.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": settings.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": settings.PASSWORD_REQUIRE_NUMBERS,
            "require_special_chars": settings.PASSWORD_REQUIRE_SPECIAL_CHARS,
            "special_chars": "!@#$%^&*(),.?\":{}|<>"
        }