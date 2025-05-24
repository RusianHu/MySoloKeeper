# -*- coding: utf-8 -*-
"""
MySoloKeeper 配置文件
"""

# SmolVLM API 配置
SMOLVLM_BASE_URL = "http://localhost:8080"
SMOLVLM_ENDPOINT = "/v1/chat/completions"

# 摄像头配置
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# 界面配置
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_TITLE = "MySoloKeeper - 打灰机守护程序"

# 人脸检测配置
FACE_DETECTION_PROMPT = """IMPORTANT: You must ONLY detect faces in this image and return ONLY their bounding box coordinates in EXACTLY this JSON format: {"faces": [{"x": number, "y": number, "width": number, "height": number}]}. If no faces are detected, return {"faces": []}. DO NOT describe the image. DO NOT add any other text. ONLY return the JSON. NEVER make up coordinates if you don't see a face."""

# 坐标处理配置
MIN_FACE_SIZE = 20  # 最小人脸尺寸（像素）
MAX_FACE_SIZE_RATIO = 0.9  # 最大人脸尺寸比例
FACE_ASPECT_RATIO_MIN = 0.5  # 人脸宽高比最小值
FACE_ASPECT_RATIO_MAX = 2.0  # 人脸宽高比最大值
SMOOTHING_WEIGHT = 0.3  # 坐标平滑权重
SIMILARITY_THRESHOLD = 0.7  # 人脸相似度阈值
MAX_NO_FACE_COUNT = 3  # 连续无人脸检测次数阈值

# 检测间隔配置（秒）
DETECTION_INTERVALS = [0.1, 0.25, 0.5, 1, 2, 3, 5]
DEFAULT_INTERVAL = 1.0

# 声音配置
ALERT_SOUND_FILE = "alert.wav"  # 可选的自定义声音文件
USE_SYSTEM_SOUND = True  # 是否使用系统声音

# 界面颜色配置（二次元风格）
COLORS = {
    "primary": "#FF6B9D",      # 粉色主色调
    "secondary": "#4ECDC4",    # 青色辅助色
    "accent": "#45B7D1",       # 蓝色强调色
    "background": "#2C3E50",   # 深色背景
    "surface": "#34495E",      # 表面色
    "text": "#FFFFFF",         # 文字色
    "text_secondary": "#BDC3C7", # 次要文字色
    "success": "#2ECC71",      # 成功色
    "warning": "#F39C12",      # 警告色
    "error": "#E74C3C",        # 错误色
    "face_box": "#FF0000"      # 人脸框颜色
}

# MediaPipe 配置
USE_MEDIAPIPE = False  # 是否启用 MediaPipe 辅助检测（默认关闭，避免安装问题）
MEDIAPIPE_CONFIDENCE = 0.5  # MediaPipe 检测置信度阈值
