"""邮件发送服务 —— 邮箱验证 / 忘记密码。

设计要点：
- 用标准库 smtplib（SMTP_SSL，465 端口 implicit SSL）+ asyncio.to_thread 异步发信，
  零第三方依赖，无需重建镜像。
- Mailer 单例可替换：未配置 SMTP 或测试环境降级为 _NoopMailer（不报错、不阻塞业务）。
- 发信 best-effort：失败仅记录日志，不抛异常给调用方（注册/找回流程不应因邮件故障 500）。
- 链接基础地址来自 settings.APP_BASE_URL；token 存 Redis（见 auth.py），这里只负责拼链接与发信。
"""
import asyncio
import logging
import smtplib
from email.message import EmailMessage

from .config import settings

logger = logging.getLogger(__name__)


class _NoopMailer:
    """不发信（未配置 SMTP / 测试环境用）。"""
    async def send(self, to: str, subject: str, html: str) -> None:
        logger.debug("[mail-noop] 收件=%s 主题=%s（未发送）", to, subject)


class _SmtpMailer:
    """基于 smtplib.SMTP_SSL 的同步发信，通过 to_thread 异步化。"""
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_addr = settings.smtp_from
        self.use_ssl = settings.SMTP_USE_SSL
        self.timeout = settings.SMTP_TIMEOUT

    def _send_sync(self, to: str, subject: str, html: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content("请使用支持 HTML 的邮件客户端查看本邮件。")
        msg.add_alternative(html, subtype="html")
        # 465 = implicit SSL；587 = STARTTLS。按配置选择。
        if self.use_ssl:
            client_cls = smtplib.SMTP_SSL
            with client_cls(self.host, self.port, timeout=self.timeout) as s:
                s.login(self.user, self.password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as s:
                s.starttls()
                s.login(self.user, self.password)
                s.send_message(msg)

    async def send(self, to: str, subject: str, html: str) -> None:
        await asyncio.to_thread(self._send_sync, to, subject, html)


_mailer = None


def get_mailer():
    """返回 Mailer 单例。未配置 SMTP 时降级为 Noop。"""
    global _mailer
    if _mailer is None:
        _mailer = _SmtpMailer() if settings.smtp_configured else _NoopMailer()
    return _mailer


def use_noop_mailer() -> None:
    """测试用：强制切换到 Noop。"""
    global _mailer
    _mailer = _NoopMailer()


def reset_mailer() -> None:
    """测试用：重置单例，下次 get_mailer 按 settings 重新决定。"""
    global _mailer
    _mailer = None


async def _safe_send(to: str, subject: str, html: str) -> None:
    """best-effort 发信：失败仅记日志，不抛异常。"""
    try:
        await get_mailer().send(to, subject, html)
    except Exception as e:
        logger.warning("[mail] 发信失败 收件=%s 主题=%s 错误=%s: %s",
                       to, subject, type(e).__name__, e)


def _verify_link(token: str) -> str:
    return f"{settings.APP_BASE_URL.rstrip('/')}/verify-email?token={token}"


def _reset_link(token: str) -> str:
    return f"{settings.APP_BASE_URL.rstrip('/')}/reset-password?token={token}"


async def send_verification_email(to_email: str, token: str) -> None:
    subject = f"【{settings.APP_NAME}】请验证你的邮箱"
    html = f"""\
<div style="font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:560px;margin:auto;padding:24px;">
  <h2 style="color:#024BA1;">欢迎注册 {settings.APP_NAME}</h2>
  <p>请点击下方按钮验证你的邮箱地址（链接 {settings.VERIFY_TOKEN_TTL_MINUTES} 分钟内有效）：</p>
  <p style="margin:24px 0;">
    <a href="{_verify_link(token)}" style="display:inline-block;padding:12px 28px;background:#024BA1;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">验证邮箱</a>
  </p>
  <p style="color:#64748b;font-size:13px;">若按钮无法点击，请复制以下链接到浏览器：<br>{_verify_link(token)}</p>
  <p style="color:#94a3b8;font-size:12px;">如非本人操作，请忽略本邮件。</p>
</div>"""
    await _safe_send(to_email, subject, html)


async def send_reset_email(to_email: str, token: str) -> None:
    subject = f"【{settings.APP_NAME}】重置你的密码"
    html = f"""\
<div style="font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:560px;margin:auto;padding:24px;">
  <h2 style="color:#024BA1;">重置密码</h2>
  <p>我们收到了你的密码重置请求。点击下方按钮设置新密码（链接 {settings.RESET_TOKEN_TTL_MINUTES} 分钟内有效）：</p>
  <p style="margin:24px 0;">
    <a href="{_reset_link(token)}" style="display:inline-block;padding:12px 28px;background:#024BA1;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">重置密码</a>
  </p>
  <p style="color:#64748b;font-size:13px;">若按钮无法点击，请复制以下链接到浏览器：<br>{_reset_link(token)}</p>
  <p style="color:#94a3b8;font-size:12px;">如非本人操作，请忽略本邮件，你的密码不会变更。</p>
</div>"""
    await _safe_send(to_email, subject, html)


async def send_email_code(to_email: str, code: str) -> None:
    """发送邮箱验证码（用于注册）"""
    subject = f"【{settings.APP_NAME}】邮箱验证码"
    html = f"""\
<div style="font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:560px;margin:auto;padding:24px;">
  <h2 style="color:#024BA1;">邮箱验证码</h2>
  <p>您好！</p>
  <p>您正在注册 {settings.APP_NAME}，验证码为：</p>
  <p style="margin:24px 0;text-align:center;">
    <span style="display:inline-block;padding:16px 32px;background:#F0F7FF;color:#024BA1;font-size:32px;font-weight:700;letter-spacing:8px;border-radius:8px;font-family:'Courier New',monospace;">{code}</span>
  </p>
  <p style="color:#64748b;font-size:14px;">验证码5分钟内有效，请尽快完成注册。</p>
  <p style="color:#94a3b8;font-size:12px;">如非本人操作，请忽略此邮件。</p>
</div>"""
    await _safe_send(to_email, subject, html)
