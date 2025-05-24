# -*- coding: utf-8 -*-
"""
MySoloKeeper - 打灰机守护程序
主程序入口
"""

import sys
import os
import traceback
from gui import MySoloKeeperGUI
from config import VERSION, PROJECT_NAME, PROJECT_DESCRIPTION


def check_dependencies():
    """检查依赖库是否安装"""
    required_modules = [
        'cv2', 'customtkinter', 'PIL', 'requests',
        'psutil', 'pygame', 'numpy', 'mediapipe'
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print("缺少以下依赖库:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        return False

    return True


def main():
    """主函数"""
    print("=" * 50)
    print(f"{PROJECT_NAME} - {PROJECT_DESCRIPTION}")
    print(f"版本: {VERSION}")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return

    try:
        # 创建并运行GUI
        app = MySoloKeeperGUI()
        app.run()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()
