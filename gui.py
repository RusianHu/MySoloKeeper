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
        self.settings_label = ctk.CTkLabel(self.settings_frame, text="设置:")

        self.audio_alert_toggle = ctk.CTkSwitch(
            self.settings_frame,
            text="声音报警",
            variable=self.enable_audio_alert
        )

        self.mediapipe_toggle = ctk.CTkSwitch(
            self.settings_frame,
            text="MediaPipe辅助检测",
            variable=self.enable_mediapipe
        )

        # 测试按钮
        self.test_audio_btn = ctk.CTkButton(
            self.settings_frame,
            text="测试声音",
            command=self.test_audio
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

        # 连接状态指示器
        self.connection_frame = ctk.CTkFrame(self.status_frame)
        self.connection_label = ctk.CTkLabel(
            self.connection_frame,
            text="SmolVLM: 未连接",
            text_color=COLORS["error"]
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
        self.audio_alert_toggle.pack(pady=2)
        self.mediapipe_toggle.pack(pady=2)
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
        self.connection_frame.pack(side="right", padx=10, pady=5)
        self.connection_label.pack()

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
        """测试SmolVLM连接"""
        def test_connection_thread():
            if self.smolvlm_client.test_connection():
                self.root.after(0, lambda: self.connection_label.configure(
                    text="SmolVLM: 已连接",
                    text_color=COLORS["success"]
                ))
                self.root.after(0, lambda: self.update_status("SmolVLM连接成功"))
            else:
                self.root.after(0, lambda: self.connection_label.configure(
                    text="SmolVLM: 连接失败",
                    text_color=COLORS["error"]
                ))
                self.root.after(0, lambda: self.update_status("SmolVLM连接失败，请检查服务"))

        threading.Thread(target=test_connection_thread, daemon=True).start()

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.configure(text=message)
        print(f"状态: {message}")

    def on_interval_change(self, value):
        """检测间隔改变事件"""
        self.interval_value_label.configure(text=f"{value:.1f}s")

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
                # 捕获当前帧
                frame_data = self.camera_handler.capture_frame_as_jpeg()
                if frame_data is None:
                    time.sleep(0.1)
                    continue

                # 获取实际图像尺寸
                image_width, image_height = self.smolvlm_client.get_image_dimensions_from_data(frame_data)

                # 更新坐标处理器的画布尺寸
                self.coordinate_processor.canvas_width = image_width
                self.coordinate_processor.canvas_height = image_height

                # 编码为base64
                image_base64_url = self.smolvlm_client.encode_image_to_base64(frame_data)

                # 发送到SmolVLM进行人类活动检测，传递实际图像尺寸
                response = self.smolvlm_client.detect_human_activity(
                    image_base64_url,
                    image_width,
                    image_height
                )

                if response:
                    # 处理检测结果
                    humans = self.coordinate_processor.process_humans(response)
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

    def update_camera_display(self):
        """更新摄像头显示"""
        if not self.is_detecting:
            return

        try:
            frame = self.camera_handler.get_current_frame()
            if frame is not None:
                # 绘制人类活动检测框
                if self.detected_humans:
                    frame = self.camera_handler.draw_face_boxes(
                        frame,
                        self.detected_humans,
                        color=(255, 0, 0),  # 蓝色（BGR格式）
                        thickness=2
                    )

                # 可选：使用MediaPipe辅助检测
                if self.enable_mediapipe.get():
                    # 人脸检测
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
