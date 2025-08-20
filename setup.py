from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["pyautogui", "requests", "pyperclip", "PIL", "markdown2"],
    "include_files": ["config.ini", "assets", "data"],
    "excludes": ["tkinter"],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="EyeQ",
    version="1.0",
    description="视觉AI助手",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, target_name="EyeQ.exe")],
) 