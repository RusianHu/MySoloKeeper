# -*- coding: utf-8 -*-
"""
声音管理模块
"""

import pygame
import threading
import time
import os
from typing import Optional
import winsound
from config import *


class AudioManager:
    """声音管理器"""
    
    def __init__(self):
        self.pygame_initialized = False
        self.alert_sound = None
        self.is_playing = False
        self.play_thread = None
        
        # 尝试初始化pygame
        self.initialize_pygame()
        
        # 加载声音文件
        self.load_alert_sound()
    
    def initialize_pygame(self) -> bool:
        """初始化pygame音频系统"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.pygame_initialized = True
            print("Pygame音频系统初始化成功")
            return True
        except Exception as e:
            print(f"Pygame音频系统初始化失败: {e}")
            self.pygame_initialized = False
            return False
    
    def load_alert_sound(self):
        """加载报警声音文件"""
        if not self.pygame_initialized:
            return
        
        try:
            # 检查是否有自定义声音文件
            if os.path.exists(ALERT_SOUND_FILE):
                self.alert_sound = pygame.mixer.Sound(ALERT_SOUND_FILE)
                print(f"已加载自定义声音文件: {ALERT_SOUND_FILE}")
            else:
                # 创建一个简单的蜂鸣声
                self.alert_sound = self.create_beep_sound()
                print("已创建默认蜂鸣声")
                
        except Exception as e:
            print(f"加载声音文件失败: {e}")
            self.alert_sound = None
    
    def create_beep_sound(self, frequency: int = 800, duration: float = 0.5, 
                         sample_rate: int = 22050) -> Optional[pygame.mixer.Sound]:
        """创建一个简单的蜂鸣声"""
        try:
            import numpy as np
            
            # 生成正弦波
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                wave = np.sin(2 * np.pi * frequency * i / sample_rate)
                # 添加淡入淡出效果
                if i < frames * 0.1:
                    wave *= i / (frames * 0.1)
                elif i > frames * 0.9:
                    wave *= (frames - i) / (frames * 0.1)
                
                arr[i][0] = wave * 32767  # 左声道
                arr[i][1] = wave * 32767  # 右声道
            
            arr = arr.astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            return sound
            
        except Exception as e:
            print(f"创建蜂鸣声失败: {e}")
            return None
    
    def play_alert_async(self, repeat: int = 1, interval: float = 0.1):
        """异步播放报警声音"""
        if self.is_playing:
            return
        
        self.play_thread = threading.Thread(
            target=self._play_alert_thread, 
            args=(repeat, interval), 
            daemon=True
        )
        self.play_thread.start()
    
    def _play_alert_thread(self, repeat: int, interval: float):
        """播放报警声音的线程函数"""
        self.is_playing = True
        
        try:
            for i in range(repeat):
                if not self.is_playing:  # 检查是否被停止
                    break
                
                # 尝试使用pygame播放
                if self.pygame_initialized and self.alert_sound:
                    try:
                        self.alert_sound.play()
                        # 等待声音播放完成
                        while pygame.mixer.get_busy() and self.is_playing:
                            time.sleep(0.01)
                    except Exception as e:
                        print(f"Pygame播放声音失败: {e}")
                        # 回退到系统声音
                        self.play_system_beep()
                
                elif USE_SYSTEM_SOUND:
                    # 使用系统声音
                    self.play_system_beep()
                
                # 如果不是最后一次重复，等待间隔
                if i < repeat - 1 and self.is_playing:
                    time.sleep(interval)
                    
        except Exception as e:
            print(f"播放报警声音错误: {e}")
        finally:
            self.is_playing = False
    
    def play_system_beep(self):
        """播放系统蜂鸣声"""
        try:
            # Windows系统声音
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as e:
            print(f"播放系统声音失败: {e}")
    
    def play_alert_sync(self):
        """同步播放报警声音（阻塞）"""
        if self.pygame_initialized and self.alert_sound:
            try:
                self.alert_sound.play()
                while pygame.mixer.get_busy():
                    time.sleep(0.01)
            except Exception as e:
                print(f"同步播放声音失败: {e}")
                self.play_system_beep()
        else:
            self.play_system_beep()
    
    def stop_alert(self):
        """停止播放报警声音"""
        self.is_playing = False
        
        if self.pygame_initialized:
            try:
                pygame.mixer.stop()
            except Exception as e:
                print(f"停止pygame声音失败: {e}")
    
    def set_volume(self, volume: float):
        """设置音量（0.0-1.0）"""
        if self.pygame_initialized and self.alert_sound:
            try:
                self.alert_sound.set_volume(max(0.0, min(1.0, volume)))
            except Exception as e:
                print(f"设置音量失败: {e}")
    
    def test_audio(self) -> bool:
        """测试音频系统"""
        try:
            print("测试音频系统...")
            self.play_alert_sync()
            print("音频测试完成")
            return True
        except Exception as e:
            print(f"音频测试失败: {e}")
            return False
    
    def get_audio_info(self) -> dict:
        """获取音频系统信息"""
        info = {
            'pygame_initialized': self.pygame_initialized,
            'has_alert_sound': self.alert_sound is not None,
            'is_playing': self.is_playing,
            'use_system_sound': USE_SYSTEM_SOUND
        }
        
        if self.pygame_initialized:
            try:
                info.update({
                    'mixer_frequency': pygame.mixer.get_init()[0] if pygame.mixer.get_init() else None,
                    'mixer_format': pygame.mixer.get_init()[1] if pygame.mixer.get_init() else None,
                    'mixer_channels': pygame.mixer.get_init()[2] if pygame.mixer.get_init() else None,
                    'num_channels': pygame.mixer.get_num_channels()
                })
            except Exception as e:
                print(f"获取pygame信息失败: {e}")
        
        return info
    
    def __del__(self):
        """析构函数，清理资源"""
        self.stop_alert()
        if self.pygame_initialized:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
