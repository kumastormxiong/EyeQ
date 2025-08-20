@echo off
REM 自动化安装依赖、激活虚拟环境并打包exe

REM 1. 检查并安装Python（需手动下载，自动检测）
python --version >nul 2>nul
if errorlevel 1 (
    echo 请先手动安装Python 3.10+ 并添加到PATH！
    pause
    exit /b 1
)

REM 2. 创建虚拟环境
if not exist venv (
    python -m venv venv
)

REM 3. 激活虚拟环境
call venv\Scripts\activate

REM 4. 升级pip
python -m pip install --upgrade pip

REM 5. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

REM 6. 打包为exe
pyinstaller --noconfirm --onefile --windowed main.py

REM 7. 完成提示
if exist dist\main.exe (
    echo 打包成功！可执行文件在 dist\main.exe
) else (
    echo 打包失败，请检查报错信息。
)
pause 