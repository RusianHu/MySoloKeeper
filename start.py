# -*- coding: utf-8 -*-
"""
MySoloKeeper 启动脚本
自动检查和安装依赖，然后启动程序
"""

import sys
import subprocess
import os
import importlib.util
from config import VERSION, PROJECT_NAME, PROJECT_DESCRIPTION


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
        return False


def start_smolvlm_service():
    """启动SmolVLM服务"""
    import subprocess
    import time

    # 检查启动脚本是否存在
    script_path = "start-SmolVLM.bat"
    if not os.path.exists(script_path):
        print(f"✗ 未找到SmolVLM启动脚本: {script_path}")
        return False

    print("正在启动SmolVLM服务...")
    print("这将在新窗口中启动SmolVLM服务，请不要关闭该窗口")

    try:
        # 在新的命令行窗口中启动SmolVLM
        subprocess.Popen([script_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

        print("SmolVLM服务启动中，等待服务就绪...")

        # 等待服务启动（最多等待30秒）
        for i in range(30):
            time.sleep(1)
            if check_smolvlm_service():
                print("✓ SmolVLM服务启动成功！")
                return True
            if i % 5 == 0:
                print(f"等待中... ({i+1}/30秒)")

        print("⚠ SmolVLM服务启动超时，但程序将继续运行")
        print("您可以稍后在界面中切换到SmolVLM模式")
        return False

    except Exception as e:
        print(f"✗ 启动SmolVLM服务失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print(f"{PROJECT_NAME} - {PROJECT_DESCRIPTION}")
    print(f"启动脚本 v{VERSION}")
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

    # 询问用户是否需要SmolVLM功能
    print("\n检测模式选择:")
    print("1. MediaPipe独立检测 (推荐) - 快速本地检测，无需额外服务")
    print("2. 包含SmolVLM检测 - 高精度AI检测，需要SmolVLM服务")
    print()

    choice = input("请选择检测模式 (1/2，默认为1): ").strip()

    if choice == '2':
        # 用户选择使用SmolVLM，检查服务状态
        print("\n检查SmolVLM服务...")
        smolvlm_running = check_smolvlm_service()

        if not smolvlm_running:
            print("\n注意: SmolVLM服务未运行")
            print("您可以:")
            print("1. 自动启动SmolVLM服务（推荐）")
            print("2. 手动启动SmolVLM服务后重新运行程序")
            print("3. 继续启动程序，稍后在界面中切换到SmolVLM模式")
            print("4. 使用MediaPipe独立检测模式")

            try:
                sub_choice = input("\n请选择 (1/2/3/4，默认为1): ").strip()
            except EOFError:
                sub_choice = '1'  # 默认选择自动启动

            if sub_choice == '' or sub_choice == '1':
                # 自动启动SmolVLM服务
                if start_smolvlm_service():
                    print("SmolVLM服务已启动，程序将继续运行")
                else:
                    print("SmolVLM服务启动失败，但程序将继续运行")
                    print("您可以稍后在界面中切换到SmolVLM模式")
            elif sub_choice == '2':
                print("请手动启动SmolVLM服务后重新运行程序")
                input("按回车键退出...")
                return
            elif sub_choice == '4':
                print("将使用MediaPipe独立检测模式启动")
            # sub_choice == '3' 时直接继续启动程序
    else:
        print("将使用MediaPipe独立检测模式启动（推荐）")

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
