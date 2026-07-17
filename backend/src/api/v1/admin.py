"""管理员后台 API"""
from fastapi import APIRouter, HTTPException, Query, Request, status

from ...core.deps import AdminUser, DbSession
from ...models.user import UserTier
from ...schemas.admin import (
    AdminCreateUser,
    AdminUserUpdate,
    AssignGroupRequest,
    GroupCreate,
    GroupUpdate,
)
from ...schemas.user import GroupOut, UserOut
from ...services.admin_service import AdminService
from ...services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------- 用户管理 ----------
@router.get("/users")
async def list_users(
    admin: AdminUser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    tier: UserTier | None = None,
    keyword: str | None = None,
) -> dict:
    svc = AdminService(db)
    users, total = await svc.list_users(skip=skip, limit=limit, tier=tier, keyword=keyword)
    return {
        "total": total,
        "items": [UserOut.model_validate(u) for u in users],
    }


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: AdminCreateUser, admin: AdminUser, db: DbSession) -> UserOut:
    # 预校验组存在，避免建号后才发现组无效
    if payload.group_id is not None and not await AdminService(db).get_group(payload.group_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户组不存在")
    usvc = UserService(db)
    if await usvc.get_by_email(payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已存在")
    user = await usvc.create(
        email=payload.email,
        username=payload.username,
        password=payload.password,
        tier=payload.tier,
        is_admin=payload.is_admin,
    )
    if payload.group_id is not None:
        try:
            await AdminService(db).update_user(user.id, AdminUserUpdate(group_id=payload.group_id))
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
        user = await usvc.get_by_id(user.id)
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, payload: AdminUserUpdate, admin: AdminUser, db: DbSession, request: Request
) -> UserOut:
    svc = AdminService(db)
    # 自我保护：不能取消自己的管理员权限 / 停用自己
    if user_id == admin.id:
        if payload.is_admin is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能取消自己的管理员权限")
        if payload.is_active is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能停用自己的账号")
    # 最后一个管理员保护
    if payload.is_admin is False and await svc.count_admins(exclude_id=user_id) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "至少需保留一个管理员")
    try:
        user = await svc.update_user(user_id, payload)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    await svc.log(
        actor_id=admin.id,
        action="update_user",
        target=str(user_id),
        detail=payload.model_dump_json(exclude_unset=True),
        ip=request.client.host if request.client else None,
    )
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin: AdminUser, db: DbSession) -> None:
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能删除自己")
    svc = AdminService(db)
    ok = await svc.delete_user(user_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    await svc.log(actor_id=admin.id, action="delete_user", target=str(user_id))


@router.post("/users/assign-group")
async def assign_group(payload: AssignGroupRequest, admin: AdminUser, db: DbSession) -> dict:
    svc = AdminService(db)
    affected = await svc.assign_group(payload.user_ids, payload.group_id)
    await svc.log(
        actor_id=admin.id,
        action="assign_group",
        target=str(payload.group_id),
        detail=f"users={payload.user_ids}",
    )
    return {"affected": affected}


# ---------- 用户组管理 ----------
@router.get("/groups", response_model=list[GroupOut])
async def list_groups(admin: AdminUser, db: DbSession) -> list[GroupOut]:
    svc = AdminService(db)
    return [GroupOut.model_validate(g) for g in await svc.list_groups()]


@router.post("/groups", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(payload: GroupCreate, admin: AdminUser, db: DbSession) -> GroupOut:
    svc = AdminService(db)
    grp = await svc.create_group(payload)
    await svc.log(actor_id=admin.id, action="create_group", target=str(grp.id))
    return GroupOut.model_validate(grp)


@router.patch("/groups/{group_id}", response_model=GroupOut)
async def update_group(group_id: int, payload: GroupUpdate, admin: AdminUser, db: DbSession) -> GroupOut:
    svc = AdminService(db)
    grp = await svc.update_group(group_id, payload)
    if not grp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户组不存在")
    return GroupOut.model_validate(grp)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, admin: AdminUser, db: DbSession) -> None:
    svc = AdminService(db)
    ok = await svc.delete_group(group_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户组不存在")
