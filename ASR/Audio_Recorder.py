import socket
import time
import threading

class AudioRecorderController:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None
        self.result_signal = None
        self.socket = None  # 新增socket引用

    def _task(self):
        buffer = ""
        while not self.stop_event.is_set():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('localhost', 25565))
                self.socket = s
                print("已连接ASR服务")
                buffer = ""
                while not self.stop_event.is_set():
                    data = s.recv(1024)
                    if not data:
                        break
                    buffer += data.decode('utf-8', errors='ignore')
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if self.result_signal:
                            self.result_signal.emit(line.strip())
                            print(f"[DEBUG] 发送信号: {line.strip()}")
            except Exception as e:
                print(f"连接异常: {str(e)}")
            finally:
                if self.socket:
                    self.socket.close()
                    self.socket = None

    def force_stop(self):  # <-- 新增强制停止方法
        self.stop_event.set()
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)

    def start(self, result_signal):
        self.stop_event.clear()
        self.result_signal = result_signal
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._task,daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

audio_controller = AudioRecorderController()
