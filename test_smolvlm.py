# -*- coding: utf-8 -*-
"""
测试SmolVLM连接的简单脚本
"""

import requests
import base64
import json
from PIL import Image
import io


def test_smolvlm_connection():
    """测试SmolVLM连接"""
    base_url = "http://localhost:8080"
    
    print("测试SmolVLM连接...")
    
    # 创建一个简单的测试图像
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_data = img_buffer.getvalue()
    
    image_base64_url = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"
    
    # 构建请求
    payload = {
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_base64_url}
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print("✓ SmolVLM连接成功！")
            print(f"响应: {data['choices'][0]['message']['content']}")
            return True
        else:
            print(f"✗ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False


if __name__ == "__main__":
    test_smolvlm_connection()
