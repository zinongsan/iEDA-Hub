"""短信发送服务 - 手机验证码

支持多个短信服务商:
- 阿里云短信 (Alibaba Cloud SMS)
- 腾讯云短信 (Tencent Cloud SMS)
- 模拟发送 (用于开发测试)

设计要点:
- 异步发送,不阻塞主流程
- 失败时仅记录日志,不抛异常
- 未配置时降级为控制台输出(开发环境)
"""
import asyncio
import logging
import secrets

from .config import settings

logger = logging.getLogger(__name__)


class _NoopSmsService:
    """模拟短信服务(开发/测试环境用) - 直接在控制台打印验证码"""
    async def send_verification_code(self, phone: str, code: str) -> bool:
        logger.info(f"[SMS-NOOP] 发送验证码到 {phone}: {code}")
        print(f"\n{'='*50}")
        print(f"📱 短信验证码 (开发模式)")
        print(f"手机号: {phone}")
        print(f"验证码: {code}")
        print(f"{'='*50}\n")
        return True


class _AliyunSmsService:
    """阿里云短信服务"""
    def __init__(self):
        self.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        self.sign_name = settings.ALIYUN_SMS_SIGN_NAME
        self.template_code = settings.ALIYUN_SMS_TEMPLATE_CODE

    async def send_verification_code(self, phone: str, code: str) -> bool:
        """发送验证码短信"""
        try:
            # 这里需要安装 aliyun-python-sdk-core 和 aliyun-python-sdk-dysmsapi
            # pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest

            client = AcsClient(self.access_key_id, self.access_key_secret, 'cn-hangzhou')

            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')

            request.add_query_param('PhoneNumbers', phone)
            request.add_query_param('SignName', self.sign_name)
            request.add_query_param('TemplateCode', self.template_code)
            request.add_query_param('TemplateParam', f'{{"code":"{code}"}}')

            response = await asyncio.to_thread(client.do_action_with_exception, request)
            logger.info(f"[SMS-ALIYUN] 发送成功: {phone}")
            return True
        except Exception as e:
            logger.error(f"[SMS-ALIYUN] 发送失败: {phone}, 错误: {e}")
            return False


class _TencentSmsService:
    """腾讯云短信服务"""
    def __init__(self):
        self.secret_id = settings.TENCENT_SECRET_ID
        self.secret_key = settings.TENCENT_SECRET_KEY
        self.app_id = settings.TENCENT_SMS_APP_ID
        self.sign_name = settings.TENCENT_SMS_SIGN_NAME
        self.template_id = settings.TENCENT_SMS_TEMPLATE_ID

    async def send_verification_code(self, phone: str, code: str) -> bool:
        """发送验证码短信"""
        try:
            # 这里需要安装 tencentcloud-sdk-python
            # pip install tencentcloud-sdk-python
            from tencentcloud.common import credential
            from tencentcloud.sms.v20210111 import sms_client, models

            cred = credential.Credential(self.secret_id, self.secret_key)
            client = sms_client.SmsClient(cred, "ap-guangzhou")

            req = models.SendSmsRequest()
            req.SmsSdkAppId = self.app_id
            req.SignName = self.sign_name
            req.TemplateId = self.template_id
            req.TemplateParamSet = [code]
            req.PhoneNumberSet = [f"+86{phone}"]

            resp = await asyncio.to_thread(client.SendSms, req)
            logger.info(f"[SMS-TENCENT] 发送成功: {phone}")
            return True
        except Exception as e:
            logger.error(f"[SMS-TENCENT] 发送失败: {phone}, 错误: {e}")
            return False


# 全局单例
_sms_service = None


def get_sms_service():
    """获取短信服务实例"""
    global _sms_service
    if _sms_service is None:
        sms_provider = getattr(settings, 'SMS_PROVIDER', 'noop')

        if sms_provider == 'aliyun':
            _sms_service = _AliyunSmsService()
        elif sms_provider == 'tencent':
            _sms_service = _TencentSmsService()
        else:
            # 默认使用模拟服务(开发环境)
            _sms_service = _NoopSmsService()

    return _sms_service


def use_noop_sms() -> None:
    """测试用: 强制使用模拟服务"""
    global _sms_service
    _sms_service = _NoopSmsService()


def reset_sms_service() -> None:
    """测试用: 重置单例"""
    global _sms_service
    _sms_service = None


async def send_sms_code(phone: str, code: str) -> bool:
    """发送短信验证码 (统一入口)

    Args:
        phone: 手机号
        code: 验证码

    Returns:
        bool: 是否发送成功
    """
    try:
        service = get_sms_service()
        return await service.send_verification_code(phone, code)
    except Exception as e:
        logger.error(f"[SMS] 发送验证码失败: {phone}, 错误: {e}")
        return False
