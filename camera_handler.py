# -*- coding: utf-8 -*-
"""
摄像头处理模块
"""

import cv2
import numpy as np
import threading
import time
from typing import Optional, Callable, Tuple
from config import *

# 尝试导入MediaPipe，如果失败则禁用相关功能
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    print("警告: MediaPipe未安装，相关功能将被禁用")
    MEDIAPIPE_AVAILABLE = False
    mp = None


class CameraHandler:
    """摄像头处理器"""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None

        # MediaPipe 人脸检测
        if USE_MEDIAPIPE and MEDIAPIPE_AVAILABLE:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=MEDIAPIPE_CONFIDENCE
            )
        else:
            self.face_detection = None

    def initialize_camera(self) -> bool:
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"无法打开摄像头 {self.camera_index}")
                return False

            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

            # 测试读取一帧
            ret, frame = self.cap.read()
            if not ret:
                print("无法从摄像头读取帧")
                self.cap.release()
                return False

            print(f"摄像头初始化成功，分辨率: {frame.shape[1]}x{frame.shape[0]}")
            return True

        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            return False

    def start_capture(self) -> bool:
        """开始捕获视频流"""
        if self.is_running:
            return True

        if not self.cap or not self.cap.isOpened():
            if not self.initialize_camera():
                return False

        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

        print("摄像头捕获已开始")
        return True

    def stop_capture(self):
        """停止捕获视频流"""
        self.is_running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None

        print("摄像头捕获已停止")

    def _capture_loop(self):
        """摄像头捕获循环"""
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                else:
                    print("读取摄像头帧失败")
                    time.sleep(0.1)

            except Exception as e:
                print(f"摄像头捕获循环错误: {e}")
                time.sleep(0.1)

    def get_current_frame(self) -> Optional[np.ndarray]:
        """获取当前帧"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def capture_frame_as_jpeg(self, quality: int = 80) -> Optional[bytes]:
        """捕获当前帧并编码为JPEG格式"""
        frame = self.get_current_frame()
        if frame is None:
            return None

        try:
            # 编码为JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)

            if result:
                return encoded_img.tobytes()
            else:
                print("帧编码失败")
                return None

        except Exception as e:
            print(f"帧编码错误: {e}")
            return None

    def detect_faces_with_mediapipe(self, frame: np.ndarray) -> list:
        """使用MediaPipe检测人脸"""
        if not self.face_detection:
            return []

        try:
            # 转换BGR到RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)

            faces = []
            if results.detections:
                h, w, _ = frame.shape
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box

                    # 转换相对坐标到绝对坐标
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)

                    # 确保坐标在有效范围内
                    x = max(0, x)
                    y = max(0, y)
                    width = min(width, w - x)
                    height = min(height, h - y)

                    if width > 0 and height > 0:
                        faces.append({
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height,
                            'confidence': detection.score[0]
                        })

            return faces

        except Exception as e:
            print(f"MediaPipe人脸检测错误: {e}")
            return []

    def draw_face_boxes(self, frame: np.ndarray, faces: list,
                       color: Tuple[int, int, int] = (0, 0, 255),
                       thickness: int = 2) -> np.ndarray:
        """在帧上绘制人脸框"""
        if not faces:
            return frame

        result_frame = frame.copy()

        for face in faces:
            try:
                x = int(face['x'])
                y = int(face['y'])
                width = int(face['width'])
                height = int(face['height'])

                # 绘制矩形框
                cv2.rectangle(result_frame, (x, y), (x + width, y + height), color, thickness)

                # 如果有置信度信息，显示它
                if 'confidence' in face:
                    confidence_text = f"{face['confidence']:.2f}"
                    cv2.putText(result_frame, confidence_text, (x, y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            except (KeyError, ValueError, TypeError) as e:
                print(f"绘制人脸框错误: {e}")
                continue

        return result_frame

    def get_camera_info(self) -> dict:
        """获取摄像头信息"""
        if not self.cap or not self.cap.isOpened():
            return {}

        try:
            info = {
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'backend': self.cap.getBackendName(),
                'is_running': self.is_running
            }
            return info
        except Exception as e:
            print(f"获取摄像头信息错误: {e}")
            return {}

    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop_capture()
