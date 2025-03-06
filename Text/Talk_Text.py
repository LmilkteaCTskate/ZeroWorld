from PyQt5 import QtCore, QtGui, QtWidgets
import threading
from LLM.Text import Talk

class Talk_Text(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(str)
    
    def __init__(self, ui_instance):
        super().__init__()
        self.ui = ui_instance
        self.talk_model = Talk()
        
        # 连接模型信号到处理函数
        self.talk_model.model_output_signal.connect(self._handle_model_output)
        
    def text_run(self):
        """触发对话流程"""
        user_text = self.ui.textEdit.toPlainText().strip()
        
        if not user_text:
            return
        
        # 更新对话框
        self._safe_append_text(f'用户: {user_text}\n')
        self._clear_input()
        
        # 启动处理线程
        threading.Thread(target=self._text_run_thread, args=(user_text,), daemon=True).start()
    
    def _text_run_thread(self, user_text):
        """后台线程执行模型调用"""
        self.talk_model.Talk_model(user_text)
    
    def _handle_model_output(self, text):
        """处理模型输出信号"""
        # 告知主线程有新文本需要更新
        self.update_signal.emit(text)
    
    def _safe_append_text(self, text):
        """线程安全的文本追加"""
        QtCore.QMetaObject.invokeMethod(
            self.ui.textBrowser,
            "append",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, text),
        )
    
    def _clear_input(self):
        """清空输入框"""
        QtCore.QMetaObject.invokeMethod(
            self.ui.textEdit,
            "clear",
            QtCore.Qt.QueuedConnection
        )
