# -*- coding: utf-8 -*-
"""
SmolVLM API 客户端模块
"""

import requests
import base64
import json
from typing import Optional
from config import *


class SmolVLMClient:
    """SmolVLM API 客户端"""

    def __init__(self, base_url: str = SMOLVLM_BASE_URL):
        self.base_url = base_url
        self.endpoint = SMOLVLM_ENDPOINT
        self.session = requests.Session()
        self.debug_callback = None  # 调试信息回调函数

    def set_debug_callback(self, callback):
        """设置调试信息回调函数"""
        self.debug_callback = callback

    def encode_image_to_base64(self, image_data: bytes) -> str:
        """将图像数据编码为base64格式"""
        return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"

    def send_chat_completion_request(self, instruction: str, image_base64_url: str,
                                   max_tokens: int = 600) -> Optional[str]:
        """发送聊天完成请求到SmolVLM API"""
        try:
            url = f"{self.base_url}{self.endpoint}"

            # payload = {
            #     "max_tokens": max_tokens,
            #     "messages": [
            #         {
            #             "role": "user",
            #             "content": [
            #                 {"type": "text", "text": instruction},
            #                 {
            #                     "type": "image_url",
            #                     "image_url": {"url": image_base64_url}
            #                 }
            #             ]
            #         }
            #     ],
            #      "response_format": { "type": "json_object" }
            # }

            payload = {
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [
                    {   # 约束搬到 system
                        "role": "system",
                        "content": [
                            {"type": "text", "text": instruction}
                        ]
                    },
                    {   # 真正的任务
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Detect faces."},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_base64_url}
                            }
                        ]
                    }
                ]
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = self.session.post(url, json=payload, headers=headers, timeout=30)

            if not response.ok:
                error_text = response.text
                print(f"SmolVLM API 错误: {response.status_code} - {error_text}")
                error_response = f"服务器错误: {response.status_code} - {error_text}"

                # 记录调试信息
                if self.debug_callback:
                    self.debug_callback(instruction, error_response)

                return error_response

            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                response_content = data['choices'][0]['message']['content']

                # 记录调试信息
                if self.debug_callback:
                    self.debug_callback(instruction, response_content)

                return response_content
            else:
                print("SmolVLM API 响应格式错误")
                error_response = "API响应格式错误"

                # 记录调试信息
                if self.debug_callback:
                    self.debug_callback(instruction, error_response)

                return error_response

        except requests.exceptions.Timeout:
            print("SmolVLM API 请求超时")
            error_response = "请求超时"
            if self.debug_callback:
                self.debug_callback(instruction, error_response)
            return error_response
        except requests.exceptions.ConnectionError:
            print("无法连接到SmolVLM API")
            error_response = "连接错误"
            if self.debug_callback:
                self.debug_callback(instruction, error_response)
            return error_response
        except requests.exceptions.RequestException as e:
            print(f"SmolVLM API 请求异常: {e}")
            error_response = f"请求异常: {e}"
            if self.debug_callback:
                self.debug_callback(instruction, error_response)
            return error_response
        except json.JSONDecodeError as e:
            print(f"SmolVLM API 响应JSON解析错误: {e}")
            error_response = "响应解析错误"
            if self.debug_callback:
                self.debug_callback(instruction, error_response)
            return error_response
        except Exception as e:
            print(f"SmolVLM API 未知错误: {e}")
            error_response = f"未知错误: {e}"
            if self.debug_callback:
                self.debug_callback(instruction, error_response)
            return error_response

    def detect_faces(self, image_base64_url: str) -> Optional[str]:
        """使用SmolVLM检测人脸"""
        return self.send_chat_completion_request(
            FACE_DETECTION_PROMPT,
            image_base64_url
        )

    def analyze_image(self, image_base64_url: str, custom_prompt: str) -> Optional[str]:
        """使用自定义提示分析图像"""
        return self.send_chat_completion_request(
            custom_prompt,
            image_base64_url
        )

    def test_connection(self) -> bool:
        """测试与SmolVLM API的连接"""
        try:
            # 简单的健康检查，不发送图像
            import requests
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            # 如果没有health端点，尝试发送一个简单的请求
            try:
                # 创建一个最小的JPEG图像
                import io
                from PIL import Image

                # 创建一个10x10的白色图像
                img = Image.new('RGB', (10, 10), color='white')
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG')
                img_data = img_buffer.getvalue()

                test_image_url = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"

                response = self.send_chat_completion_request(
                    "What do you see?",
                    test_image_url
                )

                return response is not None and not response.startswith("服务器错误") and not response.startswith("连接错误")

            except Exception as e:
                print(f"连接测试失败: {e}")
                return False
