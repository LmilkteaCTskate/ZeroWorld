import sys
import re
from threading import Lock
sys.path.append("D:/ASR_LLX_TTS/ASR/Human")
from ollama import Client
from PyQt5.QtCore import pyqtSignal, QObject
from TTS.TTSx3 import async_stream_tts, stop_tts

class Talk(QObject):
    model_output_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.text_buffer = ""
        self.buffer_lock = Lock()
        self.is_streaming = False

    def Talk_model(self, user_text):
        client = Client(host='http://localhost:11434')
        stream = client.chat(
            model='deepseek-r1:1.5b',
            messages=[{'role': 'user', 'content': user_text}],
            stream=True
        )

        self.is_streaming = True
        stop_tts()  # 清除之前的播放

        for chunk in stream:
            if not self.is_streaming:
                break
                
            Model_text = chunk['message']['content']
            Model_text = re.sub(r'[\n\r\t<sep/><think>]', '', Model_text).strip()
            Model_text = re.sub(r'\s{10,}', ' ', Model_text)

            with self.buffer_lock:
                self.text_buffer += Model_text
                sentences = re.split(r'(?<=[.!?。！？])', self.text_buffer)
                
                if len(sentences) > 1:
                    for sent in sentences[:-1]:
                        if sent.strip():
                            self.model_output_signal.emit(sent)
                            async_stream_tts(sent)
                    self.text_buffer = sentences[-1]

        if self.is_streaming and self.text_buffer:
            self.model_output_signal.emit(self.text_buffer)
            async_stream_tts(self.text_buffer)
            
    def stop(self):
        self.is_streaming = False
        stop_tts()