@echo off
chcp 65001 >nul

echo 测试bat中的中文字符稳定性

echo 请输入包含特殊符号的中文文本
set /p "user_input="

:: 显示原始输入
echo 您输入的是：%user_input%

:: 如果需要在文件名中使用，替换非法字符
set "safe_filename=%user_input%"
rem 更安全的字符替换处理
setlocal enabledelayedexpansion
set "safe_filename=!input!"
set "safe_filename=!safe_filename:<=_!"
set "safe_filename=!safe_filename:>=_!" 
set "safe_filename=!safe_filename:|=_!"
set "safe_filename=!safe_filename:*=_!"
set "safe_filename=!safe_filename:?=_!"
set "safe_filename=!safe_filename:"='!"
set "safe_filename=!safe_filename:%%=_!"
endlocal

echo 安全的文件名：%safe_filename%

pause