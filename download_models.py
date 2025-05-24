import os
import subprocess
from typing import List

MODELS_DIR = "models"
REPO_ID = "ggml-org/SmolVLM2-500M-Video-Instruct-GGUF"

# 需要下载的模型文件列表
MODEL_FILES = [
    "SmolVLM2-500M-Video-Instruct-f16.gguf",
    "mmproj-SmolVLM2-500M-Video-Instruct-f16.gguf"
]

def create_models_dir():
    """创建models目录"""
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"已创建目录: {MODELS_DIR}")
    else:
        print(f"目录已存在: {MODELS_DIR}")

def run_huggingface_cli(command: List[str]) -> bool:
    """运行huggingface-cli命令"""
    try:
        result = subprocess.run(
            ["huggingface-cli"] + command,
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e.stderr}")
        return False

def download_from_hf_mirror() -> bool:
    """从huggingface镜像下载"""
    print("\n使用huggingface镜像源下载...")
    command = [
        "download", REPO_ID,
        "--local-dir", MODELS_DIR,
        "--include", *MODEL_FILES
    ]
    return run_huggingface_cli(command)

def download_from_modelscope() -> bool:
    """从魔搭下载"""
    print("\n使用魔搭下载...")
    token = input("请输入魔搭访问令牌(可在https://www.modelscope.cn获取): ")
    
    # 先登录
    login_cmd = [
        "login",
        "--token", token,
        "--endpoint", "https://www.modelscope.cn"
    ]
    if not run_huggingface_cli(login_cmd):
        return False
    
    # 再下载
    download_cmd = [
        "download", REPO_ID,
        "--repo-type", "model",
        "--endpoint", "https://www.modelscope.cn",
        "--local-dir", MODELS_DIR,
        "--include", *MODEL_FILES
    ]
    return run_huggingface_cli(download_cmd)

def main():
    print("SmolVLM2 模型下载脚本")
    create_models_dir()
    
    print("\n请选择下载源:")
    print("1. huggingface镜像 (推荐)")
    print("2. 魔搭（需要令牌）")
    choice = input("请输入选择 (1/2): ")
    
    success = False
    if choice == "1":
        success = download_from_hf_mirror()
    elif choice == "2":
        success = download_from_modelscope()
    else:
        print("无效选择")
        return
    
    if success:
        print("\n所有模型文件下载完成!")
    else:
        print("\n部分文件下载失败，请检查网络连接后重试")

if __name__ == "__main__":
    main()