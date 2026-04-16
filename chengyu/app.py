# 这里调用智能体，同时获取智能体结果
import os
from datetime import datetime
import random

from flask import Flask, request, jsonify
from cozepy import Coze, TokenAuth, Message, COZE_CN_BASE_URL, ChatStatus
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 创建一个Flask的应用实例
app = Flask(__name__)

COMMON_IDIOMS = ['一心一意','三心二意']

# 射界游戏的逻辑
class IdiomGame:

    # 创建初始化方法
    def __init__(self):
        self.api_token = os.environ.get("COZE_API_TOKEN")
        self.bot_id =  os.environ.get("BOT_ID")
        self.user_id = os.environ.get("USER_ID")

        # 初始化成语接龙状态
        self.current_idiom = self.get_random_idiom()
        # 成语的历史记录
        self.game_history = []

        # 初始化coze的实例对象
        self.coze = Coze(
            auth=TokenAuth(self.api_token),
            base_url=COZE_CN_BASE_URL
        )

    # 获取随机的初始成语
    def get_random_idiom(self):
        return random.choice(COMMON_IDIOMS)

    # 添加成语到历史记录
    def add_to_history(self, user_idiom, sdk_response):
        record = {
            "user": user_idiom,
            "ai": sdk_response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        self.game_history.insert(0, record)

        # 历史记录需要有一个长度的上线 20
        if len(self.game_history) > 20:
            self.game_history = self.game_history[:20]

    # 访问智能体获取成语
    def get_sdk_response(self, user_input):  # 只改这里：inpit → input
        # 异常捕获
        try:
            message = [
                Message(
                    role="user",
                    content=f"成语接龙游戏，上一个成语是：{self.current_idiom}，请接下一个成语",
                    content_type="text",
                    type="question",
                ),
                Message(
                    role="user",
                    content=user_input,  # 只改这里：inpit → input
                    content_type="text",
                    type="question",
                )
            ]

            # 给智能体发送消息
            chat = self.coze.chat.create(
                bot_id=self.bot_id,
                user_id=self.user_id,
                additional_messages=message,
                auto_save_history=True
            )

            # 等待智能体返回的成语结果
            while chat.status == ChatStatus.IN_PROGRESS:
                chat = self.coze.chat.retrieve(
                    conversation_id=chat.conversation_id,
                    chat_id=chat.id
                )

            if chat.status == ChatStatus.COMPLETED:
                # 获取对话中的消息
                message = self.coze.chat.messages.list(  # 只改这里：去掉空格
                    conversation_id=chat.conversation_id,
                    chat_id=chat.id
                )

            sdk_response = None
            for msg in message:
                if hasattr(msg, "role") and msg.role == "assistant":
                    sdk_response = msg.content.strip()
                    sdk_response = "".join(filter(lambda x: '\u4e00' <= x <= '\u9fff', sdk_response))  # 只改这里：/u → \u
                    break

            if sdk_response and len(sdk_response) ==  4:
                self.add_to_history(user_input, sdk_response)  # 只改这里：inpit → input
                self.current_idiom = sdk_response

            # 成功的返回结果
            return {
                'success': True,
                'sdk_response': sdk_response,
                'current_idiom': self.current_idiom,
                'history': self.game_history
            }


        except Exception as e:
            return {"success" : False , "error" : str(e)}

game = IdiomGame()

# 接口路由
@app.route("/api/play", methods=["POST"])
def play_game():
    # 1. 接接收请求参数
    data = request.get_json()
    user_input = data.get('idiom', '').strip()

    if len(user_input) != 4:
        return jsonify({"error":"请输入4字成语"})  # 只改这里：变成合法JSON

    # 2. 发送COZE调用SDK的请求
    result = game.get_sdk_response(user_input)
    # 3.返回结果
    return jsonify(result)


# 程序启动入口
if __name__ == "__main__":
    app.run(debug=True, port=5000)