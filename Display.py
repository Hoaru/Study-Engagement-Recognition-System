import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import cv2
import sys
import threading
import requests
import json
from video import *

from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore, QtGui, QtWidgets

import matplotlib
matplotlib.use("Qt5Agg")  # 声明使用QT5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

import time


##################################################
#图表嵌入
class MyFigure(FigureCanvas):#这是在PYQt中引入matplotlib的关键
    def __init__(self, width=5, height=4, dpi=100):
        # 第一步：创建一个创建Figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # 第二步：在父类中激活Figure窗口
        super(MyFigure, self).__init__(self.fig)  # 此句不可缺少，否则不能显示图形



#信号类
class MySignal(QWidget):
    # 定义信号,定义参数为无类型
    update_date = pyqtSignal()


#捕获传输
class Display(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("参与度自动识别系统")

        self.btn_open_camera.clicked.connect(self.openCamera)
        self.btn_close_camera.clicked.connect(self.closeCamera)
        self.btn_post.clicked.connect(self.captureCamera)

        self.stopEvent = threading.Event()
        self.stopEvent.clear()

        self.capture = False
        self.capIsNone = True

        self.setBtnAble(True, False, False)
        self.result_list = []

        # 初始化信号
        self.ms = MySignal()
        self.ms.update_date.connect(self.drawGraph)

    def openCamera(self):
        self.setBtnAble(False, True, True)
        self.allFrame = 0
        self.capIsNone = False
        self.label_screen.setStyleSheet("QLabel{background:#FFFFF;}")
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.sz = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                   int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        self.out = cv2.VideoWriter('output.mp4', fourcc, 10, self.sz, True)
        th = threading.Thread(target=self.display)
        th.start()

    def closeCamera(self):
        self.label_screen.setStyleSheet("QLabel{background:#000000;}")
        self.stopEvent.set()
        self.capIsNone = True
        self.setBtnAble(True, False, False)

    def display(self):
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                self.label_screen.setPixmap(QPixmap.fromImage(img))
                if self.capture == True and self.allFrame != 64:
                    self.label_onTime.setText("录制中")
                    frame = cv2.resize(frame, self.sz)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    self.out.write(frame)
                    self.allFrame += 1
                    self.setBtnAble(False, False, False)
                if self.allFrame == 64:
                    self.setBtnAble(False, True, True)
                    self.label_onTime.clear()
                    th = threading.Thread(target=self.post)
                    th.start()
                    self.out.release()
            cv2.waitKey(1)
            if self.stopEvent.is_set():
                self.stopEvent.clear()
                self.label_screen.clear()
                cv2.destroyAllWindows()
                self.cap.release()

    def captureCamera(self):
        self.label_result.clear()
        if self.capIsNone == False:
            self.capture = True

    def post(self):
        self.allFrame = 0
        self.capture = False
        url = "http://127.0.0.1:8080"
        file = {'video': open('output.mp4', 'rb')}
        upload_data = {
            'totalFrame': 64
        }
        r = requests.post(url, data=upload_data, files=file)
        self.result_list = json.loads(r.text)  # 解码为list数据类型
        self.label_result.setText(r.text)
        # 发送信号
        self.ms.update_date.emit()

    def closeEvent(self, *args, **kwargs):
        if self.capIsNone == False:
            cv2.destroyAllWindows()
            self.cap.release()

    def setBtnAble(self, able_open, able_close, able_post):
        self.btn_open_camera.setEnabled(able_open)
        self.btn_close_camera.setEnabled(able_close)
        self.btn_post.setEnabled(able_post)

    def drawGraph(self):
        # print(type(self.result_list))
        lenth = len(self.result_list)  # result是一个列表，len()返回列表长度
        # print("专注度集合:", self.result_list)
        F = MyFigure(3, 3, 100)
        axes = F.fig.add_subplot(111)
        x = np.arange(0, lenth, 1)  # 表示横坐标x，首、尾、间隔
        # print("专注度集合长度:", lenth)
        # print("x坐标集合:", x)
        # print("type(x坐标集合):", type(x))
        y = np.array(self.result_list)  # 表示f（x）
        # print("y坐标集合:", y)
        # print("type(y坐标集合):", type(y))
        axes.plot(x, y)
        F.fig.suptitle("Result")
        QtWidgets.QGridLayout(self.line_chart_display).addWidget(F)
        #print("如果正常打印曲线图，则显示这句话")

        attention_figure = 0
        total_concentration = 0
        for i in range(lenth):
            attention_figure += self.result_list[i]
            total_concentration += 3
        figure = round(attention_figure / total_concentration * 100)
        figure = int(figure + 0.5)
        self.probar_con_level.setValue(figure)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my = Display()
    my.show()
    sys.exit(app.exec())

