"""导入所有模型以便 Alembic 自动发现"""
from ..db.session import Base  # noqa: F401
from ..models.user import User  # noqa: F401
from ..models.group import Group  # noqa: F401
from ..models.audit import AuditLog  # noqa: F401
