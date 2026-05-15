import os

from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file, app
from pyparsing import results

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 起始的页面
@app.route("/")
def index():
    return send_file('index.html')

# 把创建Coze客户端的工作写到路由里
# @app.route('/generate_images', methods=['POST'])
# def generate_images():
#     # 1.创建coze客户端
#
#     api_token = os.getenv('COZE_API_TOKEN')
#     workflow_id = os.getenv('WORKFLOW_ID')
#
#     coze = Coze(
#         auth=TokenAuth(token=api_token),
#         base_url=COZE_CN_BASE_URL
#     )
#
#     # 2.执行工作流
#
#     ## 2.1接收用户传递的参数
#     user_input = request.json.get('input','')
#
#     workflow = coze.workflows.runs.create(
#         workflow_id=workflow_id,
#         parameters={
#             "input": user_input
#         }
#     )
#
#     print(workflow.data)
#     results = workflow.data[:2]
#
#     return jsonify({'images': results})

import json


@app.route('/generate_images', methods=['POST'])
def generate_images():
    api_token = os.getenv('COZE_API_TOKEN')
    workflow_id = os.getenv('WORKFLOW_ID')
    coze = Coze(
        auth=TokenAuth(token=api_token),
        base_url=COZE_CN_BASE_URL
    )
    user_input = request.json.get('input', '')
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters={"input": user_input}
    )

    # workflow.data 是字符串，需要先解析
    data = workflow.data
    if isinstance(data, str):
        data = json.loads(data)

    results = data.get('output', [])[:2]
    return jsonify({'images': results})


# 服务启动入口
if __name__ == '__main__':
    app.run(debug=True, port=5000)

