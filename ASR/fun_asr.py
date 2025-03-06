import sys 
sys.path.append("D:/ASR_LLX_TTS/ASR/Human")
import numpy as np
import torch
import pyaudio
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from collections import deque
import os
import time
import threading
import socket
import select
import soundfile as sf  # 新增音频保存库


# -------------------------- 配置参数 --------------------------
SAVE_DIR = "D:/ASR_LLX_TTS/ASR/Human/ASR/Uploda_Audio"
MODEL_DIR = "D:/ASR_LLX_TTS/ASR/Human/ASR/models/SeACoParaformer"
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024 * 4
BUFFER_SECONDS = 1.0  # 缩短缓冲区以降低延迟
HOTWORDS = ["支付宝", "健康码"]
DEVICE_INDEX = 1

# -------------------------- 加载本地模型 --------------------------
def load_local_model():
    """加载模型并尝试量化"""
    asr_pipeline = pipeline(
        task=Tasks.auto_speech_recognition,
        model=MODEL_DIR,
        model_revision=None,
        hotwords=HOTWORDS,
        hotword_weight=15.0,
        beam_size=2,  # 减小束宽
        max_end_silence_time=300,  # 减少静音等待
        ngpu=0
    )
    
    # 尝试量化（如果模型支持）
    if hasattr(asr_pipeline.model, 'model') and isinstance(asr_pipeline.model.model, torch.nn.Module):
        quantized_model = torch.quantization.quantize_dynamic(
            asr_pipeline.model.model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
        asr_pipeline.model.model = quantized_model
    return asr_pipeline

# -------------------------- 音频流处理类 --------------------------
class RealtimeASR:
    def __init__(self, asr_pipeline):
        self.asr = asr_pipeline
        self.audio_buffer = deque(maxlen=int(SAMPLE_RATE * BUFFER_SECONDS))
        self.p = pyaudio.PyAudio()
        self.stream = None
        
        # 新增Socket服务器配置
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', 25565))
        self.server_socket.listen(5)
        self.client_sockets = []
        print("ASR服务已启动，等待客户端连接...")

    def _handle_clients(self):
        """处理客户端连接"""
        while True:
            read_sockets, _, _ = select.select([self.server_socket] + self.client_sockets, [], [], 0.1)
            for sock in read_sockets:
                if sock == self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    print(f"新的客户端连接: {addr}")
                    self.client_sockets.append(client_socket)
                else:
                    try:
                        data = sock.recv(1024)
                        if not data:
                            print(f"客户端断开连接: {sock.getpeername()}")
                            self.client_sockets.remove(sock)
                            sock.close()
                        else:
                            print(f"接收到客户端数据: {data}（未处理）")
                    except ConnectionResetError as e:
                        print(f"客户端异常断开: {e}")
                        self.client_sockets.remove(sock)
                        sock.close()
                    except Exception as e:
                        print(f"处理客户端连接错误: {e}")
                        self.client_sockets.remove(sock)
                        sock.close()

    def start(self):
        """启动服务"""
        # 启动客户端处理线程
        client_thread = threading.Thread(target=self._handle_clients, daemon=True)
        client_thread.start()
        
        # 修复音频流参数
        self.stream = self.p.open(
            format=pyaudio.paInt16,        
            channels=1,                    
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=DEVICE_INDEX,
            stream_callback=self._audio_callback  # 回调函数
        )
        
        try:
            while self.stream.is_active():
                result = self._process_buffer()
                # 向所有客户端发送结果
                if result and self.client_sockets:
                    for client in self.client_sockets[:]:  # 使用副本遍历
                        try:
                            client.send(result.encode('utf-8') + b'\n')
                        except:
                            self.client_sockets.remove(client)
                            client.close()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)
        audio_chunk = audio_chunk.astype(np.float32) / 32768.0
        self.audio_buffer.extend(audio_chunk)
        return (None, pyaudio.paContinue)

    def _process_buffer(self):
        if len(self.audio_buffer) < SAMPLE_RATE * 0.5:
            return None
        audio_segment = np.array(self.audio_buffer)[-int(SAMPLE_RATE * BUFFER_SECONDS):]
        db = 10 * np.log10(np.mean(audio_segment**3) + 1e-8)
    
        # 调整静音阈值（提高到-40dB）
        if db < -40:
            return None
        
        result = self.asr(audio_segment)
        # 修正结果提取逻辑
        if isinstance(result, dict) and 'text' in result:
            text = result['text']
        elif isinstance(result, list) and len(result) > 0 and 'text' in result[0]:
            text = result[0]['text']
        else:
            text = str(result)
        
        print(f"\r实时结果: {text}", " " * 20, end='', flush=True)
        return text  # 确保返回文本字符串

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        print("\n服务已停止")

if __name__ == "__main__":
    asr_pipeline = load_local_model()
    processor = RealtimeASR(asr_pipeline)
    processor.start()