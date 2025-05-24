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
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(True, True)

        # 初始化组件
        self.camera_handler = CameraHandler()
        self.smolvlm_client = SmolVLMClient()
        self.process_manager = ProcessManager()
        self.coordinate_processor = CoordinateProcessor(CAMERA_WIDTH, CAMERA_HEIGHT)
        self.audio_manager = AudioManager()

        # 状态变量
        self.is_detecting = False
        self.is_guarding = False
        self.detection_thread = None
        self.current_frame = None
        self.detected_faces = []
        self.selected_process_pid = None

        # GUI变量
        self.detection_interval = tk.DoubleVar(value=DEFAULT_INTERVAL)
        self.enable_audio_alert = tk.BooleanVar(value=True)
        self.enable_mediapipe = tk.BooleanVar(value=USE_MEDIAPIPE)
        self.guard_enabled = tk.BooleanVar(value=False)

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
            text="开始识别",
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

        # 进程列表
        self.process_listbox = tk.Listbox(
            self.process_frame,
            height=10,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            selectbackground=COLORS["primary"],
            font=("Microsoft YaHei", 9)
        )
        self.process_scrollbar = ttk.Scrollbar(self.process_frame, orient="vertical")
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
            text="MediaPipe辅助",
            variable=self.enable_mediapipe
        )

        # 测试按钮
        self.test_audio_btn = ctk.CTkButton(
            self.settings_frame,
            text="测试声音",
            command=self.test_audio
        )

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
        self.right_panel.configure(width=350)

        # 进程选择区域
        self.process_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.process_label.pack(pady=(10, 5))

        # 进程列表和滚动条
        listbox_frame = ctk.CTkFrame(self.process_frame)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)

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
            text="停止识别",
            fg_color=COLORS["error"]
        )

        # 启动检测线程
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()

        # 启动摄像头显示更新
        self.update_camera_display()

        self.update_status("人脸检测已开始")

    def stop_detection(self):
        """停止检测"""
        self.is_detecting = False
        self.camera_handler.stop_capture()

        self.start_detection_btn.configure(
            text="开始识别",
            fg_color=COLORS["success"]
        )

        self.camera_label.configure(image="", text="摄像头已停止")
        self.coordinate_processor.reset()

        self.update_status("人脸检测已停止")

    def detection_loop(self):
        """检测循环"""
        while self.is_detecting:
            try:
                # 捕获当前帧
                frame_data = self.camera_handler.capture_frame_as_jpeg()
                if frame_data is None:
                    time.sleep(0.1)
                    continue

                # 编码为base64
                image_base64_url = self.smolvlm_client.encode_image_to_base64(frame_data)

                # 发送到SmolVLM进行人脸检测
                response = self.smolvlm_client.detect_faces(image_base64_url)
                if response:
                    # 处理检测结果
                    faces = self.coordinate_processor.process_faces(response)
                    self.detected_faces = faces

                    # 如果启用守护且检测到人脸
                    if self.is_guarding and faces and self.selected_process_pid:
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
                # 绘制人脸框
                if self.detected_faces:
                    frame = self.camera_handler.draw_face_boxes(
                        frame,
                        self.detected_faces,
                        color=(0, 0, 255),  # 红色
                        thickness=2
                    )

                # 可选：使用MediaPipe辅助检测
                if self.enable_mediapipe.get():
                    mediapipe_faces = self.camera_handler.detect_faces_with_mediapipe(frame)
                    if mediapipe_faces:
                        frame = self.camera_handler.draw_face_boxes(
                            frame,
                            mediapipe_faces,
                            color=(0, 255, 0),  # 绿色
                            thickness=1
                        )

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
                messagebox.showwarning("警告", "请先开始人脸检测")
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
            # 最小化被守护的进程
            if self.process_manager.minimize_process_windows(self.selected_process_pid):
                self.update_status("检测到人脸，已最小化目标进程")

                # 播放声音报警
                if self.enable_audio_alert.get():
                    self.audio_manager.play_alert_async(repeat=2, interval=0.2)

        except Exception as e:
            print(f"触发守护动作错误: {e}")

    def test_audio(self):
        """测试音频"""
        def test_thread():
            success = self.audio_manager.test_audio()
            message = "音频测试成功" if success else "音频测试失败"
            self.root.after(0, lambda: self.update_status(message))

        threading.Thread(target=test_thread, daemon=True).start()

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
