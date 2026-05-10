# 导入必要的库和模块
import os  # 用于操作系统环境变量
from flask import Flask, request, jsonify, send_file  # Flask web框架相关功能
from cozepy import Coze, TokenAuth, ChatStatus, COZE_CN_BASE_URL, Message  # Coze AI服务SDK
from dotenv import load_dotenv  # 用于加载环境变量文件
import uuid  # 用于生成唯一的用户ID
import time  # 用于时间相关操作

# 加载.env文件中的环境变量
load_dotenv()

# 创建Flask应用实例
app = Flask(__name__)

# 用于存储会话状态的字典，key为客户端IP或自定义标识，value为会话信息
user_sessions = {}


# 定义Coze服务类，用于封装与Coze AI服务的交互
class CozeService:
    def __init__(self):
        # 从环境变量获取Coze API令牌，如果没有则返回None
        self.api_token = os.getenv("COZE_API_TOKEN")
        # 从环境变量获取机器人ID，如果没有则使用默认值
        self.bot_id = os.getenv("BOT_ID", "7552823978826694671")
        # 初始化Coze客户端，使用令牌认证和中国区基础URL
        self.coze = Coze(
            auth=TokenAuth(token=self.api_token),
            base_url=COZE_CN_BASE_URL
        )

    def get_sdk_response(self, user_message, user_identifier):
        """获取智能体响应，基于用户标识保持会话"""
        try:
            # 检查是否已有该用户的会话
            if user_identifier in user_sessions:
                session_data = user_sessions[user_identifier]
                conversation_id = session_data["conversation_id"]
                user_id = session_data["user_id"]

                # 构建用户消息
                messages = [
                    Message(
                        role="user",  # 消息角色为用户
                        content=user_message,  # 消息内容
                        content_type="text",  # 内容类型为文本
                        type="question"  # 消息类型为问题
                    )
                ]

                # 在现有会话中继续聊天
                chat = self.coze.chat.create(
                    bot_id=self.bot_id,  # 指定机器人ID
                    user_id=user_id,  # 使用相同的用户ID
                    conversation_id=conversation_id,  # 使用相同的会话ID
                    additional_messages=messages,  # 添加用户消息
                    auto_save_history=True  # 自动保存聊天历史
                )
            else:
                # 创建新的会话
                # 生成唯一的用户ID
                user_id = str(uuid.uuid4())

                # 构建用户消息
                messages = [
                    Message(
                        role="user",  # 消息角色为用户
                        content=user_message,  # 消息内容
                        content_type="text",  # 内容类型为文本
                        type="question"  # 消息类型为问题
                    )
                ]

                # 创建新的聊天会话
                chat = self.coze.chat.create(
                    bot_id=self.bot_id,  # 指定机器人ID
                    user_id=user_id,  # 指定用户ID
                    additional_messages=messages,  # 添加用户消息
                    auto_save_history=True  # 自动保存聊天历史
                )

                # 保存会话信息到user_sessions字典中
                user_sessions[user_identifier] = {
                    "conversation_id": chat.conversation_id,  # Coze的会话ID
                    "user_id": user_id,  # 用户ID
                    "chat_id": chat.id,  # 聊天ID
                    "created_at": time.time(),  # 会话创建时间戳
                    "last_activity": time.time()  # 最后活动时间
                }

            # 更新最后活动时间
            user_sessions[user_identifier]["last_activity"] = time.time()
            # 更新chat_id（每次新的聊天都会生成新的chat_id）
            user_sessions[user_identifier]["chat_id"] = chat.id

            # 轮询等待聊天完成，当聊天状态为"进行中"时继续查询
            while chat.status == ChatStatus.IN_PROGRESS:
                chat = self.coze.chat.retrieve(
                    conversation_id=chat.conversation_id,  # 会话ID
                    chat_id=chat.id  # 聊天ID
                )

            # 如果聊天状态为"已完成"，获取聊天消息
            if chat.status == ChatStatus.COMPLETED:
                messages = self.coze.chat.messages.list(
                    conversation_id=chat.conversation_id,  # 会话ID
                    chat_id=chat.id  # 聊天ID
                )
                # 遍历消息，找到助手的回复
                for msg in messages:
                    if msg.role == "assistant":
                        return {
                            "status": "success",
                            "content": msg.content
                        }
            # 如果对话未完成，返回失败状态
            return {"status": "failed", "content": "对话未完成"}

        except Exception as e:
            # 如果发生异常，返回错误状态和异常信息
            return {"status": "error", "content": str(e)}


# 创建CozeService实例
coze_service = CozeService()


@app.route('/')
def index():
    # 在返回页面之前清理过期会话
    cleanup_expired_sessions()

    # 返回index.html文件
    return send_file('index.html')


# 定义聊天路由，处理POST请求
@app.route('/chat', methods=['POST'])
def chat():
    # 从请求的JSON数据中获取用户消息
    data = request.json
    user_message = data.get('message')

    # 如果消息为空，返回错误
    if not user_message:
        return jsonify({"status": "error", "content": "消息不能为空"})

    # 使用客户端IP作为用户标识（也可以使用cookie或其他方式）
    user_identifier = request.remote_addr

    # 获取AI响应，基于用户标识保持会话
    response = coze_service.get_sdk_response(user_message, user_identifier)
    # 将响应转换为JSON格式返回
    return jsonify(response)


# 清理过期会话的辅助函数
def cleanup_expired_sessions():
    expired_sessions = []

    for user_identifier, session_data in user_sessions.items():
            expired_sessions.append(user_identifier)

    # 删除过期会话
    for user_identifier in expired_sessions:
        del user_sessions[user_identifier]


# 如果是直接运行此脚本，启动Flask应用
if __name__ == '__main__':
    # 启动应用，开启调试模式，端口为5000
    app.run(debug=True, port=5000)