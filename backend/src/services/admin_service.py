"""管理员后台业务逻辑"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.audit import AuditLog
from ..models.group import Group
from ..models.user import User, UserTier
from ..schemas.admin import AdminUserUpdate, GroupCreate, GroupUpdate


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 用户管理 ----------
    async def list_users(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        tier: UserTier | None = None,
        keyword: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User).options(selectinload(User.group))
        count_stmt = select(func.count(User.id))
        if tier:
            stmt = stmt.where(User.tier == tier)
            count_stmt = count_stmt.where(User.tier == tier)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where((User.email.ilike(like)) | (User.username.ilike(like)))
            count_stmt = count_stmt.where((User.email.ilike(like)) | (User.username.ilike(like)))
        stmt = stmt.order_by(User.id.desc()).offset(skip).limit(limit)
        total = (await self.db.execute(count_stmt)).scalar_one()
        users = (await self.db.execute(stmt)).scalars().unique().all()
        return list(users), total

    async def update_user(self, user_id: int, payload: AdminUserUpdate) -> User | None:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return None
        data = payload.model_dump(exclude_unset=True)
        # 处理 group_id：
        #   - 显式传 null  → 移出用户组（tier 保持不变）
        #   - 传组 id      → 关联组并自动同步 tier
        #   - 未传         → 保持原样
        if "group_id" in data:
            gid = data["group_id"]
            if gid is None:
                user.group_id = None
            else:
                grp = (await self.db.execute(select(Group).where(Group.id == gid))).scalar_one_or_none()
                if not grp:
                    raise ValueError("用户组不存在")
                user.group_id = grp.id
                user.tier = grp.tier
        for k, v in data.items():
            if k == "group_id":
                continue
            setattr(user, k, v)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def assign_group(self, user_ids: list[int], group_id: int) -> int:
        grp = (await self.db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
        if not grp:
            return 0
        result = await self.db.execute(select(User).where(User.id.in_(user_ids)))
        users = result.scalars().all()
        for u in users:
            u.group_id = grp.id
            u.tier = grp.tier
        await self.db.commit()
        return len(users)

    async def delete_user(self, user_id: int) -> bool:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True

    async def count_admins(self, *, exclude_id: int | None = None) -> int:
        """统计管理员数量；exclude_id 用于“降级某管理员前”判断是否还有其他管理员。"""
        stmt = select(func.count(User.id)).where(User.is_admin.is_(True))
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        return (await self.db.execute(stmt)).scalar_one()

    async def get_group(self, group_id: int) -> Group | None:
        return (await self.db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()

    # ---------- 用户组管理 ----------
    async def list_groups(self) -> list[Group]:
        result = await self.db.execute(select(Group).order_by(Group.id))
        return list(result.scalars().all())

    async def create_group(self, payload: GroupCreate) -> Group:
        grp = Group(**payload.model_dump())
        self.db.add(grp)
        await self.db.commit()
        await self.db.refresh(grp)
        return grp

    async def update_group(self, group_id: int, payload: GroupUpdate) -> Group | None:
        grp = (await self.db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
        if not grp:
            return None
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(grp, k, v)
        await self.db.commit()
        await self.db.refresh(grp)
        return grp

    async def delete_group(self, group_id: int) -> bool:
        grp = (await self.db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
        if not grp:
            return False
        await self.db.delete(grp)
        await self.db.commit()
        return True

    # ---------- 审计 ----------
    async def log(self, *, actor_id: int | None, action: str, target: str | None = None,
                  detail: str | None = None, ip: str | None = None) -> None:
        entry = AuditLog(actor_id=actor_id, action=action, target=target, detail=detail, ip=ip)
        self.db.add(entry)
        await self.db.commit()
