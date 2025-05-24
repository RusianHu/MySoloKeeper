# -*- coding: utf-8 -*-
"""
进程管理模块
"""

import psutil
import subprocess
import time
from typing import List, Dict, Optional
import ctypes
from ctypes import wintypes

try:
    import win32gui
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    print("警告: pywin32 未安装，进程窗口管理功能将受限")
    WIN32_AVAILABLE = False


class ProcessManager:
    """进程管理器"""

    def __init__(self):
        self.monitored_processes = {}  # {pid: process_info}

    def get_running_processes(self) -> List[Dict]:
        """获取所有运行中的进程列表"""
        processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
                try:
                    proc_info = proc.info

                    # 过滤掉系统进程和没有窗口的进程
                    if (proc_info['name'] and
                        not proc_info['name'].startswith('System') and
                        proc_info['exe'] and
                        self.has_visible_window(proc_info['pid'])):

                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'exe': proc_info['exe'],
                            'create_time': proc_info['create_time']
                        })

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            print(f"获取进程列表错误: {e}")

        return sorted(processes, key=lambda x: x['name'].lower())

    def has_visible_window(self, pid: int) -> bool:
        """检查进程是否有可见窗口"""
        if not WIN32_AVAILABLE:
            return True  # 如果没有win32api，假设所有进程都有窗口

        try:
            windows = []

            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        window_title = win32gui.GetWindowText(hwnd)
                        if window_title.strip():  # 只考虑有标题的窗口
                            windows.append(hwnd)
                return True

            win32gui.EnumWindows(enum_windows_callback, windows)
            return len(windows) > 0

        except Exception:
            return False

    def get_process_windows(self, pid: int) -> List[Dict]:
        """获取指定进程的所有窗口"""
        if not WIN32_AVAILABLE:
            return []

        windows = []

        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        window_title = win32gui.GetWindowText(hwnd)
                        if window_title.strip():
                            # 获取窗口状态
                            is_minimized = win32gui.IsIconic(hwnd)
                            is_maximized = self._is_window_maximized(hwnd)

                            windows.append({
                                'hwnd': hwnd,
                                'title': window_title,
                                'is_minimized': is_minimized,
                                'is_maximized': is_maximized
                            })
                return True

            win32gui.EnumWindows(enum_windows_callback, windows)

        except Exception as e:
            print(f"获取进程窗口错误: {e}")

        return windows

    def _is_window_maximized(self, hwnd) -> bool:
        """检查窗口是否最大化"""
        try:
            # 使用 GetWindowPlacement 来检查窗口状态
            placement = win32gui.GetWindowPlacement(hwnd)
            # placement[1] 是 showCmd，SW_SHOWMAXIMIZED = 3
            return placement[1] == win32con.SW_SHOWMAXIMIZED
        except Exception as e:
            print(f"检查窗口最大化状态错误: {e}")
            return False

    def minimize_process_windows(self, pid: int) -> bool:
        """最小化指定进程的所有窗口"""
        if not WIN32_AVAILABLE:
            print("警告: 无法最小化窗口，缺少win32api支持")
            return False

        try:
            windows = self.get_process_windows(pid)
            if not windows:
                print(f"未找到PID {pid} 的可见窗口")
                return False

            minimized_count = 0
            print(f"找到 {len(windows)} 个窗口，准备最小化...")

            for window in windows:
                print(f"窗口状态: {window['title']} - 最小化: {window['is_minimized']}, 最大化: {window['is_maximized']}")

                if not window['is_minimized']:
                    try:
                        # 先尝试将窗口设为前台，然后最小化
                        win32gui.SetForegroundWindow(window['hwnd'])
                        time.sleep(0.1)  # 短暂等待
                        win32gui.ShowWindow(window['hwnd'], win32con.SW_MINIMIZE)
                        minimized_count += 1
                        print(f"✓ 已最小化窗口: {window['title']}")
                    except Exception as e:
                        print(f"✗ 最小化窗口失败 {window['title']}: {e}")
                else:
                    print(f"- 窗口已是最小化状态: {window['title']}")

            print(f"成功最小化 {minimized_count} 个窗口")
            return minimized_count > 0

        except Exception as e:
            print(f"最小化进程窗口错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def restore_process_windows(self, pid: int) -> bool:
        """恢复指定进程的所有窗口"""
        if not WIN32_AVAILABLE:
            print("警告: 无法恢复窗口，缺少win32api支持")
            return False

        try:
            windows = self.get_process_windows(pid)
            restored_count = 0

            for window in windows:
                if window['is_minimized']:
                    try:
                        win32gui.ShowWindow(window['hwnd'], win32con.SW_RESTORE)
                        restored_count += 1
                        print(f"已恢复窗口: {window['title']}")
                    except Exception as e:
                        print(f"恢复窗口失败 {window['title']}: {e}")

            return restored_count > 0

        except Exception as e:
            print(f"恢复进程窗口错误: {e}")
            return False

    def is_process_running(self, pid: int) -> bool:
        """检查进程是否仍在运行"""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False

    def get_process_info(self, pid: int) -> Optional[Dict]:
        """获取指定进程的详细信息"""
        try:
            proc = psutil.Process(pid)
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'exe': proc.exe(),
                'status': proc.status(),
                'create_time': proc.create_time(),
                'cpu_percent': proc.cpu_percent(),
                'memory_info': proc.memory_info(),
                'num_threads': proc.num_threads(),
                'windows': self.get_process_windows(pid)
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"获取进程信息失败 {pid}: {e}")
            return None

    def add_monitored_process(self, pid: int, name: str) -> bool:
        """添加要监控的进程"""
        if not self.is_process_running(pid):
            return False

        self.monitored_processes[pid] = {
            'pid': pid,
            'name': name,
            'added_time': time.time(),
            'minimize_count': 0,
            'last_minimize_time': None
        }

        print(f"已添加监控进程: {name} (PID: {pid})")
        return True

    def remove_monitored_process(self, pid: int) -> bool:
        """移除监控的进程"""
        if pid in self.monitored_processes:
            process_info = self.monitored_processes.pop(pid)
            print(f"已移除监控进程: {process_info['name']} (PID: {pid})")
            return True
        return False

    def get_monitored_processes(self) -> Dict:
        """获取所有监控中的进程"""
        # 清理已经不存在的进程
        dead_pids = []
        for pid in self.monitored_processes:
            if not self.is_process_running(pid):
                dead_pids.append(pid)

        for pid in dead_pids:
            self.remove_monitored_process(pid)

        return self.monitored_processes.copy()

    def minimize_monitored_processes(self) -> int:
        """最小化所有监控的进程"""
        minimized_count = 0
        current_time = time.time()

        for pid, process_info in self.monitored_processes.items():
            if self.is_process_running(pid):
                if self.minimize_process_windows(pid):
                    process_info['minimize_count'] += 1
                    process_info['last_minimize_time'] = current_time
                    minimized_count += 1

        return minimized_count

    def get_process_by_name(self, name: str) -> List[Dict]:
        """根据进程名查找进程"""
        processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and name.lower() in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'exe': proc.info['exe']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            print(f"按名称查找进程错误: {e}")

        return processes
