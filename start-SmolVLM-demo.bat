@echo off
chcp 65001 >nul

echo 启动 SmolVLM-500M-Instruct-f16:

::llama-server -m models/SmolVLM-500M-Instruct-f16.gguf --mmproj models/mmproj-SmolVLM-500M-Instruct-f16.gguf -ngl 99

llama-server -m models/SmolVLM2-500M-Video-Instruct-f16.gguf --mmproj models/mmproj-SmolVLM2-500M-Video-Instruct-f16.gguf -ngl 99

pause