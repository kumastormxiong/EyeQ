from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QSlider, QPushButton, QTextEdit, QLineEdit, QListWidget, 
                          QListWidgetItem, QMessageBox, QFrame, QSizePolicy, QDialog, QCheckBox, QComboBox, QFormLayout, QSystemTrayIcon, QMenu, QAction, QGraphicsBlurEffect)
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QBrush, QLinearGradient
import os
import pyperclip
from screenshot import take_area_screenshot
from api_client import send_question
from database import insert_screenshot, insert_conversation
from datetime import datetime
import configparser
import keyboard
from markdown2 import markdown
from PyQt5.QtWidgets import QTextBrowser
from database import get_or_create_user, load_conversations, get_db_path, check_user_password, get_user_stats

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
        self.setWindowTitle('设置')
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
        self.api_key = self.load_api_key()
        self.screenshot_dir = self.load_screenshot_dir()
        self.hotkey_update_callback = hotkey_update_callback
        self.screenshot_request.connect(self.screenshot_and_ask_mainthread)
        self.answer_ready.connect(self.replace_answer_bubble)

        # 分层布局，底层为磨砂背景，上层为内容
        self.bg = FrostedGlassBg(self)
        self.content_container = QWidget(self)
        self.main_layout = QVBoxLayout(self.content_container)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(6)

        # 标题栏
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel('EyeQ')
        self.title_label.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        self.title_label.setStyleSheet("color: white; background: transparent;")
        self.new_chat_btn = ModernButton('N')
        self.new_chat_btn.setFixedWidth(80)
        self.new_chat_btn.clicked.connect(self.new_chat)
        
        self.info_btn = ModernButton('H')
        self.info_btn.setFixedWidth(80)
        self.info_btn.clicked.connect(self.show_info)

        self.close_btn = QPushButton('×')
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setFont(QFont('Arial', 14))
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("QPushButton { background: transparent; color: white; border: none; } QPushButton:hover { color: #4682b4; }")
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.new_chat_btn)
        self.header_layout.addWidget(self.info_btn)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.close_btn)
        self.main_layout.addWidget(self.header_frame)

        # Author Label
        # self.author_label = QLabel('by 虚空造物')
        # self.author_label.setFont(QFont('Microsoft YaHei', 8))
        # self.author_label.setStyleSheet("color: #aaa; background: transparent;")
        # self.author_label.setAlignment(Qt.AlignCenter)
        # self.main_layout.addWidget(self.author_label)

        # 截图缩略图显示区
        self.screenshot_thumb = QLabel()
        self.screenshot_thumb.setFixedSize(70, 50)
        self.screenshot_thumb.setScaledContents(True)
        self.screenshot_thumb.hide()
        self.main_layout.addWidget(self.screenshot_thumb, alignment=Qt.AlignLeft)
        # 操作区
        self.action_frame = QFrame()
        self.action_frame.setStyleSheet("background: transparent;")
        self.action_layout = QHBoxLayout(self.action_frame)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        # 移除截图按钮相关代码
        # self.screenshot_btn = ModernButton('截图')
        # self.screenshot_btn.setMinimumWidth(60)
        # self.screenshot_btn.clicked.connect(self.screenshot_request.emit)
        # self.action_layout.addWidget(self.screenshot_btn)
        # self.content_layout.addWidget(self.action_frame)
        # 不再添加action_frame到content_layout
        # 输入区
        self.input_frame = ModernFrame()
        self.input_layout = QHBoxLayout(self.input_frame)
        self.input_line = CustomTextEdit()
        self.input_line.setFont(QFont('Microsoft YaHei', 10))
        self.input_line.setStyleSheet("QTextEdit { background: #23262b; color: #f0f0f0; border-radius: 8px; padding: 8px; border: none; }")
        self.input_line.return_pressed.connect(self.ask_question)
        self.input_line.setFixedHeight(60) # 初始高度
        self.input_layout.addWidget(self.input_line)
        self.main_layout.addWidget(self.input_frame)
        # 聊天历史区
        self.history_frame = ModernFrame()
        self.history_layout = QVBoxLayout(self.history_frame)
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("QListWidget { background: transparent; border: none; } QScrollBar:vertical {width:0px;}")
        self.history_layout.addWidget(self.history_list)
        self.main_layout.addWidget(self.history_frame)
        # 新建对话按钮
        # self.new_chat_btn = ModernButton('新建对话') # Moved to header_layout
        # self.new_chat_btn.setFixedWidth(80)
        # self.new_chat_btn.clicked.connect(self.new_chat)
        # self.header_layout.insertWidget(1, self.new_chat_btn)
        # 极简去除footer、分割线、设置等
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        if icon.isNull():  # 如果图标为空，创建一个默认图标
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(70, 130, 180))
            icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        tray_menu = QMenu()
        show_action = QAction('显示', self)
        show_action.triggered.connect(self.show_and_raise)
        tray_menu.addAction(show_action)
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        self.answer_ready.connect(self.replace_answer_bubble) # 连接信号到槽
        # 在__init__的末尾调用
        self.load_history()
        # 聊天历史区磨砂背景（只对frame，不对气泡）
        # self.history_frame.setGraphicsEffect(self._create_blur_effect()) # 移除此行

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
        # 窗口显示时的处理，不再处理剪贴板
        super().showEvent(event)

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
        
        thinking_item = self.add_chat_bubble(question, '正在思考……', is_markdown=False)
        self.input_line.clear()

        def do_reply():
            try:
                q_lower = question.lower()
                # 模型身份相关问题固定回复
                if any(x in q_lower for x in ['你是什么模型', '你是谁']):
                    answer = '您好，我是EyeQ，一个由AI驱动的视觉助手。'
                    self.answer_ready.emit(thinking_item, answer, False)
                    return

                if not self.api_key or self.api_key == '你的通义千问API密钥':
                    self.answer_ready.emit(thinking_item, 'API密钥未设置，请在config.ini中填写。', False)
                    return
                
                from api_client import send_question
                from database import insert_conversation
                from datetime import datetime
                answer = send_question(self.api_key, question, self.screenshot_path)
                self.answer_ready.emit(thinking_item, answer, True)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                insert_conversation(self.user_id, question, answer, self.screenshot_id, timestamp)
            except Exception as e:
                self.answer_ready.emit(thinking_item, f'发送失败: {str(e)}', False)

        import threading
        threading.Thread(target=do_reply, daemon=True).start()

    def load_user_settings(self):
        import configparser
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path, encoding='utf-8')
            self.hotkey = config.get('Window', 'hotkey', fallback='Ctrl+Alt+A')
            self.enter_send = config.getboolean('Window', 'enter_send', fallback=True)

    def open_settings(self):
        dlg = SettingsDialog(self, self.config_path)
        if dlg.exec_():
            self.load_user_settings()
            # 通知主程序重新注册快捷键
            if self.hotkey_update_callback:
                self.hotkey_update_callback(self.hotkey)
            # 重新绑定回车事件
            if self.enter_send:
                self.input_line.returnPressed.connect(self.ask_question)
            else:
                try:
                    self.input_line.returnPressed.disconnect()
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
        在主线程中执行截图操作，并处理后续逻辑。
        由热键或按钮点击触发。
        """
        self.hide()
        from screenshot import take_area_screenshot
        screenshot_path = take_area_screenshot(self.screenshot_dir)
        self.show_and_raise()
        if not screenshot_path:
            QMessageBox.warning(self, '截图失败', '未获取到截图')
            return
        from database import insert_screenshot
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.screenshot_id = insert_screenshot(self.user_id, screenshot_path, timestamp)
        self.screenshot_path = screenshot_path
        pixmap = QPixmap(screenshot_path)
        if not pixmap.isNull():
            self.screenshot_thumb.setPixmap(pixmap.scaled(self.screenshot_thumb.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.screenshot_thumb.show()
        self.input_line.setFocus() 
    def add_chat_bubble(self, question, answer, is_markdown=True):
        # 问题气泡（左）
        q_item = QListWidgetItem()
        q_widget = QWidget()
        q_layout = QHBoxLayout(q_widget)
        q_layout.setContentsMargins(0, 0, 0, 0)
        q_layout.setAlignment(Qt.AlignLeft)
        q_label = BubbleTextBrowser()
        q_label.doubleClicked.connect(lambda b=q_label: self.zoom_bubble(b))
        q_label.setOpenExternalLinks(True)
        # 聊天气泡不设置任何模糊/透明，保证文字清晰
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
    def replace_answer_bubble(self, a_item, answer, is_markdown=True):
        a_widget = self.history_list.itemWidget(a_item)
        if a_widget:
            a_label = a_widget.findChild(QTextBrowser)
            if a_label:
                if is_markdown:
                    a_label.setHtml(markdown(answer))
                else:
                    a_label.setHtml(f'<span>{answer}</span>')
                # 调整大小以适应新内容
                a_label.adjustSize()
                a_widget.adjustSize()
                a_item.setSizeHint(a_widget.sizeHint()) 

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
        self.bg.setGeometry(self.rect())
        self.content_container.setGeometry(self.rect())
        super().resizeEvent(event) 