# -*- coding: utf-8 -*-
"""
图形界面模块
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from typing import Optional, List, Dict
import base64

from config import *
from camera_handler import CameraHandler
from smolvlm_client import SmolVLMClient
from process_manager import ProcessManager
from coordinate_processor import CoordinateProcessor
from audio_manager import AudioManager


class MySoloKeeperGUI:
    """MySoloKeeper 主界面"""

    def __init__(self):
        # 设置customtkinter主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 初始化主窗口
        self.root = ctk.CTk()
        self.root.title(WINDOW_TITLE)

        # 计算窗口居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2

        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.resizable(True, True)

        # 初始化组件
        self.camera_handler = CameraHandler()
        self.smolvlm_client = SmolVLMClient()
        self.process_manager = ProcessManager()
        self.coordinate_processor = CoordinateProcessor(CAMERA_WIDTH, CAMERA_HEIGHT)
        self.audio_manager = AudioManager()

        # 设置调试回调
        self.smolvlm_client.set_debug_callback(self._on_api_debug)

        # 状态变量
        self.is_detecting = False
        self.is_guarding = False
        self.detection_thread = None
        self.current_frame = None
        self.detected_humans = []  # 检测到的人类活动
        self.detected_faces = []   # 保持向后兼容
        self.selected_process_pid = None
        self.last_guard_action_time = 0  # 上次触发守护动作的时间
        self.guard_action_cooldown = 3.0  # 守护动作冷却时间（秒）

        # GUI变量
        self.detection_interval = tk.DoubleVar(value=DEFAULT_INTERVAL)
        self.enable_audio_alert = tk.BooleanVar(value=True)
        self.enable_mediapipe = tk.BooleanVar(value=USE_MEDIAPIPE)
        self.guard_enabled = tk.BooleanVar(value=False)
        self.debug_expanded = tk.BooleanVar(value=False)
        self.detection_mode = tk.StringVar(value=DEFAULT_DETECTION_MODE)

        # 调试信息存储
        self.debug_history = []
        self.max_debug_entries = 10
        self.current_debug_index = -1  # 当前显示的调试条目索引

        # 创建界面
        self.create_widgets()
        self.setup_layout()

        # 绑定事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 初始化摄像头
        self.initialize_camera()

        # 初始化模式状态
        self.update_mode_status()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.main_frame = ctk.CTkFrame(self.root)

        # 左侧面板 - 摄像头和控制
        self.left_panel = ctk.CTkFrame(self.main_frame)

        # 摄像头显示区域
        self.camera_frame = ctk.CTkFrame(self.left_panel)
        self.camera_label = ctk.CTkLabel(
            self.camera_frame,
            text="摄像头未启动",
            width=CAMERA_WIDTH,
            height=CAMERA_HEIGHT
        )

        # 摄像头控制按钮
        self.camera_controls = ctk.CTkFrame(self.left_panel)
        self.start_detection_btn = ctk.CTkButton(
            self.camera_controls,
            text="开始检测",
            command=self.toggle_detection,
            fg_color=COLORS["success"],
            hover_color=COLORS["primary"]
        )

        # 检测间隔设置
        self.interval_frame = ctk.CTkFrame(self.camera_controls)
        self.interval_label = ctk.CTkLabel(self.interval_frame, text="检测间隔(秒):")
        self.interval_slider = ctk.CTkSlider(
            self.interval_frame,
            from_=0.1,
            to=5.0,
            number_of_steps=49,
            variable=self.detection_interval,
            command=self.on_interval_change
        )
        self.interval_value_label = ctk.CTkLabel(
            self.interval_frame,
            text=f"{DEFAULT_INTERVAL:.1f}s"
        )

        # 右侧面板 - 进程管理和设置
        self.right_panel = ctk.CTkFrame(self.main_frame)

        # 进程选择区域
        self.process_frame = ctk.CTkFrame(self.right_panel)
        self.process_label = ctk.CTkLabel(self.process_frame, text="选择要守护的进程:")

        # 进程列表容器
        self.listbox_frame = ctk.CTkFrame(self.process_frame)

        # 进程列表
        self.process_listbox = tk.Listbox(
            self.listbox_frame,
            height=10,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            selectbackground=COLORS["primary"],
            font=("Microsoft YaHei", 9)
        )
        self.process_scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical")
        self.process_listbox.config(yscrollcommand=self.process_scrollbar.set)
        self.process_scrollbar.config(command=self.process_listbox.yview)

        # 进程控制按钮
        self.process_controls = ctk.CTkFrame(self.process_frame)
        self.refresh_processes_btn = ctk.CTkButton(
            self.process_controls,
            text="刷新进程列表",
            command=self.refresh_process_list
        )
        self.select_process_btn = ctk.CTkButton(
            self.process_controls,
            text="选择进程",
            command=self.select_process
        )

        # 守护控制区域
        self.guard_frame = ctk.CTkFrame(self.right_panel)
        self.guard_label = ctk.CTkLabel(self.guard_frame, text="守护设置:")

        self.selected_process_label = ctk.CTkLabel(
            self.guard_frame,
            text="未选择进程",
            wraplength=300
        )

        self.guard_toggle = ctk.CTkSwitch(
            self.guard_frame,
            text="启用守护",
            variable=self.guard_enabled,
            command=self.toggle_guard
        )

        # 设置区域
        self.settings_frame = ctk.CTkFrame(self.right_panel)
        self.settings_label = ctk.CTkLabel(self.settings_frame, text="检测设置:")

        # 检测模式选择
        self.detection_mode_frame = ctk.CTkFrame(self.settings_frame)
        self.detection_mode_label = ctk.CTkLabel(
            self.detection_mode_frame,
            text="检测模式:",
            font=("Microsoft YaHei", 12, "bold")
        )

        self.detection_mode_menu = ctk.CTkOptionMenu(
            self.detection_mode_frame,
            variable=self.detection_mode,
            values=list(DETECTION_MODES.values()),
            command=self.on_detection_mode_change,
            width=200
        )

        # 模式状态指示器
        self.mode_status_frame = ctk.CTkFrame(self.settings_frame)
        self.mediapipe_status_label = ctk.CTkLabel(
            self.mode_status_frame,
            text="MediaPipe: 就绪",
            text_color=COLORS["success"],
            font=("Microsoft YaHei", 10)
        )
        self.smolvlm_status_label = ctk.CTkLabel(
            self.mode_status_frame,
            text="SmolVLM: 未连接",
            text_color=COLORS["error"],
            font=("Microsoft YaHei", 10)
        )

        # 其他设置
        self.other_settings_frame = ctk.CTkFrame(self.settings_frame)
        self.audio_alert_toggle = ctk.CTkSwitch(
            self.other_settings_frame,
            text="声音报警",
            variable=self.enable_audio_alert
        )

        # 测试按钮
        self.test_audio_btn = ctk.CTkButton(
            self.other_settings_frame,
            text="测试声音",
            command=self.test_audio,
            width=120
        )

        # 调试区域
        self.debug_frame = ctk.CTkFrame(self.right_panel)
        self.debug_header = ctk.CTkFrame(self.debug_frame)

        # 调试标题和展开/收起按钮
        self.debug_toggle_btn = ctk.CTkButton(
            self.debug_header,
            text="▼ 调试信息",
            command=self.toggle_debug_panel,
            width=100,
            height=30,
            fg_color="transparent",
            text_color=COLORS["text"],
            hover_color=COLORS["surface"]
        )

        # 调试历史导航
        self.debug_nav_frame = ctk.CTkFrame(self.debug_header)

        self.debug_prev_btn = ctk.CTkButton(
            self.debug_nav_frame,
            text="◀",
            command=self.prev_debug_entry,
            width=30,
            height=30,
            font=("Arial", 12)
        )

        self.debug_info_label = ctk.CTkLabel(
            self.debug_nav_frame,
            text="0/0",
            width=50,
            font=("Arial", 10)
        )

        self.debug_next_btn = ctk.CTkButton(
            self.debug_nav_frame,
            text="▶",
            command=self.next_debug_entry,
            width=30,
            height=30,
            font=("Arial", 12)
        )

        self.debug_clear_btn = ctk.CTkButton(
            self.debug_header,
            text="清除",
            command=self.clear_debug_info,
            width=60,
            height=30,
            fg_color=COLORS["error"],
            hover_color=COLORS["warning"]
        )

        # 调试内容区域
        self.debug_content = ctk.CTkFrame(self.debug_frame)

        # Prompt显示区域
        self.prompt_frame = ctk.CTkFrame(self.debug_content)
        self.prompt_label = ctk.CTkLabel(
            self.prompt_frame,
            text="📤 发送的Prompt:",
            font=("Microsoft YaHei", 12, "bold"),
            text_color=COLORS["primary"]
        )
        self.prompt_text = ctk.CTkTextbox(
            self.prompt_frame,
            height=80,
            width=390,
            font=("Consolas", 9),
            wrap="word"
        )

        # 响应显示区域
        self.response_frame = ctk.CTkFrame(self.debug_content)
        self.response_label = ctk.CTkLabel(
            self.response_frame,
            text="📥 接收的响应:",
            font=("Microsoft YaHei", 12, "bold"),
            text_color=COLORS["secondary"]
        )
        self.response_text = ctk.CTkTextbox(
            self.response_frame,
            height=100,
            width=390,
            font=("Consolas", 9),
            wrap="word"
        )

        # 初始隐藏调试内容
        self.debug_content_visible = False

        # 状态栏
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="就绪",
            anchor="w"
        )



    def setup_layout(self):
        """设置布局"""
        # 主框架
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧面板
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 摄像头区域
        self.camera_frame.pack(fill="x", pady=(0, 10))
        self.camera_label.pack(padx=10, pady=10)

        # 摄像头控制
        self.camera_controls.pack(fill="x", pady=(0, 10))
        self.start_detection_btn.pack(pady=10)

        # 间隔设置
        self.interval_frame.pack(fill="x", padx=10, pady=5)
        self.interval_label.pack(pady=(5, 0))
        self.interval_slider.pack(fill="x", padx=10, pady=5)
        self.interval_value_label.pack(pady=(0, 5))

        # 右侧面板
        self.right_panel.pack(side="right", fill="both", expand=False, padx=(5, 0))
        self.right_panel.configure(width=420)

        # 进程选择区域
        self.process_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.process_label.pack(pady=(10, 5))

        # 进程列表和滚动条
        self.listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.process_listbox.pack(side="left", fill="both", expand=True)
        self.process_scrollbar.pack(side="right", fill="y")

        # 进程控制按钮
        self.process_controls.pack(fill="x", padx=10, pady=5)
        self.refresh_processes_btn.pack(side="left", padx=(0, 5))
        self.select_process_btn.pack(side="right", padx=(5, 0))

        # 守护控制区域
        self.guard_frame.pack(fill="x", pady=(0, 10))
        self.guard_label.pack(pady=(10, 5))
        self.selected_process_label.pack(pady=5, padx=10)
        self.guard_toggle.pack(pady=5)

        # 设置区域
        self.settings_frame.pack(fill="x", pady=(0, 10))
        self.settings_label.pack(pady=(10, 5))

        # 检测模式选择
        self.detection_mode_frame.pack(fill="x", padx=10, pady=5)
        self.detection_mode_label.pack(pady=(5, 2))
        self.detection_mode_menu.pack(pady=(0, 5))

        # 模式状态指示器
        self.mode_status_frame.pack(fill="x", padx=10, pady=5)
        self.mediapipe_status_label.pack(pady=2)
        self.smolvlm_status_label.pack(pady=2)

        # 其他设置
        self.other_settings_frame.pack(fill="x", padx=10, pady=5)
        self.audio_alert_toggle.pack(pady=2)
        self.test_audio_btn.pack(pady=5)

        # 调试区域
        self.debug_frame.pack(fill="x", pady=(0, 10))

        # 调试头部
        self.debug_header.pack(fill="x", padx=5, pady=5)
        self.debug_toggle_btn.pack(side="left", padx=(5, 0))
        self.debug_clear_btn.pack(side="right", padx=(0, 5))

        # 导航按钮（居中）
        self.debug_nav_frame.pack(side="right", padx=(0, 10))
        self.debug_prev_btn.pack(side="left", padx=(0, 2))
        self.debug_info_label.pack(side="left", padx=2)
        self.debug_next_btn.pack(side="left", padx=(2, 0))

        # 调试内容（初始隐藏）
        # self.debug_content 将在 toggle_debug_panel 中动态显示/隐藏

        # 状态栏
        self.status_frame.pack(fill="x", side="bottom")
        self.status_label.pack(side="left", padx=10, pady=5)

    def initialize_camera(self):
        """初始化摄像头"""
        def init_camera_thread():
            if self.camera_handler.initialize_camera():
                self.update_status("摄像头初始化成功")
                self.root.after(0, self.test_smolvlm_connection)
            else:
                self.update_status("摄像头初始化失败")

        threading.Thread(target=init_camera_thread, daemon=True).start()

    def test_smolvlm_connection(self):
        """测试SmolVLM连接（初始化时调用）"""
        def test_connection_thread():
            if self.smolvlm_client.test_connection():
                self.root.after(0, lambda: self.update_status("SmolVLM连接成功"))
                self.root.after(0, self.update_mode_status)
            else:
                self.root.after(0, lambda: self.update_status("SmolVLM连接失败，请检查服务"))
                self.root.after(0, self.update_mode_status)

        threading.Thread(target=test_connection_thread, daemon=True).start()

    def test_smolvlm_connection_for_status(self):
        """测试SmolVLM连接并更新状态显示"""
        def test_connection_thread():
            if self.smolvlm_client.test_connection():
                self.root.after(0, lambda: self.smolvlm_status_label.configure(
                    text="SmolVLM: 已连接",
                    text_color=COLORS["success"]
                ))
            else:
                self.root.after(0, lambda: self.smolvlm_status_label.configure(
                    text="SmolVLM: 连接失败",
                    text_color=COLORS["error"]
                ))

        threading.Thread(target=test_connection_thread, daemon=True).start()

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.configure(text=message)
        print(f"状态: {message}")

    def on_interval_change(self, value):
        """检测间隔改变事件"""
        self.interval_value_label.configure(text=f"{value:.1f}s")

    def on_detection_mode_change(self, mode_name):
        """检测模式改变事件"""
        # 根据模式名称找到对应的模式键
        mode_key = None
        for key, name in DETECTION_MODES.items():
            if name == mode_name:
                mode_key = key
                break

        if mode_key:
            self.detection_mode.set(mode_key)
            self.update_status(f"检测模式已切换为: {mode_name}")

            # 根据模式更新状态显示
            self.update_mode_status()

            # 如果正在检测，重新启动以应用新模式
            if self.is_detecting:
                self.stop_detection()
                self.root.after(500, self.start_detection)  # 延迟500ms重新启动

    def update_mode_status(self):
        """更新模式状态显示"""
        current_mode = self.detection_mode.get()

        # 更新MediaPipe状态
        if current_mode in ["MEDIAPIPE_ONLY", "HYBRID"]:
            if hasattr(self.camera_handler, 'face_detection') and self.camera_handler.face_detection:
                self.mediapipe_status_label.configure(
                    text="MediaPipe: 就绪",
                    text_color=COLORS["success"]
                )
            else:
                self.mediapipe_status_label.configure(
                    text="MediaPipe: 不可用",
                    text_color=COLORS["error"]
                )
        else:
            self.mediapipe_status_label.configure(
                text="MediaPipe: 未使用",
                text_color=COLORS["text_secondary"]
            )

        # 更新SmolVLM状态
        if current_mode in ["SMOLVLM_ONLY", "HYBRID"]:
            # 测试SmolVLM连接
            self.test_smolvlm_connection_for_status()
        else:
            self.smolvlm_status_label.configure(
                text="SmolVLM: 未使用",
                text_color=COLORS["text_secondary"]
            )

    def toggle_detection(self):
        """切换检测状态"""
        if not self.is_detecting:
            self.start_detection()
        else:
            self.stop_detection()

    def start_detection(self):
        """开始检测"""
        if not self.camera_handler.start_capture():
            messagebox.showerror("错误", "无法启动摄像头")
            return

        self.is_detecting = True
        self.start_detection_btn.configure(
            text="停止检测",
            fg_color=COLORS["error"]
        )

        # 启动检测线程
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()

        # 启动摄像头显示更新
        self.update_camera_display()

        self.update_status("人类活动检测已开始")

    def stop_detection(self):
        """停止检测"""
        self.is_detecting = False
        self.camera_handler.stop_capture()

        self.start_detection_btn.configure(
            text="开始检测",
            fg_color=COLORS["success"]
        )

        self.camera_label.configure(image="", text="摄像头已停止")
        self.coordinate_processor.reset()

        self.update_status("人类活动检测已停止")

    def detection_loop(self):
        """检测循环"""
        while self.is_detecting:
            try:
                current_mode = self.detection_mode.get()
                humans = []

                # 获取当前帧
                current_frame = self.camera_handler.get_current_frame()
                if current_frame is None:
                    time.sleep(0.1)
                    continue

                # 根据检测模式执行不同的检测逻辑
                if current_mode == "MEDIAPIPE_ONLY":
                    # 仅使用MediaPipe检测
                    humans = self.detect_with_mediapipe_only(current_frame)

                elif current_mode == "SMOLVLM_ONLY":
                    # 仅使用SmolVLM检测
                    humans = self.detect_with_smolvlm_only(current_frame)

                elif current_mode == "HYBRID":
                    # 混合模式：SmolVLM + MediaPipe验证
                    humans = self.detect_with_hybrid_mode(current_frame)

                self.detected_humans = humans
                self.detected_faces = humans  # 保持向后兼容

                # 如果启用守护且检测到人类活动
                if self.is_guarding and humans and self.selected_process_pid:
                    self.trigger_guard_action()

                # 等待指定间隔
                time.sleep(self.detection_interval.get())

            except Exception as e:
                print(f"检测循环错误: {e}")
                time.sleep(1.0)

    def detect_with_mediapipe_only(self, frame):
        """仅使用MediaPipe进行检测"""
        try:
            # 人脸检测
            faces = self.camera_handler.detect_faces_with_mediapipe(frame)

            # 姿态检测
            pose_data = self.camera_handler.detect_pose_with_mediapipe(frame)

            humans = []

            # 将人脸检测结果转换为人类活动
            for face in faces:
                humans.append({
                    'x': face['x'],
                    'y': face['y'],
                    'width': face['width'],
                    'height': face['height'],
                    'confidence': face['confidence'],
                    'source': 'mediapipe_face'
                })

            # 如果有姿态检测结果，添加姿态区域
            if pose_data and pose_data.get('landmarks'):
                pose_box = self._get_pose_bounding_box(pose_data['landmarks'], frame.shape)
                if pose_box:
                    humans.append({
                        'x': pose_box['x'],
                        'y': pose_box['y'],
                        'width': pose_box['width'],
                        'height': pose_box['height'],
                        'confidence': 0.8,  # 姿态检测置信度
                        'source': 'mediapipe_pose'
                    })

            return humans

        except Exception as e:
            print(f"MediaPipe检测错误: {e}")
            return []

    def detect_with_smolvlm_only(self, frame):
        """仅使用SmolVLM进行检测"""
        try:
            # 捕获当前帧数据
            frame_data = self.camera_handler.capture_frame_as_jpeg()
            if frame_data is None:
                return []

            # 获取实际图像尺寸
            image_width, image_height = self.smolvlm_client.get_image_dimensions_from_data(frame_data)

            # 更新坐标处理器的画布尺寸
            self.coordinate_processor.canvas_width = image_width
            self.coordinate_processor.canvas_height = image_height

            # 编码为base64
            image_base64_url = self.smolvlm_client.encode_image_to_base64(frame_data)

            # 发送到SmolVLM进行人类活动检测
            response = self.smolvlm_client.detect_human_activity(
                image_base64_url,
                image_width,
                image_height
            )

            if response:
                # 处理SmolVLM检测结果
                humans = self.coordinate_processor.process_humans(response)
                for human in humans:
                    human['source'] = 'smolvlm'
                return humans

            return []

        except Exception as e:
            print(f"SmolVLM检测错误: {e}")
            return []

    def detect_with_hybrid_mode(self, frame):
        """混合模式：SmolVLM + MediaPipe验证"""
        try:
            # 首先使用SmolVLM检测
            smolvlm_humans = self.detect_with_smolvlm_only(frame)

            if not smolvlm_humans:
                return []

            # 使用MediaPipe进行验证和增强
            enhanced_humans = self.enhance_detection_with_mediapipe(frame, smolvlm_humans)

            for human in enhanced_humans:
                human['source'] = 'hybrid'

            return enhanced_humans

        except Exception as e:
            print(f"混合模式检测错误: {e}")
            return []

    def _get_pose_bounding_box(self, landmarks, frame_shape):
        """从姿态关键点计算边界框"""
        try:
            h, w = frame_shape[:2]

            # 获取所有可见关键点的坐标
            x_coords = []
            y_coords = []

            for landmark in landmarks.landmark:
                if landmark.visibility > 0.5:  # 只考虑可见度高的关键点
                    x_coords.append(int(landmark.x * w))
                    y_coords.append(int(landmark.y * h))

            if len(x_coords) < 3:  # 至少需要3个关键点
                return None

            # 计算边界框
            x_min = max(0, min(x_coords))
            y_min = max(0, min(y_coords))
            x_max = min(w, max(x_coords))
            y_max = min(h, max(y_coords))

            # 添加一些边距
            margin = 20
            x_min = max(0, x_min - margin)
            y_min = max(0, y_min - margin)
            x_max = min(w, x_max + margin)
            y_max = min(h, y_max + margin)

            return {
                'x': x_min,
                'y': y_min,
                'width': x_max - x_min,
                'height': y_max - y_min
            }

        except Exception as e:
            print(f"计算姿态边界框错误: {e}")
            return None

    def update_camera_display(self):
        """更新摄像头显示"""
        if not self.is_detecting:
            return

        try:
            frame = self.camera_handler.get_current_frame()
            if frame is not None:
                current_mode = self.detection_mode.get()

                # 根据检测模式绘制不同的检测框
                if current_mode == "MEDIAPIPE_ONLY":
                    # MediaPipe独立模式：绘制人脸和姿态
                    mediapipe_faces = self.camera_handler.detect_faces_with_mediapipe(frame)
                    if mediapipe_faces:
                        frame = self.camera_handler.draw_face_boxes(
                            frame,
                            mediapipe_faces,
                            color=(0, 255, 0),  # 绿色
                            thickness=2
                        )

                    # 姿态检测
                    pose_data = self.camera_handler.detect_pose_with_mediapipe(frame)
                    if pose_data and pose_data.get('landmarks'):
                        frame = self.camera_handler.draw_pose_landmarks(frame, pose_data)

                elif current_mode == "SMOLVLM_ONLY":
                    # SmolVLM独立模式：只绘制SmolVLM检测结果
                    if self.detected_humans:
                        frame = self.camera_handler.draw_face_boxes(
                            frame,
                            self.detected_humans,
                            color=(255, 0, 0),  # 蓝色（BGR格式）
                            thickness=2
                        )

                elif current_mode == "HYBRID":
                    # 混合模式：绘制SmolVLM主检测结果和MediaPipe辅助结果
                    if self.detected_humans:
                        frame = self.camera_handler.draw_face_boxes(
                            frame,
                            self.detected_humans,
                            color=(255, 0, 0),  # 蓝色（BGR格式）
                            thickness=2
                        )

                    # 显示MediaPipe辅助检测结果（较细的绿色框）
                    mediapipe_faces = self.camera_handler.detect_faces_with_mediapipe(frame)
                    if mediapipe_faces:
                        frame = self.camera_handler.draw_face_boxes(
                            frame,
                            mediapipe_faces,
                            color=(0, 255, 0),  # 绿色
                            thickness=1
                        )

                    # 姿态检测
                    pose_data = self.camera_handler.detect_pose_with_mediapipe(frame)
                    if pose_data and pose_data.get('landmarks'):
                        frame = self.camera_handler.draw_pose_landmarks(frame, pose_data)

                # 转换为PIL图像并显示
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)

                # 调整图像大小以适应显示区域
                display_width = CAMERA_WIDTH
                display_height = CAMERA_HEIGHT
                pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)

                # 转换为tkinter可显示的格式
                tk_image = ImageTk.PhotoImage(pil_image)
                self.camera_label.configure(image=tk_image, text="")
                self.camera_label.image = tk_image  # 保持引用

        except Exception as e:
            print(f"更新摄像头显示错误: {e}")

        # 继续更新
        if self.is_detecting:
            self.root.after(50, self.update_camera_display)  # 20 FPS

    def refresh_process_list(self):
        """刷新进程列表"""
        def refresh_thread():
            processes = self.process_manager.get_running_processes()

            # 在主线程中更新UI
            self.root.after(0, lambda: self._update_process_list(processes))

        threading.Thread(target=refresh_thread, daemon=True).start()
        self.update_status("正在刷新进程列表...")

    def _update_process_list(self, processes: List[Dict]):
        """更新进程列表UI"""
        self.process_listbox.delete(0, tk.END)

        for proc in processes:
            display_text = f"{proc['name']} (PID: {proc['pid']})"
            self.process_listbox.insert(tk.END, display_text)
            # 存储完整的进程信息
            self.process_listbox.insert(tk.END, "")  # 占位符，实际存储在tag中
            self.process_listbox.delete(tk.END)  # 删除占位符

        # 存储进程数据
        self.process_data = processes
        self.update_status(f"已加载 {len(processes)} 个进程")

    def select_process(self):
        """选择进程"""
        selection = self.process_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个进程")
            return

        index = selection[0]
        if hasattr(self, 'process_data') and index < len(self.process_data):
            selected_proc = self.process_data[index]
            self.selected_process_pid = selected_proc['pid']

            # 更新显示
            display_text = f"{selected_proc['name']}\nPID: {selected_proc['pid']}"
            self.selected_process_label.configure(text=display_text)

            # 添加到监控列表
            self.process_manager.add_monitored_process(
                selected_proc['pid'],
                selected_proc['name']
            )

            self.update_status(f"已选择进程: {selected_proc['name']}")

    def toggle_guard(self):
        """切换守护状态"""
        if self.guard_enabled.get():
            if not self.selected_process_pid:
                messagebox.showwarning("警告", "请先选择要守护的进程")
                self.guard_enabled.set(False)
                return

            if not self.is_detecting:
                messagebox.showwarning("警告", "请先开始人类活动检测")
                self.guard_enabled.set(False)
                return

            self.is_guarding = True
            self.update_status("守护模式已启用")
        else:
            self.is_guarding = False
            self.update_status("守护模式已禁用")

    def enhance_detection_with_mediapipe(self, frame, smolvlm_humans):
        """使用MediaPipe增强SmolVLM的检测结果"""
        try:
            # 获取MediaPipe检测结果
            mediapipe_faces = self.camera_handler.detect_faces_with_mediapipe(frame)
            pose_data = self.camera_handler.detect_pose_with_mediapipe(frame)

            enhanced_humans = []

            for human in smolvlm_humans:
                enhanced_human = human.copy()

                # 1. 人脸验证：检查SmolVLM检测的区域是否有MediaPipe检测到的人脸
                face_confidence = self._calculate_face_overlap(human, mediapipe_faces)

                # 2. 姿态验证：检查是否有人体姿态
                pose_confidence = self._calculate_pose_presence(human, pose_data, frame.shape)

                # 3. 综合置信度计算
                original_confidence = human.get('confidence', 0.5)

                # 如果MediaPipe也检测到相关特征，提高置信度
                if (face_confidence > MEDIAPIPE_FACE_OVERLAP_THRESHOLD or
                    pose_confidence > MEDIAPIPE_POSE_PRESENCE_THRESHOLD):
                    enhanced_confidence = min(1.0, original_confidence + MEDIAPIPE_CONFIDENCE_BOOST)
                    enhanced_human['confidence'] = enhanced_confidence
                    enhanced_human['mediapipe_verified'] = True
                    enhanced_human['face_confidence'] = face_confidence
                    enhanced_human['pose_confidence'] = pose_confidence
                    print(f"MediaPipe验证通过: 人脸{face_confidence:.2f}, 姿态{pose_confidence:.2f}")
                else:
                    # 如果MediaPipe没有检测到相关特征，降低置信度
                    enhanced_confidence = max(0.1, original_confidence - MEDIAPIPE_CONFIDENCE_PENALTY)
                    enhanced_human['confidence'] = enhanced_confidence
                    enhanced_human['mediapipe_verified'] = False
                    print(f"MediaPipe验证失败: 人脸{face_confidence:.2f}, 姿态{pose_confidence:.2f}")

                # 只保留置信度较高的检测结果
                if enhanced_confidence > MEDIAPIPE_FINAL_CONFIDENCE_THRESHOLD:
                    enhanced_humans.append(enhanced_human)

            return enhanced_humans

        except Exception as e:
            print(f"MediaPipe辅助检测错误: {e}")
            return smolvlm_humans  # 出错时返回原始结果

    def _calculate_face_overlap(self, human_box, mediapipe_faces):
        """计算人类检测框与MediaPipe人脸的重叠度"""
        if not mediapipe_faces:
            return 0.0

        try:
            human_x = human_box['x']
            human_y = human_box['y']
            human_w = human_box['width']
            human_h = human_box['height']

            max_overlap = 0.0

            for face in mediapipe_faces:
                face_x = face['x']
                face_y = face['y']
                face_w = face['width']
                face_h = face['height']

                # 计算重叠区域
                overlap_x = max(0, min(human_x + human_w, face_x + face_w) - max(human_x, face_x))
                overlap_y = max(0, min(human_y + human_h, face_y + face_h) - max(human_y, face_y))
                overlap_area = overlap_x * overlap_y

                # 计算重叠比例
                face_area = face_w * face_h
                if face_area > 0:
                    overlap_ratio = overlap_area / face_area
                    max_overlap = max(max_overlap, overlap_ratio)

            return max_overlap

        except Exception as e:
            print(f"计算人脸重叠度错误: {e}")
            return 0.0

    def _calculate_pose_presence(self, human_box, pose_data, frame_shape):
        """计算人类检测框内是否有姿态关键点"""
        if not pose_data or not pose_data.get('landmarks'):
            return 0.0

        try:
            human_x = human_box['x']
            human_y = human_box['y']
            human_w = human_box['width']
            human_h = human_box['height']

            frame_h, frame_w = frame_shape[:2]
            landmarks = pose_data['landmarks'].landmark

            points_in_box = 0
            total_visible_points = 0

            for landmark in landmarks:
                if landmark.visibility > 0.5:  # 只考虑可见的关键点
                    total_visible_points += 1

                    # 转换相对坐标到绝对坐标
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)

                    # 检查是否在人类检测框内
                    if (human_x <= x <= human_x + human_w and
                        human_y <= y <= human_y + human_h):
                        points_in_box += 1

            if total_visible_points > 0:
                return points_in_box / total_visible_points
            else:
                return 0.0

        except Exception as e:
            print(f"计算姿态存在度错误: {e}")
            return 0.0

    def trigger_guard_action(self):
        """触发守护动作"""
        try:
            current_time = time.time()

            # 检查冷却时间
            if current_time - self.last_guard_action_time < self.guard_action_cooldown:
                remaining_time = self.guard_action_cooldown - (current_time - self.last_guard_action_time)
                print(f"守护动作冷却中，剩余 {remaining_time:.1f} 秒")
                return

            print(f"触发守护动作 - 目标进程PID: {self.selected_process_pid}")

            # 最小化被守护的进程
            if self.process_manager.minimize_process_windows(self.selected_process_pid):
                self.last_guard_action_time = current_time
                self.update_status("检测到人类活动，已最小化目标进程")

                # 播放声音报警
                if self.enable_audio_alert.get():
                    self.audio_manager.play_alert_async(repeat=2, interval=0.2)
            else:
                print("未能最小化任何窗口")

        except Exception as e:
            print(f"触发守护动作错误: {e}")
            import traceback
            traceback.print_exc()

    def test_audio(self):
        """测试音频"""
        def test_thread():
            success = self.audio_manager.test_audio()
            message = "音频测试成功" if success else "音频测试失败"
            self.root.after(0, lambda: self.update_status(message))

        threading.Thread(target=test_thread, daemon=True).start()

    def _on_api_debug(self, prompt: str, response: str):
        """API调试信息回调"""
        # 使用root.after确保在主线程中执行
        self.root.after(0, lambda: self.add_debug_info(prompt, response))

    def toggle_debug_panel(self):
        """切换调试面板显示/隐藏"""
        if self.debug_content_visible:
            # 隐藏调试内容
            self.debug_content.pack_forget()
            self.debug_toggle_btn.configure(text="▼ 调试信息")
            self.debug_content_visible = False

            # 收起时缩小窗口高度
            self.root.after(50, lambda: self._adjust_window_size_for_debug(False))
        else:
            # 显示调试内容
            self.debug_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))

            # Prompt区域布局
            self.prompt_frame.pack(fill="x", padx=5, pady=(5, 2))
            self.prompt_label.pack(anchor="w", padx=5, pady=(5, 2))
            self.prompt_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))

            # 响应区域布局
            self.response_frame.pack(fill="both", expand=True, padx=5, pady=(2, 5))
            self.response_label.pack(anchor="w", padx=5, pady=(5, 2))
            self.response_text.pack(fill="both", expand=True, padx=5, pady=(0, 5))

            self.debug_toggle_btn.configure(text="▲ 调试信息")
            self.debug_content_visible = True

            # 展开时增加窗口高度（延迟执行，让布局先完成）
            self.root.after(50, lambda: self._adjust_window_size_for_debug(True))

    def _adjust_window_size_for_debug(self, expand: bool):
        """根据调试面板状态调整窗口大小"""
        try:
            # 获取当前窗口位置和大小
            current_geometry = self.root.geometry()
            # 解析几何字符串 "widthxheight+x+y"
            size_part, pos_part = current_geometry.split('+', 1)
            width, height = map(int, size_part.split('x'))
            x, y = map(int, pos_part.split('+'))

            # 调试面板的高度（包括边距）
            debug_panel_height = 280  # Prompt框80 + 响应框100 + 标签和边距100

            if expand:
                # 展开：增加高度
                new_height = height + debug_panel_height
                # 确保不超过屏幕高度
                screen_height = self.root.winfo_screenheight()
                max_height = screen_height - 100  # 留出任务栏空间
                if new_height > max_height:
                    new_height = max_height
                    # 如果窗口太高，向上移动一些
                    if y + new_height > screen_height - 50:
                        y = max(50, screen_height - new_height - 50)
            else:
                # 收起：减少高度
                new_height = max(WINDOW_MIN_HEIGHT, height - debug_panel_height)

            # 应用新的窗口大小
            self.root.geometry(f"{width}x{new_height}+{x}+{y}")

        except Exception as e:
            print(f"调整窗口大小错误: {e}")

    def clear_debug_info(self):
        """清除调试信息"""
        self.debug_history.clear()
        self.current_debug_index = -1
        self.prompt_text.delete("1.0", "end")
        self.response_text.delete("1.0", "end")
        self.update_debug_nav_info()
        self.update_status("调试信息已清除")

    def prev_debug_entry(self):
        """显示上一条调试信息"""
        if not self.debug_history:
            return

        if self.current_debug_index > 0:
            self.current_debug_index -= 1
            self.update_debug_display()

    def next_debug_entry(self):
        """显示下一条调试信息"""
        if not self.debug_history:
            return

        if self.current_debug_index < len(self.debug_history) - 1:
            self.current_debug_index += 1
            self.update_debug_display()

    def update_debug_nav_info(self):
        """更新调试导航信息"""
        if not self.debug_history:
            self.debug_info_label.configure(text="0/0")
            self.debug_prev_btn.configure(state="disabled")
            self.debug_next_btn.configure(state="disabled")
        else:
            total = len(self.debug_history)
            current = self.current_debug_index + 1
            self.debug_info_label.configure(text=f"{current}/{total}")

            # 更新按钮状态
            self.debug_prev_btn.configure(state="normal" if self.current_debug_index > 0 else "disabled")
            self.debug_next_btn.configure(state="normal" if self.current_debug_index < total - 1 else "disabled")

    def add_debug_info(self, prompt: str, response: str, timestamp: str = None):
        """添加调试信息"""
        import datetime

        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 添加到历史记录
        debug_entry = {
            "timestamp": timestamp,
            "prompt": prompt,
            "response": response
        }

        self.debug_history.append(debug_entry)

        # 保持最大条目数限制
        if len(self.debug_history) > self.max_debug_entries:
            self.debug_history.pop(0)

        # 设置当前索引为最新条目
        self.current_debug_index = len(self.debug_history) - 1

        # 更新显示
        self.update_debug_display()
        self.update_debug_nav_info()

    def update_debug_display(self):
        """更新调试信息显示"""
        if not self.debug_history or self.current_debug_index < 0:
            return

        # 获取当前索引的调试信息
        current_entry = self.debug_history[self.current_debug_index]

        # 更新Prompt显示
        self.prompt_text.delete("1.0", "end")
        prompt_display = f"[{current_entry['timestamp']}]\n{current_entry['prompt']}"
        self.prompt_text.insert("1.0", prompt_display)

        # 更新响应显示
        self.response_text.delete("1.0", "end")
        response_display = f"[{current_entry['timestamp']}]\n{current_entry['response']}"
        self.response_text.insert("1.0", response_display)

        # 滚动到顶部显示内容
        self.prompt_text.see("1.0")
        self.response_text.see("1.0")

    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 停止所有活动
            self.is_detecting = False
            self.is_guarding = False

            # 停止摄像头
            self.camera_handler.stop_capture()

            # 停止音频
            self.audio_manager.stop_alert()

            # 销毁窗口
            self.root.destroy()

        except Exception as e:
            print(f"关闭程序错误: {e}")

    def run(self):
        """运行主循环"""
        # 初始加载进程列表
        self.refresh_process_list()

        # 启动主循环
        self.root.mainloop()
