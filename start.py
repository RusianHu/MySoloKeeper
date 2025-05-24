# -*- coding: utf-8 -*-
"""
MySoloKeeper 启动脚本
自动检查和安装依赖，然后启动程序
"""

import sys
import subprocess
import os
import importlib.util


def install_requirements():
    """安装requirements.txt中的所有依赖"""
    print("正在安装依赖包...")
    try:
        # 使用国内镜像源加速下载
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"
        ], capture_output=True, text=True, check=True)
        print("✓ 所有依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        print(f"错误输出: {e.stderr}")

        # 尝试不使用镜像源重新安装
        print("尝试使用官方源重新安装...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, check=True)
            print("✓ 使用官方源安装成功")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"✗ 官方源安装也失败: {e2}")
            return False


def check_dependencies():
    """检查依赖是否已安装"""
    print("检查依赖库...")

    # 依赖映射：模块名 -> 显示名
    dependencies = {
        'cv2': 'OpenCV',
        'customtkinter': 'CustomTkinter',
        'PIL': 'Pillow',
        'requests': 'Requests',
        'psutil': 'PSUtil',
        'pygame': 'Pygame',
        'numpy': 'NumPy',
        'mediapipe': 'MediaPipe'
    }

    # Windows特定依赖
    if sys.platform == 'win32':
        dependencies['win32gui'] = 'PyWin32'

    missing_count = 0

    # 检查每个依赖
    for module_name, display_name in dependencies.items():
        try:
            if module_name == 'cv2':
                import cv2
            elif module_name == 'PIL':
                from PIL import Image
            elif module_name == 'win32gui':
                import win32gui
            else:
                __import__(module_name)
            print(f"✓ {display_name} 已安装")
        except ImportError:
            print(f"✗ {display_name} 未安装")
            missing_count += 1

    return missing_count == 0


def check_and_install_dependencies():
    """检查并安装依赖"""
    # 首先检查依赖
    if check_dependencies():
        print("\n所有依赖已满足！")
        return True

    # 如果有缺失依赖，尝试安装
    print(f"\n发现缺失依赖，尝试自动安装...")

    if install_requirements():
        print("\n重新检查依赖...")
        if check_dependencies():
            print("\n所有依赖安装完成！")
            return True
        else:
            print("\n警告: 部分依赖仍然缺失")
            print("程序仍可运行，但某些功能可能受限")
            choice = input("是否继续启动程序？(y/n): ").lower().strip()
            return choice in ['y', 'yes', '是']
    else:
        print("\n依赖安装失败")
        print("请手动运行以下命令安装依赖:")
        print("pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        choice = input("是否继续启动程序？(y/n): ").lower().strip()
        return choice in ['y', 'yes', '是']


def check_smolvlm_service():
    """检查SmolVLM服务是否运行"""
    try:
        import requests
        response = requests.get("http://localhost:8080", timeout=5)
        print("✓ SmolVLM服务正在运行")
        return True
    except:
        print("✗ SmolVLM服务未运行")
        print("请确保SmolVLM服务已启动在 http://localhost:8080")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("MySoloKeeper - 打灰机守护程序")
    print("启动脚本 v1.0")
    print("=" * 60)

    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        input("按回车键退出...")
        return

    print(f"Python版本: {sys.version}")

    # 检查并安装依赖
    if not check_and_install_dependencies():
        print("\n依赖安装失败，无法启动程序")
        input("按回车键退出...")
        return

    # 检查SmolVLM服务
    print("\n检查SmolVLM服务...")
    smolvlm_running = check_smolvlm_service()

    if not smolvlm_running:
        print("\n警告: SmolVLM服务未运行")
        print("程序仍可启动，但人脸检测功能将不可用")
        choice = input("是否继续启动程序？(y/n): ").lower().strip()
        if choice not in ['y', 'yes', '是']:
            return

    # 启动主程序
    print("\n启动MySoloKeeper...")
    try:
        from main import main as run_main
        run_main()
    except Exception as e:
        print(f"启动程序失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()
