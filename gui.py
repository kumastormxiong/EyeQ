from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QSlider, QPushButton, QTextEdit, QLineEdit, QListWidget, 
                          QListWidgetItem, QMessageBox, QFrame, QSizePolicy, QDialog, QCheckBox, QComboBox, QFormLayout, QSystemTrayIcon, QMenu, QAction, QGraphicsBlurEffect, QTextBrowser, QStyle)
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QBrush, QLinearGradient
import os
import pyperclip
from screenshot import ScreenShotWidget  # 直接导入截图窗口类
from api_client import send_question
from database import insert_screenshot, insert_conversation
from datetime import datetime
import configparser
import keyboard
from markdown2 import markdown
from PyQt5.QtWidgets import QTextBrowser
from database import get_or_create_user, load_conversations, get_db_path, check_user_password, get_user_stats
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGraphicsBlurEffect, QWidget
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class BubbleTextBrowser(QTextBrowser):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGraphicsBlurEffect, QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush


class FrostedGlassBg(QWidget):
    """
    只负责绘制底层半透明磨砂背景，不遮挡上层内容。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.blur = QGraphicsBlurEffect()
        self.blur.setBlurRadius(18)
        self.setGraphicsEffect(self.blur)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(38, 43, 51, 180)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)

class LoginDialog(QDialog):
    """
    支持手机号+密码注册/登录的对话框，磨砂半透明风格，可拖动。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('登录/注册')
        self.setFixedSize(320, 240)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.user_id = None
        self._drag_pos = None
        # 底层磨砂背景
        self.bg = FrostedGlassBg(self)
        self.bg.setGeometry(0, 0, 320, 240)
        # 内容区
        self.content_widget = QWidget(self)
        self.content_widget.setGeometry(0, 0, 320, 240)
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        # 手机号
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('请输入11位手机号')
        self.phone_input.setMaxLength(11)
        self.phone_input.setStyleSheet("QLineEdit { background: #23262b; color: #f0f0f0; border-radius: 8px; padding: 8px; border: none; }")
        layout.addWidget(self.phone_input)
        # 密码
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText('请输入密码')
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setStyleSheet("QLineEdit { background: #23262b; color: #f0f0f0; border-radius: 8px; padding: 8px; border: none; }")
        layout.addWidget(self.pwd_input)
        # 确认密码（注册时显示）
        self.pwd2_input = QLineEdit()
        self.pwd2_input.setPlaceholderText('请再次输入密码')
        self.pwd2_input.setEchoMode(QLineEdit.Password)
        self.pwd2_input.setStyleSheet("QLineEdit { background: #23262b; color: #f0f0f0; border-radius: 8px; padding: 8px; border: none; }")
        self.pwd2_input.hide()
        layout.addWidget(self.pwd2_input)
        # 登录/注册按钮
        self.login_btn = QPushButton('登录 / 注册')
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #23262b;
                color: #f0f0f0;
                border-radius: 8px;
                padding: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #323741;
            }
        """)
        self.login_btn.clicked.connect(self.accept)
        layout.addWidget(self.login_btn)
        # 事件
        self.phone_input.textChanged.connect(self._on_phone_changed)
    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        self.content_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
    def _on_phone_changed(self):
        """
        检查手机号是否已注册，切换注册/登录模式。
        """
        phone = self.phone_input.text()
        if len(phone) == 11 and phone.isdigit():
            import sqlite3
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE phone_number=?', (phone,))
            user = c.fetchone()
            conn.close()
            if user:
                self.pwd2_input.hide()
                self.login_btn.setText('登录')
            else:
                self.pwd2_input.show()
                self.login_btn.setText('注册')
        else:
            self.pwd2_input.hide()
            self.login_btn.setText('登录 / 注册')
    def accept(self):
        phone = self.phone_input.text()
        pwd = self.pwd_input.text()
        pwd2 = self.pwd2_input.text()
        if len(phone) != 11 or not phone.isdigit():
            QMessageBox.warning(self, '格式错误', '请输入有效的11位手机号。')
            return
        if self.pwd2_input.isVisible():
            # 注册
            if not pwd or not pwd2:
                QMessageBox.warning(self, '提示', '请填写两次密码。')
                return
            if pwd != pwd2:
                QMessageBox.warning(self, '提示', '两次密码不一致。')
                return
            user_id = get_or_create_user(phone, pwd)
            if user_id:
                self.user_id = user_id
                super().accept()
            else:
                QMessageBox.warning(self, '注册失败', '注册失败，请重试。')
        else:
            # 登录
            if not pwd:
                QMessageBox.warning(self, '提示', '请输入密码。')
                return
            user_id = check_user_password(phone, pwd)
            if user_id:
                self.user_id = user_id
                super().accept()
            else:
                QMessageBox.warning(self, '登录失败', '手机号或密码错误。')

class ModernButton(QPushButton):
    def __init__(self, text, parent=None, icon_path=None):
        super().__init__(text, parent)
        self.setMinimumHeight(36)
        self.setFont(QFont('Microsoft YaHei', 10))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #23262b;
                color: #f0f0f0;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #323741;
            }
            QPushButton:pressed {
                background-color: #23262b;
            }
        """)
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config_path=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #262b33, stop:1 #191c23);
                border-radius: 12px;
                font-family: 'Microsoft YaHei';
            }
            QLabel, QCheckBox, QLineEdit, QComboBox {
                color: #f0f0f0;
                font-size: 15px;
                font-family: 'Microsoft YaHei';
            }
            QLineEdit, QComboBox {
                background: #323741;
                border: 1px solid #444a55;
                border-radius: 6px;
                padding: 4px 8px;
                color: #f0f0f0;
                font-family: 'Microsoft YaHei';
            }
            QPushButton {
                background: #222;
                color: #fff;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                min-width: 60px;
                min-height: 28px;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: #444a55;
            }
        """)
        self.setFixedSize(320, 220)
        self.bg = FrostedGlassBg(self)
        self.bg.setGeometry(0, 0, 320, 220)
        self.config_path = config_path
        # self.setStyleSheet('background: rgba(41,50,65,0.95); color: white; font-family: Microsoft YaHei;')
        layout = QFormLayout(self)

        # 快捷键设置
        self.hotkey_box = QComboBox()
        self.hotkey_box.addItems(['Ctrl+Alt+A', 'Ctrl+Shift+S', 'Alt+Q'])
        layout.addRow('截图快捷键', self.hotkey_box)

        # 回车发送
        self.enter_send_checkbox = QCheckBox('回车发送信息')
        self.enter_send_checkbox.setChecked(True)
        layout.addRow('', self.enter_send_checkbox)

        # 保存按钮
        self.save_btn = QPushButton('保存')
        self.save_btn.clicked.connect(self.save_settings)
        layout.addRow('', self.save_btn)

        self.load_settings()

    def load_settings(self):
        import configparser
        config = configparser.ConfigParser()
        if self.config_path and os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
            hotkey = config.get('Window', 'hotkey', fallback='Ctrl+Alt+A')
            idx = self.hotkey_box.findText(hotkey)
            if idx >= 0:
                self.hotkey_box.setCurrentIndex(idx)
            enter_send = config.getboolean('Window', 'enter_send', fallback=True)
            self.enter_send_checkbox.setChecked(enter_send)

    def save_settings(self):
        import configparser
        config = configparser.ConfigParser()
        if self.config_path and os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
        if 'Window' not in config:
            config['Window'] = {}
        config['Window']['hotkey'] = self.hotkey_box.currentText()
        config['Window']['enter_send'] = str(self.enter_send_checkbox.isChecked())
        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        self.accept()

class CustomTextEdit(QTextEdit):
    """
    自定义的QTextEdit，用于捕获Enter事件。
    """
    return_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText('输入问题，回车提问...')
        self.setStyleSheet("QTextEdit { background: #23262b; color: #f0f0f0; border-radius: 8px; padding: 8px; border: none; }")

    def keyPressEvent(self, event):
        """
        重写按键事件，实现Enter发送和Shift+Enter换行。
        """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event) # Shift+Enter -> 换行
            else:
                self.return_pressed.emit() # Enter -> 发送
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    """
    应用程序的主窗口。
    集成了截图、提问、显示历史记录等核心功能。
    """
    screenshot_request = pyqtSignal()
    answer_ready = pyqtSignal(object, str, bool)

    def __init__(self, user_id, hotkey_update_callback=None):
        """
        初始化主窗口。
        """
        super().__init__()
        self.user_id = user_id
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.setWindowTitle('EyeQ')
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 移除置顶，允许调整大小
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._drag_pos = None
        self.screenshot_path = None
        self.screenshot_id = None
        self.current_screenshot_path = None  # 添加当前截图路径的初始化
        self.api_key = self.load_api_key()
        self.screenshot_dir = self.load_screenshot_dir()
        self.hotkey_update_callback = hotkey_update_callback
        self.screenshot_request.connect(self.screenshot_and_ask_mainthread)
        self.answer_ready.connect(self.replace_answer_bubble)
        self.screenshot_widget = None
        
        # 初始化UI组件
        self._init_ui()
        
        # 加载用户设置和窗口几何信息
        self.load_user_settings()
        self.load_window_geometry()
        
        # 创建系统托盘
        self._create_tray_icon()
        
        # 加载历史记录
        self.load_history()

    def __init__(self, user_id, hotkey_update_callback=None):
        super().__init__()
        self.user_id = user_id
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.setWindowTitle('EyeQ')
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 移除置顶，允许调整大小
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._drag_pos = None
        self.screenshot_path = None
        self.screenshot_id = None
        self.current_screenshot_path = None  # 添加当前截图路径的初始化
        self.api_key = self.load_api_key()
        self.screenshot_dir = self.load_screenshot_dir()
        self.hotkey_update_callback = hotkey_update_callback
        self.screenshot_request.connect(self.screenshot_and_ask_mainthread)
        self.answer_ready.connect(self.replace_answer_bubble)
        self.screenshot_widget = None
        
        # 初始化UI组件
        self._init_ui()
        
        # 加载用户设置和窗口几何信息
        self.load_user_settings()
        self.load_window_geometry()
        
        # 创建系统托盘
        self._create_tray_icon()
        
        # 加载历史记录
        self.load_history()

    def _init_ui(self):
        """初始化用户界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建背景
        self.bg = FrostedGlassBg(self)
        self.bg.setGeometry(self.rect())
        
        # 创建内容容器
        self.content_container = QWidget(self)
        self.content_container.setGeometry(self.rect())
        
        # 创建主布局
        main_layout = QVBoxLayout(self.content_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建标题栏
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)
        
        # 输入框在上方
        input_container = self._create_input_area()
        main_layout.addWidget(input_container)
        
        # 聊天历史区在下方，初始不显示且不占空间
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                font-family: 'Microsoft YaHei';
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 5px;
                font-family: 'Microsoft YaHei';
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                width: 0px; height: 0px; background: transparent; }
        """)
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.hide()  # 启动时隐藏
        main_layout.addWidget(self.history_list)
        self.history_list.setMaximumHeight(0)  # 不占空间
        
        # 设置窗口初始高度为最小，仅显示标题栏和输入框
        self.setFixedHeight(150)
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)
        self.resize(450, 150)

    def _create_input_area(self):
        input_container = QWidget()
        input_container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(input_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.input_line = CustomTextEdit()
        self.input_line.setFixedHeight(80)
        self.input_line.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_line.setWordWrapMode(True)
        self.input_line.setStyleSheet("""
            QTextEdit {
                background: rgba(60, 65, 75, 0.8);
                border: 2px solid rgba(100, 110, 130, 0.5);
                border-radius: 8px;
                color: #f0f0f0;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
                padding: 8px;
            }
            QTextEdit:focus {
                border: 2px solid rgba(120, 140, 180, 0.8);
            }
            QScrollBar:vertical {width:0px; background:transparent;}
        """)
        self.input_line.setPlaceholderText("输入问题或按Alt+Q截图...")
        self.input_line.return_pressed.connect(self.ask_question)
        layout.addWidget(self.input_line)
        return input_container

    def _auto_resize_input(self):
        doc = self.input_line.document()
        doc_height = doc.size().height()
        min_h = 40
        max_h = 200
        new_h = max(min_h, min(int(doc_height + 16), max_h))
        self.input_line.setFixedHeight(new_h)

    def _create_title_bar(self):
        """创建标题栏"""
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        # 标题
        title_label = QLabel("EyeQ AI")
        title_label.setStyleSheet("color: #f0f0f0; font-size: 16px; font-weight: bold; font-family: 'Microsoft YaHei';")
        layout.addWidget(title_label)
        layout.addStretch()
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        btn_style = "color:#fff; background:#222; border-radius:6px; font-size:18px; font-weight:bold; min-width:32px; min-height:30px; max-width:32px; max-height:30px; padding:0; font-family: 'Microsoft YaHei';"
        # 新建对话按钮
        new_btn = ModernButton("N", title_bar)
        new_btn.setStyleSheet(btn_style)
        new_btn.setFixedSize(32, 30)
        new_btn.clicked.connect(self.new_chat)
        button_layout.addWidget(new_btn)
        # 设置按钮
        settings_btn = ModernButton("S", title_bar)
        settings_btn.setStyleSheet(btn_style)
        settings_btn.setFixedSize(32, 30)
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)
        # 帮助按钮
        help_btn = ModernButton("H", title_bar)
        help_btn.setStyleSheet(btn_style)
        help_btn.setFixedSize(32, 30)
        help_btn.clicked.connect(self.show_info)
        button_layout.addWidget(help_btn)
        # 退出按钮
        exit_btn = ModernButton("X", title_bar)
        exit_btn.setStyleSheet(btn_style)
        exit_btn.setFixedSize(32, 30)
        exit_btn.clicked.connect(self.exit_app)
        button_layout.addWidget(exit_btn)
        layout.addLayout(button_layout)
        return title_bar

    def _create_tray_icon(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 如果没有图标文件，使用默认图标
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show_and_raise)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def show_and_raise(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        self.tray_icon.hide()
        self.close()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

    def changeEvent(self, event):
        if event.type() == event.WindowStateChange:
            if self.isMinimized():
                self.hide()
        super().changeEvent(event)

    def load_window_geometry(self):
        """加载窗口大小和位置"""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
            if 'WindowGeometry' in config:
                x = config.getint('WindowGeometry', 'x', fallback=100)
                y = config.getint('WindowGeometry', 'y', fallback=100)
                width = config.getint('WindowGeometry', 'width', fallback=450)
                height = config.getint('WindowGeometry', 'height', fallback=650)
                self.setGeometry(x, y, width, height)

    def save_window_geometry(self):
        """保存窗口大小和位置"""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
        if 'WindowGeometry' not in config:
            config['WindowGeometry'] = {}
        geometry = self.geometry()
        config['WindowGeometry']['x'] = str(geometry.x())
        config['WindowGeometry']['y'] = str(geometry.y())
        config['WindowGeometry']['width'] = str(geometry.width())
        config['WindowGeometry']['height'] = str(geometry.height())
        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)

    def closeEvent(self, event):
        """重写关闭事件，保存窗口大小和位置"""
        self.save_window_geometry()
        self.tray_icon.hide()
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        # 安装事件过滤器
        self.input_line.installEventFilter(self)

    def show_and_fill_text(self, text):
        self.show_and_raise()
        self.input_line.setText(text)
        self.input_line.setFocus()

    def load_api_key(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config.ini'), encoding='utf-8')
        return config.get('API', 'api_key', fallback='')

    def load_screenshot_dir(self):
        # 修正：始终返回 Assistant/data/screenshots 绝对路径
        return os.path.join(os.path.dirname(__file__), 'data', 'screenshots')

    def change_opacity(self, value):
        self.setWindowOpacity(value / 100)

    def _create_blur_effect(self):
        # 此函数不再需要，模糊效果由FrostedGlassBg处理
        pass

    def paintEvent(self, event):
        # 半透明深灰磨砂背景
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(38, 43, 51, 220))  # 深灰
        gradient.setColorAt(1, QColor(25, 28, 35, 200))  # 更深灰
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

    def screenshot_and_ask(self):
        # 区域截图并弹出输入框
        self.hide()  # 先隐藏窗口避免截到自身
        self.screenshot_path = take_area_screenshot(self.screenshot_dir)
        self.show()
        if not self.screenshot_path:
            QMessageBox.warning(self, '截图失败', '未获取到截图')
            return
        # 保存截图到数据库
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.screenshot_id = insert_screenshot(self.user_id, self.screenshot_path, timestamp)
        QMessageBox.information(self, '截图成功', f'截图已保存: {self.screenshot_path}\n请输入你的问题后回车')
        self.input_line.setFocus()

    def ask_question(self):
        question = self.input_line.toPlainText().strip()
        if not question:
            return
        thinking_item = self.add_chat_bubble(question, '', is_markdown=False)
        self.input_line.clear()
        self._current_bubble = None  # Reset for new question
        def do_reply():
            try:
                q_lower = question.lower()
                if any(x in q_lower for x in ['你是什么模型', '你是谁']):
                    answer = '您好，我是EyeQ，一个由AI驱动的视觉助手。'
                    self.answer_ready.emit(thinking_item, answer, False)
                    return
                if not self.api_key or self.api_key == '你的通义千问API密钥':
                    self.answer_ready.emit(thinking_item, 'API密钥未设置，请在config.ini中填写。', False)
                    return
                from api_client import stream_question
                from database import insert_conversation
                from datetime import datetime
                screenshot_path = getattr(self, 'current_screenshot_path', None)
                # 流式获取内容
                last_content = ''
                for partial in stream_question(self.api_key, question, screenshot_path):
                    # 只追加新内容
                    self.answer_ready.emit(thinking_item, partial, True)
                    last_content = partial
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                insert_conversation(self.user_id, question, last_content, self.screenshot_id, timestamp)
            except Exception as e:
                self.answer_ready.emit(thinking_item, f'发送失败: {str(e)}', False)
        import threading
        threading.Thread(target=do_reply, daemon=True).start()

    def load_user_settings(self):
        import configparser
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
            self.hotkey = config.get('Window', 'hotkey', fallback='Alt+Q')
            self.enter_send = config.getboolean('Window', 'enter_send', fallback=True)
        else:
            self.hotkey = 'Alt+Q'
            self.enter_send = True

    def open_settings(self):
        dlg = SettingsDialog(self, self.config_path)
        if dlg.exec_():
            self.load_user_settings()
            # 通知主程序重新注册快捷键
            if self.hotkey_update_callback:
                self.hotkey_update_callback(self.hotkey)
            # 重新绑定回车事件
            if self.enter_send:
                self.input_line.return_pressed.connect(self.ask_question)
            else:
                try:
                    self.input_line.return_pressed.disconnect()
                except:
                    pass 

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None 

    def screenshot_and_ask_mainthread(self):
        """
        主线程中处理截图请求的槽函数。
        """
        # 隐藏主窗口以便截图
        self.hide()
        # 每次都新建截图窗口，避免信号重复连接和资源冲突
        save_dir = self.load_screenshot_dir()
        screenshot_widget = ScreenShotWidget(save_dir)
        screenshot_widget.screenshot_done.connect(self.on_screenshot_finished)
        screenshot_widget.showFullScreen()
        self.screenshot_widget = screenshot_widget  # 临时引用

    def on_screenshot_finished(self, screenshot_path):
        """
        截图完成后的回调槽函数。
        """
        if self.screenshot_widget:
            self.screenshot_widget.hide()
            self.screenshot_widget.deleteLater()
            self.screenshot_widget = None
        self.show_and_raise()
        print(f"调试信息 - 截图完成回调，路径: {screenshot_path}")
        if screenshot_path:
            self.current_screenshot_path = screenshot_path
            print(f"调试信息 - 设置current_screenshot_path: {self.current_screenshot_path}")
            self.input_line.clear()
            from PyQt5.QtGui import QTextCursor, QTextImageFormat
            cursor = self.input_line.textCursor()
            img_format = QTextImageFormat()
            img_format.setName(screenshot_path)
            img_format.setWidth(100)
            img_format.setHeight(100)
            cursor.insertImage(img_format)
            self.input_line.insertPlainText("\n请输入问题...")
            self.input_line.setFocus()
            self.input_line.installEventFilter(self)
        else:
            self.current_screenshot_path = None
            print("调试信息 - 截图被取消，current_screenshot_path设为None")

    # 增加图片缩放功能
    def zoomImage(self, img_path):
        from PyQt5.QtWidgets import QLabel, QDialog, QVBoxLayout
        from PyQt5.QtGui import QPixmap
        dlg = QDialog(self)
        dlg.setWindowTitle("图片预览")
        vbox = QVBoxLayout(dlg)
        label = QLabel()
        pix = QPixmap(img_path)
        label.setPixmap(pix)
        label.setScaledContents(True)
        label.setMinimumSize(400, 300)
        vbox.addWidget(label)
        dlg.setLayout(vbox)
        dlg.resize(pix.width(), pix.height())
        dlg.exec_()

    # 重载eventFilter，捕获输入框图片点击事件
    def eventFilter(self, obj, event):
        if obj == self.input_line and event.type() == event.MouseButtonRelease:
            print("调试信息 - 捕获到输入框鼠标释放事件")
            cursor = self.input_line.cursorForPosition(event.pos())
            fmt = cursor.charFormat()
            print(f"调试信息 - charFormat isImageFormat: {fmt.isImageFormat()}")
            if fmt.isImageFormat():
                img_path = fmt.toImageFormat().name()
                print(f"调试信息 - 点击图片路径: {img_path}")
                self.zoomImage(img_path)
                return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        # 安装事件过滤器
        self.input_line.installEventFilter(self)

    def add_chat_bubble(self, question, answer, is_markdown=True):
        # 首次有回复时显示历史区并扩展窗口高度
        if not self.history_list.isVisible():
            self.history_list.show()
            self.history_list.setMaximumHeight(16777215)  # 恢复最大高度
            self.setMinimumHeight(150)
            self.setMaximumHeight(16777215)
            self.resize(self.width(), 650)
        # 问题气泡（左）
        q_item = QListWidgetItem()
        q_widget = QWidget()
        q_layout = QHBoxLayout(q_widget)
        q_layout.setContentsMargins(0, 0, 0, 0)
        q_layout.setAlignment(Qt.AlignLeft)
        q_label = BubbleTextBrowser()
        q_label.doubleClicked.connect(lambda b=q_label: self.zoom_bubble(b))
        q_label.setOpenExternalLinks(True)
        q_label.setStyleSheet('background: #3c414b; color: #f0f0f0; border-radius: 12px; padding: 8px 12px; max-width: 320px; border: none;')
        q_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        q_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        q_label.setFrameShape(QTextBrowser.NoFrame)
        q_label.setFont(QFont('Microsoft YaHei', 10))
        q_label.setMaximumHeight(9999) # 移除最大高度限制
        q_label.setMinimumWidth(60)
        q_label.setMaximumWidth(320)
        q_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        q_label.setHtml(markdown(question))
        q_layout.addWidget(q_label)
        q_layout.addStretch()
        q_item.setSizeHint(q_widget.sizeHint())
        self.history_list.addItem(q_item)
        self.history_list.setItemWidget(q_item, q_widget)
        # 答案气泡（右）
        a_item = QListWidgetItem()
        a_widget = QWidget()
        a_layout = QHBoxLayout(a_widget)
        a_layout.setContentsMargins(0, 0, 0, 0)
        a_layout.setAlignment(Qt.AlignRight)
        a_label = BubbleTextBrowser()
        a_label.doubleClicked.connect(lambda b=a_label: self.zoom_bubble(b))
        a_label.setOpenExternalLinks(True)
        a_label.setStyleSheet('background: #323741; color: #f0f0f0; border-radius: 12px; padding: 8px 12px; max-width: 320px; border: none;')
        a_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        a_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        a_label.setFrameShape(QTextBrowser.NoFrame)
        a_label.setFont(QFont('Microsoft YaHei', 10))
        a_label.setMaximumHeight(9999) # 移除最大高度限制
        a_label.setMinimumWidth(60)
        a_label.setMaximumWidth(320)
        a_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        
        # 将答案设置移到replace_answer_bubble中，这里只创建
        if answer:
            if is_markdown:
                a_label.setHtml(markdown(answer))
            else:
                a_label.setHtml(f'<span>{answer}</span>')

        a_layout.addStretch()
        a_layout.addWidget(a_label)
        a_item.setSizeHint(a_widget.sizeHint())
        self.history_list.addItem(a_item)
        self.history_list.setItemWidget(a_item, a_widget)
        self.history_list.scrollToBottom()
        self._auto_resize_window()
        return a_item

    def zoom_bubble(self, browser):
        self.original_geometry = browser.geometry()
        self.zoomed_browser = browser
        self.zoomed_browser.setFixedSize(self.width() - 50, self.height() - 100)
        self.zoomed_browser.raise_()

    def unzoom_bubble(self):
        if hasattr(self, 'zoomed_browser') and self.zoomed_browser:
            self.zoomed_browser.setFixedSize(self.original_geometry.width(), self.original_geometry.height())
            self.zoomed_browser = None

# 支持多气泡弹窗
    def replace_answer_bubble(self, a_item, answer, is_markdown=True):
        if not hasattr(self, '_current_bubble') or self._current_bubble is None:
            self._current_bubble = BubbleWindow(answer)
            geo = self.geometry()
            x = geo.x() + geo.width() + 20
            y = geo.y()
            self._current_bubble.move(x, y)
            self._current_bubble.show()
        else:
            self._current_bubble.setText(answer)
            self._current_bubble.adjustSize()
            self._current_bubble.raise_()

    def add_chat_bubble(self, question, answer, is_markdown=True):
        return None

    def load_history(self):
        """
        加载当前用户的对话历史记录，并显示在界面上。
        """
        history = load_conversations(self.user_id)
        for question, answer in history:
            self.add_chat_bubble(question, answer) 

    def _auto_resize_window(self):
        """
        根据聊天内容自动调整主窗口高度（不超过屏幕高度的80%）。
        """
        screen = QApplication.primaryScreen().availableGeometry()
        max_height = int(screen.height() * 0.8)
        content_height = self.content_container.sizeHint().height() + 40
        new_height = min(max_height, max(400, content_height))
        self.resize(self.width(), new_height)

    def new_chat(self):
        """
        新建对话，清空历史区，开启新分支。
        """
        self.history_list.clear()
        self.screenshot_id = None
        self.screenshot_path = None
        self._auto_resize_window() 

    def show_info(self):
        user_stats = get_user_stats(self.user_id)
        if user_stats:
            user_name, total_questions = user_stats
            info_text = f"""
            <b>您:</b> {user_name}<br>
            <b>询问次数:</b> {total_questions}<br><br>
            <b>指引：</b><br>
            - <b>Alt+Q:</b> 截屏 <br>
            - <b>N:</b> 新对话 <br>
            - <b>ESC:</b> 隐藏窗口 <br>
            - <b>        </b>            <br>
            - <b> Made by 虚空造物  </b><br>
            """
            QMessageBox.information(self, '信息', info_text)
        else:
            QMessageBox.warning(self, '信息', '无法获取用户信息。')

    def keyPressEvent(self, event):
        """按ESC键最小化窗口"""
        if event.key() == Qt.Key_Escape:
            if hasattr(self, 'zoomed_browser') and self.zoomed_browser:
                self.unzoom_bubble()
            else:
                self.showMinimized()
        else:
            super().keyPressEvent(event) 
            
    def resizeEvent(self, event):
        """同步调整背景和内容区大小"""
        if hasattr(self, 'bg') and self.bg:
            self.bg.setGeometry(self.rect())
        if hasattr(self, 'content_container') and self.content_container:
            self.content_container.setGeometry(self.rect())
        super().resizeEvent(event) 

# 统一帮助弹窗样式
from PyQt5.QtWidgets import QMessageBox
old_information = QMessageBox.information
old_warning = QMessageBox.warning

def themed_information(parent, title, text):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Information)
    box.setStyleSheet("""
        QMessageBox {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #262b33, stop:1 #191c23);
            border-radius: 12px;
            font-family: 'Microsoft YaHei';
        }
        QLabel {
            color: #f0f0f0;
            font-size: 15px;
            font-family: 'Microsoft YaHei';
        }
        QPushButton {
            background: #222;
            color: #fff;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 60px;
            min-height: 28px;
            font-family: 'Microsoft YaHei';
        }
        QPushButton:hover {
            background: #444a55;
        }
    """)
    return box.exec_()

def themed_warning(parent, title, text):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Warning)
    box.setStyleSheet("""
        QMessageBox {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #262b33, stop:1 #191c23);
            border-radius: 12px;
            font-family: 'Microsoft YaHei';
        }
        QLabel {
            color: #f0f0f0;
            font-size: 15px;
            font-family: 'Microsoft YaHei';
        }
        QPushButton {
            background: #222;
            color: #fff;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 60px;
            min-height: 28px;
            font-family: 'Microsoft YaHei';
        }
        QPushButton:hover {
            background: #444a55;
        }
    """)
    return box.exec_()

QMessageBox.information = themed_information
QMessageBox.warning = themed_warning 

class BubbleWindow(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet('''
            QDialog {
                background-color: #323741;
                border-radius: 16px;
                border: 1px solid #444a55;
            }
            QTextBrowser {
                color: #f0f0f0;
                font-size: 16px;
                font-family: 'Microsoft YaHei';
                background-color: transparent;
                border: none;
                padding: 16px;
            }
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.browser = QTextBrowser()
        self.browser.setHtml(markdown(text))
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser)
        self.adjustSize()
        self.setMaximumWidth(480)
        self.setMinimumWidth(180)
        self.setMinimumHeight(60)

    def setText(self, text):
        self.browser.setHtml(markdown(text))
        self.adjustSize() 