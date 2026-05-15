import os
import json
from dotenv import load_dotenv
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 允许跨域请求


# 调用工作流生成视频
def create_video(animal_description):
    try:
        api_token = os.getenv('COZE_API_TOKEN')
        workflow_id = os.getenv('WORKFLOW_ID')

        # 初始化coze客户端
        coze = Coze(
            auth=TokenAuth(token=api_token),
            base_url=COZE_CN_BASE_URL
        )
        # 执行工作流
        workflow = coze.workflows.runs.create(
            workflow_id=workflow_id,
            parameters={
                "input":  animal_description
            }
        )

        # 接收返回的内容
        video_url = json.loads(workflow.data)['output']
        return  video_url

    except Exception as e:
        return None

# 声明接口路由
@app.route("/generate-video", methods=['POST'])
def generate_video():
    # 获取请求参数
    data = request.get_json()
    animal_description = data.get('input', '').strip()

    video_url = create_video(animal_description)

    return jsonify({
        'success': True,
        'video_url': video_url,
        'description': animal_description
    })


# 访问首页
@app.route('/')
def index():
    return send_file('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)