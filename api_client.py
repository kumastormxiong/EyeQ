import requests
import base64
import os
from mimetypes import guess_type

def encode_image_to_base64(image_path):
    """
    将本地图像文件编码为Base64数据URI。
    这种格式可以直接嵌入到API请求中。

    :param image_path: 图像文件的本地路径 (str)
    :return: Base64编码后的数据URI (str)，如果文件不存在或不是图片则可能出错
    """
    mime_type, _ = guess_type(image_path)
    if not mime_type or not mime_type.startswith('image'):
        mime_type = 'image/png'  # 如果无法猜测MIME类型，则默认为png
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded_string}"

def send_question(api_key, question, image_path=None):
    """
    使用与OpenAI兼容的模式，将问题（和可选的图片）发送到通义千问大模型。

    :param api_key: 你的通义千问API密钥 (str)
    :param question: 用户提出的文本问题 (str)
    :param image_path: 可选的、与问题相关的本地图片路径 (str)
    :return: API返回的文本回答 (str)。如果请求失败或返回格式错误，则返回错误信息。
    """
    # 使用通义千问最新的OpenAI兼容模式API Endpoint
    url = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # 构建符合最新VLM模型文档的messages结构
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}],
        }
    ]
    
    user_content = []
    # 如果有图片，将其编码并添加到user_content中
    if image_path and os.path.exists(image_path):
        base64_image_uri = encode_image_to_base64(image_path)
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": base64_image_uri
            },
        })

    # 将文本问题添加到user_content中
    user_content.append({
        "type": "text",
        "text": question
    })

    # 将最终的用户内容添加到messages列表中
    messages.append({
        "role": "user",
        "content": user_content
    })

    # 准备发送到API的完整数据包
    data = {
        'model': 'qwen-vl-plus',  # 您也可以按需更换为 qwen-vl-max
        'messages': messages
    }
    
    # 发送POST请求
    response = requests.post(url, json=data, headers=headers)
    
    # 检查HTTP请求是否成功，如果不成功（如4xx或5xx错误），则会抛出异常
    response.raise_for_status()
    
    result = response.json()
    # 解析并返回模型生成的回答
    if result.get('choices') and result['choices'][0].get('message'):
        return result['choices'][0].get('message', {}).get('content', '')
    else:
        return f"API返回格式错误: {result}" 