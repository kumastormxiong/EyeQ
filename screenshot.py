import pyautogui
import os
from datetime import datetime
from PIL import Image, ImageGrab
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QEventLoop
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

# 全屏截图
def take_screenshot(save_dir):
    """
    进行一次全屏截图，并保存到指定目录。

    :param save_dir: 截图文件的保存目录 (str)
    :return: 截图文件的完整路径 (str)
    """
    screenshot = pyautogui.screenshot()
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(save_dir, f'screenshot_{timestamp}.png')
    screenshot.save(file_path)
    return file_path

# 区域截图窗口
class ScreenShotWidget(QDialog):
    """
    一个用于区域截图的自定义Qt窗口。
    它会创建一个全屏的半透明遮罩，用户可以通过拖动鼠标选择一个矩形区域进行截图。
    """
    def __init__(self, save_dir):
        """
        初始化截图窗口。

        :param save_dir: 截图成功后文件的保存目录 (str)
        """
        super().__init__()
        self.save_dir = save_dir
        # 设置窗口属性：保持在最前、无边框
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.5)  # 设置窗口透明度
        self.begin = self.end = None  # 初始化截图区域的起始点和结束点
        self.screenshot_path = None  # 用于保存最终的截图路径
        self.setCursor(Qt.CrossCursor)  # 设置鼠标样式为十字
        self.showFullScreen()  # 全屏显示

        # 创建并设置提示标签
        self.tip_label = QLabel("拖动鼠标选择区域，松开完成截图", self)
        self.tip_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: white;
            border-radius: 5px;
            padding: 10px;
            font-family: 'Microsoft YaHei';
            font-size: 14px;
        """)
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.adjustSize()
        self.tip_label.move(10, 10)
        self.setAttribute(Qt.WA_DeleteOnClose) # 确保窗口关闭时自动删除
        
        # 创建并设置尺寸显示标签
        self.size_label = QLabel(self)
        self.size_label.setStyleSheet("""
            background-color: rgba(70, 130, 180, 180);
            color: white;
            border-radius: 3px;
            padding: 5px;
            font-family: 'Microsoft YaHei';
            font-size: 12px;
        """)
        self.size_label.setAlignment(Qt.AlignCenter)
        self.size_label.adjustSize()
        self.size_label.hide()

    def paintEvent(self, event):
        """
        重写绘制事件，用于绘制遮罩、选区边框和角标。
        """
        if self.begin and self.end:
            qp = QPainter(self)
            qp.setRenderHint(QPainter.Antialiasing)
            
            # 绘制半透明的黑色遮罩
            mask = QColor(0, 0, 0, 150)
            qp.fillRect(self.rect(), mask)
            
            # 计算选择的矩形区域
            rect = QRect(self.begin, self.end)
            
            # 清除选择区域的遮罩，使其变得清晰
            qp.setCompositionMode(QPainter.CompositionMode_Clear)
            qp.fillRect(rect, Qt.transparent)
            
            # 绘制选区的蓝色边框
            qp.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(70, 130, 180), 3, Qt.SolidLine)
            qp.setPen(pen)
            qp.drawRect(rect)
            
            # 绘制四个角的蓝色标记，增强视觉效果
            corner_size = 12
            corner_color = QColor(70, 130, 180)
            qp.setPen(QPen(corner_color, 3))
            
            # 左上角
            qp.drawLine(rect.topLeft().x(), rect.topLeft().y(), 
                       rect.topLeft().x() + corner_size, rect.topLeft().y())
            qp.drawLine(rect.topLeft().x(), rect.topLeft().y(), 
                       rect.topLeft().x(), rect.topLeft().y() + corner_size)
            
            # 右上角
            qp.drawLine(rect.topRight().x(), rect.topRight().y(), 
                       rect.topRight().x() - corner_size, rect.topRight().y())
            qp.drawLine(rect.topRight().x(), rect.topRight().y(), 
                       rect.topRight().x(), rect.topRight().y() + corner_size)
            
            # 左下角
            qp.drawLine(rect.bottomLeft().x(), rect.bottomLeft().y(), 
                       rect.bottomLeft().x() + corner_size, rect.bottomLeft().y())
            qp.drawLine(rect.bottomLeft().x(), rect.bottomLeft().y(), 
                       rect.bottomLeft().x(), rect.bottomLeft().y() - corner_size)
            
            # 右下角
            qp.drawLine(rect.bottomRight().x(), rect.bottomRight().y(), 
                       rect.bottomRight().x() - corner_size, rect.bottomRight().y())
            qp.drawLine(rect.bottomRight().x(), rect.bottomRight().y(), 
                       rect.bottomRight().x(), rect.bottomRight().y() - corner_size)
            
            # 更新并显示选区尺寸标签
            width = abs(self.end.x() - self.begin.x())
            height = abs(self.end.y() - self.begin.y())
            self.size_label.setText(f"{width} × {height}")
            self.size_label.adjustSize()
            
            # 将尺寸标签放置在选区下方或上方
            label_x = min(self.begin.x(), self.end.x()) + (width - self.size_label.width()) // 2
            label_y = max(self.begin.y(), self.end.y()) + 5
            if label_y + self.size_label.height() > self.height():
                label_y = min(self.begin.y(), self.end.y()) - self.size_label.height() - 5
            self.size_label.move(label_x, label_y)
            self.size_label.show()

    def keyPressEvent(self, event):
        """
        支持按ESC键直接退出截图窗口。
        """
        if event.key() == Qt.Key_Escape:
            self.screenshot_path = None
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """当鼠标按下时，记录截图的起始点。右键单击则取消截图。"""
        if event.button() == Qt.RightButton:
            self.screenshot_path = None
            self.close()
            return

        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = self.begin
            self.update()

    def mouseMoveEvent(self, event):
        """当鼠标拖动时，更新截图的结束点并重绘画布。"""
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        """当鼠标释放时，完成截图，保存图片，并关闭截图窗口。"""
        self.end = event.pos()
        self.update()
        self.capture_and_save()
        self.hide()
        self.deleteLater()

    def capture_and_save(self):
        """
        根据起始点和结束点捕获屏幕区域，并将其保存为PNG文件。
        使用了pyautogui和Pillow作为备选方案来保证截图成功率。
        """
        if self.begin and self.end and self.begin != self.end:
            x1 = min(self.begin.x(), self.end.x())
            y1 = min(self.begin.y(), self.end.y())
            x2 = max(self.begin.x(), self.end.x())
            y2 = max(self.begin.y(), self.end.y())
            width = x2 - x1
            height = y2 - y1
            
            # 检查截图区域是否有效
            if width <= 0 or height <= 0:
                QMessageBox.warning(self, '截图失败', '截图区域无效，请重新框选')
                self.screenshot_path = None
                return
            
            try:
                # 优先使用pyautogui进行截图
                img = pyautogui.screenshot(region=(x1, y1, width, height))
            except Exception as e:
                # 如果pyautogui失败，尝试使用Pillow的ImageGrab
                try:
                    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                except Exception as e2:
                    QMessageBox.critical(self, '截图失败', f'截图失败: {e}\nPillow备选也失败: {e2}')
                    self.screenshot_path = None
                    return
            
            # 确保保存目录存在
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
            
            # 生成文件名并保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.save_dir, f'screenshot_{timestamp}.png')
            img.save(file_path)
            self.screenshot_path = file_path

# 区域截图入口
def take_area_screenshot(save_dir):
    """
    区域截图功能的入口函数。
    它会创建并显示一个ScreenShotWidget实例，并等待其关闭，然后返回截图路径。

    :param save_dir: 截图文件的保存目录 (str)
    :return: 截图文件的完整路径 (str)，如果截图失败或取消则返回None
    """
    app = QApplication.instance()
    if app is None:
        # 确保此功能在有QApplication实例的情况下被调用
        raise RuntimeError("截图功能必须在主程序事件循环下调用，不应单独创建QApplication实例！")
    
    widget = ScreenShotWidget(save_dir)
    # 使用exec_()来显示窗口，并阻塞直到它关闭
    widget.exec_()
    return widget.screenshot_path 