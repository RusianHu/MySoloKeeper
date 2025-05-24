# -*- coding: utf-8 -*-
"""
MySoloKeeper 一键安装和启动脚本
"""

import sys
import subprocess
import os


def install_dependencies():
    """安装依赖"""
    print("正在安装依赖包...")
    print("使用中国镜像源加速下载...")
    
    try:
        # 使用清华大学镜像源
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
        ], check=True)
        print("✓ 依赖安装成功！")
        return True
    except subprocess.CalledProcessError:
        print("✗ 镜像源安装失败，尝试官方源...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            print("✓ 依赖安装成功！")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 依赖安装失败: {e}")
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("MySoloKeeper - 打灰机守护程序")
    print("一键安装和启动脚本")
    print("=" * 60)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        input("按回车键退出...")
        return
    
    print(f"Python版本: {sys.version}")
    
    # 检查requirements.txt是否存在
    if not os.path.exists("requirements.txt"):
        print("错误: 找不到requirements.txt文件")
        input("按回车键退出...")
        return
    
    # 安装依赖
    print("\n步骤1: 安装依赖包")
    if not install_dependencies():
        print("\n依赖安装失败！")
        print("请手动运行以下命令:")
        print("pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        input("按回车键退出...")
        return
    
    # 启动程序
    print("\n步骤2: 启动程序")
    try:
        print("正在启动MySoloKeeper...")
        from main import main as run_main
        run_main()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖都已正确安装")
        input("按回车键退出...")
    except Exception as e:
        print(f"程序运行错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()
