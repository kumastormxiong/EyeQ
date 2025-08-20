import sys
import os
from PyQt5.QtWidgets import QApplication, QDialog
from gui import MainWindow, LoginDialog
import keyboard
from database import init_db
import pyperclip

def get_config_path():
    """
    获取配置文件的绝对路径。

    :return: config.ini文件的完整路径 (str)
    """
    return os.path.join(os.path.dirname(__file__), 'config.ini')

class HotkeyManager:
    """
    用于管理全局热键的类。
    """
    def __init__(self, window, hotkey):
        """
        初始化热键管理器。

        :param window: 热键触发时需要响应的窗口实例 (MainWindow)
        :param hotkey: 要注册的快捷键字符串 (str)，例如 'Alt+·'
        """
        self.window = window
        self.current_hotkey = None  # 先置空，在register_hotkey中赋值
        self.register_hotkey(hotkey)

    def register_hotkey(self, hotkey):
        """
        注册或更新全局热键。

        :param hotkey: 新的快捷键字符串 (str)
        """
        if self.current_hotkey:
            try:
                keyboard.remove_hotkey(self.current_hotkey)
            except Exception:
                pass
        try:
            keyboard.add_hotkey(hotkey, self.on_hotkey)
            self.current_hotkey = hotkey
        except ValueError as e:
            # 发生解析错误时回退到安全默认值 Alt+Q
            fallback = 'alt+q'
            print(f'热键 "{hotkey}" 无效，回退到默认值 {fallback}:', e)
            try:
                keyboard.add_hotkey(fallback, self.on_hotkey)
                self.current_hotkey = fallback
            except Exception as e2:
                print('无法注册默认热键 Alt+Q:', e2)

    def on_hotkey(self):
        """
        热键被触发时调用的回调函数。
        它会发射一个信号，由主线程的窗口来处理实际的截图操作，以保证线程安全。
        """
        self.window.screenshot_request.emit()

def main():
    """
    应用程序的主入口函数。
    """
    # 初始化数据库（如果需要，会创建表）
    init_db()

    app = QApplication(sys.argv)
    
    # 显示登录对话框
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        user_id = login_dialog.user_id
        
        # 从配置文件读取初始快捷键设置
        import configparser
        config_path = get_config_path()
        config = configparser.ConfigParser()
        hotkey = 'alt+q'  # 默认值
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
            hotkey = config.get('Window', 'hotkey', fallback='alt+q')

        # 创建主窗口，并传入用户ID
        window = MainWindow(user_id=user_id, hotkey_update_callback=None)
        hotkey_manager = HotkeyManager(window, hotkey)
        
        # 设置热键更新的回调函数
        window.hotkey_update_callback = hotkey_manager.register_hotkey
        
        window.show()
        sys.exit(app.exec_())
    else:
        # 如果用户关闭了登录窗口，则直接退出程序
        sys.exit(0)

if __name__ == '__main__':
    main() 