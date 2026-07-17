"""日志服务 - 记录用户操作"""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.action_log import ActionLog


class LogService:
    """日志服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        user_id: int,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None
    ) -> ActionLog:
        """
        记录用户操作日志

        Args:
            user_id: 用户ID
            action: 操作类型（如 user.login, user.upload_avatar）
            resource_type: 资源类型（如 user, course, file）
            resource_id: 资源ID
            ip_address: IP地址
            user_agent: User-Agent
            details: 详细信息（字典格式）

        Returns:
            ActionLog: 创建的日志记录
        """
        log_entry = ActionLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)

        return log_entry

    # 便捷方法

    async def log_login(self, user_id: int, ip_address: str | None = None, user_agent: str | None = None) -> ActionLog:
        """记录登录"""
        return await self.log(
            user_id=user_id,
            action="user.login",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def log_logout(self, user_id: int, ip_address: str | None = None, user_agent: str | None = None) -> ActionLog:
        """记录登出"""
        return await self.log(
            user_id=user_id,
            action="user.logout",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def log_register(self, user_id: int, email: str, username: str, ip_address: str | None = None, user_agent: str | None = None) -> ActionLog:
        """记录注册"""
        return await self.log(
            user_id=user_id,
            action="user.register",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email, "username": username}
        )

    async def log_profile_update(
        self,
        user_id: int,
        fields_updated: list[str],
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> ActionLog:
        """记录资料更新"""
        return await self.log(
            user_id=user_id,
            action="user.update_profile",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            details={"fields": fields_updated}
        )

    async def log_avatar_upload(
        self,
        user_id: int,
        filename: str,
        file_size: int,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> ActionLog:
        """记录头像上传"""
        return await self.log(
            user_id=user_id,
            action="user.upload_avatar",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent,
            details={"filename": filename, "size": file_size}
        )

    async def log_password_change(self, user_id: int, ip_address: str | None = None, user_agent: str | None = None) -> ActionLog:
        """记录修改密码"""
        return await self.log(
            user_id=user_id,
            action="user.change_password",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=ip_address,
            user_agent=user_agent
        )
