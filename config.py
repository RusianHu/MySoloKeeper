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
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700
WINDOW_TITLE = "MySoloKeeper - 打灰机✈️守护程序🛡️"

# 人类活动检测提示词（Prompt）配置
HUMAN_ACTIVITY_DETECTION_PROMPT_TEMPLATE = """IMPORTANT: You are analyzing an image with dimensions {width}x{height} pixels. The coordinate system has origin (0,0) at the TOP-LEFT corner, X-axis goes RIGHT, Y-axis goes DOWN.

You must ONLY detect human activity in this image and return ONLY the bounding box coordinates of detected humans in EXACTLY this JSON format: {{"humans": [{{"x": number, "y": number, "width": number, "height": number}}]}}

COORDINATE REQUIREMENTS:
- x: left edge of bounding box (0 to {width})
- y: top edge of bounding box (0 to {height})
- width: box width in pixels
- height: box height in pixels
- All coordinates must be integers within image bounds

If no human activity is detected, return {{"humans": []}}. DO NOT describe the image. DO NOT add any other text. ONLY return the JSON. NEVER make up coordinates if you don't see any human activity."""

# 坐标处理配置
MIN_HUMAN_SIZE = 30  # 最小人类检测尺寸（像素）
MAX_HUMAN_SIZE_RATIO = 0.95  # 最大人类检测尺寸比例
HUMAN_ASPECT_RATIO_MIN = 0.3  # 人类宽高比最小值
HUMAN_ASPECT_RATIO_MAX = 3.0  # 人类宽高比最大值
SMOOTHING_WEIGHT = 0.3  # 坐标平滑权重
SIMILARITY_THRESHOLD = 0.7  # 人类相似度阈值
MAX_NO_HUMAN_COUNT = 3  # 连续无人类检测次数阈值

# 检测间隔配置（秒）
DETECTION_INTERVALS = [0.1, 0.25, 0.5, 1, 2, 3, 5]
DEFAULT_INTERVAL = 1.0

# 声音配置
ALERT_SOUND_FILE = "alert.wav"  # 可选的自定义声音文件
USE_SYSTEM_SOUND = True  # 是否使用系统声音

# 主题配置
AVAILABLE_THEMES = ["跟随系统", "浅色", "深色"]
DEFAULT_THEME = "跟随系统"

# 界面颜色配置 - 深色主题
COLORS_DARK = {
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
    "human_box": "#FF0000"     # 人类检测框颜色
}

# 界面颜色配置 - 浅色主题
COLORS_LIGHT = {
    "primary": "#E91E63",      # 粉色主色调（深化）
    "secondary": "#00BCD4",    # 青色辅助色（深化）
    "accent": "#2196F3",       # 蓝色强调色（深化）
    "background": "#FAFAFA",   # 浅色背景
    "surface": "#FFFFFF",      # 表面色
    "text": "#212121",         # 文字色
    "text_secondary": "#757575", # 次要文字色
    "success": "#4CAF50",      # 成功色
    "warning": "#FF9800",      # 警告色
    "error": "#F44336",        # 错误色
    "human_box": "#FF0000"     # 人类检测框颜色
}

# 默认使用深色主题颜色
COLORS = COLORS_DARK

# 检测模式配置
DETECTION_MODES = {
    "MEDIAPIPE_ONLY": "MediaPipe独立检测",
    "SMOLVLM_ONLY": "SmolVLM独立检测",
    "HYBRID": "混合模式"
}
DEFAULT_DETECTION_MODE = "MEDIAPIPE_ONLY"  # 默认使用MediaPipe独立检测

# MediaPipe 配置
USE_MEDIAPIPE = True  # 是否启用 MediaPipe 辅助检测（如果库可用则启用）
MEDIAPIPE_CONFIDENCE = 0.5  # MediaPipe 检测置信度阈值

# MediaPipe 独立模式触发标准
MEDIAPIPE_ONLY_FACE_CONFIDENCE_THRESHOLD = 0.6  # 人脸检测置信度阈值
MEDIAPIPE_ONLY_POSE_VISIBILITY_THRESHOLD = 0.5   # 姿态关键点可见度阈值
MEDIAPIPE_ONLY_MIN_POSE_LANDMARKS = 5            # 最少需要的可见姿态关键点数量
MEDIAPIPE_ONLY_REQUIRE_BOTH = False              # 是否需要同时检测到人脸和姿态才触发守护

# MediaPipe 辅助检测参数
MEDIAPIPE_FACE_OVERLAP_THRESHOLD = 0.3  # 人脸重叠度阈值（0.0-1.0）
MEDIAPIPE_POSE_PRESENCE_THRESHOLD = 0.3  # 姿态存在度阈值（0.0-1.0）
MEDIAPIPE_CONFIDENCE_BOOST = 0.2  # 验证通过时的置信度提升
MEDIAPIPE_CONFIDENCE_PENALTY = 0.1  # 验证失败时的置信度降低
MEDIAPIPE_FINAL_CONFIDENCE_THRESHOLD = 0.3  # 最终保留检测结果的置信度阈值

# 摄像头模糊度配置
CAMERA_BLUR_MIN = 0.0  # 最小模糊度（无模糊）
CAMERA_BLUR_MAX = 20.0  # 最大模糊度
CAMERA_BLUR_DEFAULT = 0.0  # 默认模糊度（无模糊）
CAMERA_BLUR_STEPS = 200  # 模糊度滑块步数
