from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.sms.v20210111 import sms_client, models
import logging
import configparser

class TencentSMS:
    def __init__(self):
        """
        初始化腾讯云短信客户端
        """
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        # 获取腾讯云配置
        self.secret_id = config.get('TencentCloud', 'secret_id', fallback='')
        self.secret_key = config.get('TencentCloud', 'secret_key', fallback='')
        self.sms_app_id = config.get('TencentCloud', 'sms_app_id', fallback='')
        self.sms_sign = config.get('TencentCloud', 'sms_sign', fallback='')
        self.sms_template_id = config.get('TencentCloud', 'sms_template_id', fallback='')
        
        # 检查配置是否完整
        self.is_configured = self.secret_id and self.secret_key and self.sms_app_id and self.sms_sign and self.sms_template_id
        
        if self.is_configured:
            try:
                # 初始化认证信息
                self.cred = credential.Credential(self.secret_id, self.secret_key)
                
                # 初始化HTTP选项
                httpProfile = HttpProfile()
                httpProfile.endpoint = "sms.tencentcloudapi.com"
                
                # 初始化客户端选项
                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile
                
                # 初始化短信客户端
                self.client = sms_client.SmsClient(self.cred, "ap-guangzhou", clientProfile)
                logging.info("腾讯云短信客户端初始化成功")
            except Exception as e:
                logging.error(f"腾讯云短信客户端初始化失败: {e}")
                self.is_configured = False
        else:
            logging.warning("腾讯云短信配置不完整，短信发送功能将不可用")
    
    def send_sms(self, phone_number, username, consecutive_days):
        """
        发送短信
        :param phone_number: 收件人手机号
        :param username: 用户名
        :param consecutive_days: 连续未签到天数
        :return: 发送结果字典，包含success（布尔值）和message（字符串）
        """
        if not self.is_configured:
            return {
                'success': False,
                'message': "腾讯云短信配置不完整"
            }
        
        try:
            # 准备请求参数
            req = models.SendSmsRequest()
            req.SmsSdkAppId = self.sms_app_id
            req.SignName = self.sms_sign
            req.TemplateId = self.sms_template_id
            # 格式化手机号，确保以+86开头
            formatted_phone = phone_number
            if not formatted_phone.startswith("+"):
                formatted_phone = f"+86{formatted_phone}"
            req.PhoneNumberSet = [formatted_phone]
            # 模板参数：[用户名, 连续未签到天数]
            req.TemplateParamSet = [username, str(consecutive_days)]
            
            # 发送短信
            resp = self.client.SendSms(req)
            
            # 处理响应结果
            if resp.SendStatusSet and len(resp.SendStatusSet) > 0:
                status = resp.SendStatusSet[0]
                if status.Code == "Ok":
                    logging.info(f"短信发送成功: {phone_number}，消息ID: {status.MessageId}")
                    return {
                        'success': True,
                        'message': f"短信发送成功，消息ID: {status.MessageId}"
                    }
                else:
                    logging.error(f"短信发送失败: {phone_number}，错误码: {status.Code}，错误信息: {status.Message}")
                    return {
                        'success': False,
                        'message': f"短信发送失败，错误码: {status.Code}，错误信息: {status.Message}"
                    }
            else:
                logging.error(f"短信发送失败: {phone_number}，未返回发送状态")
                return {
                    'success': False,
                    'message': "短信发送失败，未返回发送状态"
                }
        except Exception as e:
            logging.error(f"发送短信时出错: {e}")
            return {
                'success': False,
                'message': f"发送短信时出错: {str(e)}"
            }

# 测试代码
if __name__ == "__main__":
    # 初始化腾讯云短信客户端
    sms_client = TencentSMS()
    
    # 发送测试短信
    result = sms_client.send_sms(
        phone_number="13800138000",
        username="测试用户",
        consecutive_days=2
    )
    
    print(f"短信发送测试结果: {result}")
