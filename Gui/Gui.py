# Gui.py
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject
import sys
sys.path.append("D:/ASR_LLX_TTS/ASR/Human")
import threading
import importlib
from Text.Talk_Text import Talk_Text
from ASR import Audio_Recorder

class UI_Form:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Form")
        MainWindow.resize(1124, 637)
        
        # 初始化UI组件
        self._setup_ui_components(MainWindow)
        
        # 延迟加载标记
        self._modules_loaded = {
            'tts': False,
            'asr': False,
            'text': False
        }
        
        # 预加载计时器
        self._preload_timer = QtCore.QTimer()
        self._preload_timer.timeout.connect(self._async_preload)
        self._preload_timer.start(500)  # 窗口显示500ms后开始预加载

        # 基础信号连接
        self.pushButton.clicked.connect(self._on_send_clicked)
        self.pushButton_2.clicked.connect(self._on_asr_toggle)

    def _setup_ui_components(self, MainWindow):
        """初始化所有UI组件"""
        # 对话模型下拉框
        self.comboBox = QtWidgets.QComboBox(MainWindow)
        self.comboBox.setGeometry(QtCore.QRect(60, 440, 161, 41))
        self.comboBox.addItem("")
        
        # ASR下拉框
        self.comboBox_2 = QtWidgets.QComboBox(MainWindow)
        self.comboBox_2.setGeometry(QtCore.QRect(60, 500, 161, 41))
        self.comboBox_2.addItem("")
        
        # TTS下拉框
        self.comboBox_3 = QtWidgets.QComboBox(MainWindow)
        self.comboBox_3.setGeometry(QtCore.QRect(60, 560, 161, 41))
        self.comboBox_3.addItem("pyttsx3")
        self.comboBox_3.addItem("ChatTTS")
        self.comboBox_3.addItem("Parler-TTS")
        
        # 用户输入框
        self.textEdit = QtWidgets.QTextEdit(MainWindow)
        self.textEdit.setGeometry(QtCore.QRect(300, 530, 661, 71))
        
        # 输入框标签
        self.label = QtWidgets.QLabel(MainWindow)
        self.label.setGeometry(QtCore.QRect(310, 480, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.label.setFont(font)
        
        # 发送按钮
        self.pushButton = QtWidgets.QPushButton(MainWindow)
        self.pushButton.setGeometry(QtCore.QRect(970, 530, 81, 71))
        
        # 对话记录显示
        self.textBrowser = QtWidgets.QTextBrowser(MainWindow)
        self.textBrowser.setGeometry(QtCore.QRect(300, 110, 671, 371))
        self.textBrowser.setWordWrapMode(QtGui.QTextOption.WordWrap)

        # 实时识别按钮
        self.pushButton_2 = QtWidgets.QPushButton(MainWindow)
        self.pushButton_2.setGeometry(QtCore.QRect(60, 380, 161, 51))
        self.pushButton_2.setObjectName("pushButton_2")

        # #按住说话按钮
        # self.pushButton_3 = QtWidgets.QPushButton(MainWindow)
        # self.pushButton_3.setGeometry(QtCore.QRect(60, 320, 161, 51))
        # self.pushButton_3.setObjectName("pushButton_3")
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "摸鱼助手"))
        
        #对话模型
        self.comboBox.setItemText(0, _translate("MainWindow", "Deepseek"))

        #语音识别
        self.comboBox_2.setItemText(0, _translate("MainWindow", "FunASR"))

        #TTS选择
        self.comboBox_3.setItemText(0, _translate("MainWindow", "pyttsx3"))
        self.comboBox_3.setItemText(1, _translate("MainWindow", "ChatTTS"))
        self.comboBox_3.setItemText(2, _translate("MainWindow", "Parler-TTS"))

        #用户输入
        self.label.setText(_translate("MainWindow", "输入框"))
        self.pushButton.setText(_translate("MainWindow", "发送"))
        
        #实时识别按钮
        self.pushButton_2.setText(_translate("Form", "开启实时识别"))


    def _async_preload(self):
        """后台预加载核心模块"""
        if not hasattr(self, '_preload_thread'):
            self._preload_thread = threading.Thread(
                target=self._load_background_modules,
                daemon=True
            )
            self._preload_thread.start()
            self._preload_timer.stop()

    def _load_background_modules(self):
        """实际加载但不初始化模块"""
        importlib.import_module('ASR.Audio_Recorder')
        importlib.import_module('Text.Talk_Text')

    def _on_send_clicked(self):
        """发送按钮点击处理"""
        if not self._modules_loaded['text']:
            self.talk_text = Talk_Text(self)
            self.talk_text.update_signal.connect(self.update_model_output)
            self._modules_loaded['text'] = True
        
        user_text = self.textEdit.toPlainText().strip()
        if user_text:
            self.textBrowser.append(f'用户: {user_text}\n')
            self.textEdit.clear()
            threading.Thread(
                target=self.talk_text._text_run_thread,
                args=(user_text,),
                daemon=True
            ).start()

    def _on_asr_toggle(self):
        """ASR开关处理"""
        if not self._modules_loaded['asr']:
            self.Audio_Recorder = Audio_Recorder
            self.comm = Communication()
            self.comm.update_asr.connect(self.handle_asr_result)
            self._modules_loaded['asr'] = True
        
        if self.pushButton_2.text() == "开启实时识别":
            self.pushButton_2.setText("关闭实时识别")
            self.Audio_Recorder.audio_controller.start(self.comm.update_asr)
        else:
            self.pushButton_2.setText("开启实时识别")
            self.Audio_Recorder.audio_controller.stop()

    def update_model_output(self, Model_text):
        # 获取当前内容
        current_text = self.textBrowser.toPlainText()
        # 更新内容
        updated_text = current_text + Model_text
        self.textBrowser.setText(updated_text)
        
         # 滚动到底部
        self.textBrowser.verticalScrollBar().setValue(self.textBrowser.verticalScrollBar().maximum())

    def handle_asr_result(self, text):
        """处理ASR识别结果"""
        if text:
            self.textEdit.setText(text)
            self.textEdit.repaint()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = UI_Form()
        self.ui.setupUi(self)
        self._services_initialized = False

    def showEvent(self, event):
        """窗口显示后触发后台初始化"""
        if not self._services_initialized:
            QtCore.QTimer.singleShot(100, self._init_background_services)
            self._services_initialized = True
        super().showEvent(event)

    def _init_background_services(self):
        """后台初始化"""
        self.ui._async_preload()
    

class Communication(QObject):
    update_asr = pyqtSignal(str)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())