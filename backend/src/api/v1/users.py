"""当前用户相关接口"""
from datetime import datetime
from pathlib import Path
import io

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from PIL import Image

from ...core.deps import CurrentUser, DbSession
from ...schemas.user import (
    ChangePasswordRequest,
    NotificationSettingsRequest,
    ProfileCompleteRequest,
    ProfileUpdateRequest,
    UserOut,
)
from ...services.user_service import UserService
from ...services.log_service import LogService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(current: CurrentUser) -> UserOut:
    return UserOut.model_validate(current)


@router.post("/me/complete-profile", response_model=UserOut)
async def complete_profile(
    payload: ProfileCompleteRequest, current: CurrentUser, db: DbSession
) -> UserOut:
    """完善个人信息（首次）"""
    # 验证角色对应字段
    if payload.role == "student":
        if not payload.student_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "学生必须填写学号")
        if not payload.major:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "学生必须填写专业")
    elif payload.role == "teacher":
        if not payload.college:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "老师必须填写学院")

    # 更新用户信息
    current.real_name = payload.real_name
    current.role = payload.role
    current.student_id = payload.student_id if payload.role == "student" else None
    current.school = payload.school
    current.major = payload.major if payload.role == "student" else None
    current.college = payload.college if payload.role == "teacher" else None
    current.email = payload.email.lower()  # 更新邮箱
    current.profile_completed = True
    current.profile_completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(current)

    # 记录日志
    log_service = LogService(db)
    try:
        await log_service.log(
            user_id=current.id,
            action="user.complete_profile",
            resource_type="user",
            resource_id=str(current.id),
            details={"role": payload.role}
        )
    except Exception:
        pass

    return UserOut.model_validate(current)


@router.patch("/me/profile", response_model=UserOut)
async def update_profile(payload: ProfileUpdateRequest, current: CurrentUser, db: DbSession) -> UserOut:
    """更新个人信息"""
    fields_updated = []

    # 只更新提供的字段
    if payload.real_name is not None:
        current.real_name = payload.real_name
        fields_updated.append("real_name")
    if payload.role is not None:
        current.role = payload.role
        fields_updated.append("role")
    if payload.student_id is not None:
        current.student_id = payload.student_id
        fields_updated.append("student_id")
    if payload.school is not None:
        current.school = payload.school
        fields_updated.append("school")
    if payload.major is not None:
        current.major = payload.major
        fields_updated.append("major")
    if payload.college is not None:
        current.college = payload.college
        fields_updated.append("college")
    if payload.phone is not None:
        current.phone = payload.phone
        fields_updated.append("phone")
    if payload.email is not None:
        current.email = payload.email.lower()
        fields_updated.append("email")

    await db.commit()
    await db.refresh(current)

    # 记录日志
    if fields_updated:
        log_service = LogService(db)
        try:
            await log_service.log_profile_update(
                user_id=current.id,
                fields_updated=fields_updated
            )
        except Exception:
            pass

    return UserOut.model_validate(current)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(payload: ChangePasswordRequest, current: CurrentUser, db: DbSession) -> None:
    svc = UserService(db)
    ok = await svc.change_password(current, payload.old_password, payload.new_password)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "原密码错误")

    # 记录日志
    log_service = LogService(db)
    try:
        await log_service.log_password_change(user_id=current.id)
    except Exception:
        pass


@router.get("/me/export")
async def export_user_data(current: CurrentUser) -> JSONResponse:
    """导出个人数据"""
    # 手机号脱敏
    phone_masked = None
    if current.phone:
        phone_masked = current.phone[:3] + "****" + current.phone[-4:]

    data = {
        "user_id": current.id,
        "username": current.username,
        "email": current.email,
        "real_name": current.real_name,
        "role": current.role,
        "school": current.school,
        "major": current.major,
        "college": current.college,
        "student_id": current.student_id,
        "phone": phone_masked,
        "tier": current.tier.value if current.tier else None,
        "is_admin": current.is_admin,
        "is_active": current.is_active,
        "profile_completed": current.profile_completed,
        "created_at": current.created_at.isoformat() if current.created_at else None,
        "last_login_at": current.last_login_at.isoformat() if current.last_login_at else None,
        "export_time": datetime.utcnow().isoformat(),
    }

    return JSONResponse(content=data)


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current: CurrentUser = None,
    db: DbSession = None
) -> UserOut:
    """上传头像"""
    # 验证文件类型
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/jpg"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "仅支持 JPG、PNG、GIF 格式")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小（2MB）
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文件大小不能超过2MB")

    try:
        # 打开图片
        img = Image.open(io.BytesIO(content))

        # 转换为RGB（处理PNG透明通道）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # 缩放到200x200
        img = img.resize((200, 200), Image.Resampling.LANCZOS)

        # 确保上传目录存在
        avatar_dir = Path("uploads/avatars")
        avatar_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        filename = f"{current.id}.jpg"
        filepath = avatar_dir / filename
        img.save(filepath, "JPEG", quality=85)

        # 更新数据库
        current.avatar_url = f"/uploads/avatars/{filename}"
        await db.commit()
        await db.refresh(current)

        # 记录日志
        log_service = LogService(db)
        try:
            await log_service.log_avatar_upload(
                user_id=current.id,
                filename=filename,
                file_size=len(content)
            )
        except Exception:
            pass

        return UserOut.model_validate(current)

    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"图片处理失败: {str(e)}")


@router.patch("/me/notifications", response_model=UserOut)
async def update_notifications(
    payload: NotificationSettingsRequest, current: CurrentUser, db: DbSession
) -> UserOut:
    """更新通知设置"""
    if payload.notification_email is not None:
        current.notification_email = payload.notification_email
    if payload.notification_system is not None:
        current.notification_system = payload.notification_system
    if payload.notification_course is not None:
        current.notification_course = payload.notification_course
    if payload.notification_announcement is not None:
        current.notification_announcement = payload.notification_announcement

    await db.commit()
    await db.refresh(current)
    return UserOut.model_validate(current)
