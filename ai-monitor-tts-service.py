# core/voice/tts_service.py
"""
TTS语音服务 - 文本转语音功能
支持多种语音引擎和情感化语音
"""

import os
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
import tempfile
import wave
import numpy as np
from pathlib import Path
import logging
import platform
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VoiceType(Enum):
    """语音类型"""
    ALLOY = "alloy"           # 中性
    ECHO = "echo"             # 温暖
    FABLE = "fable"           # 故事
    ONYX = "onyx"             # 深沉
    NOVA = "nova"             # 活泼
    SHIMMER = "shimmer"       # 清晰

@dataclass
class VoiceConfig:
    """语音配置"""
    voice_type: VoiceType
    language: str = "zh-CN"
    gender: str = "neutral"
    age: str = "adult"
    pitch: float = 1.0        # 音调 0.5-2.0
    rate: float = 1.0         # 语速 0.5-2.0
    volume: float = 1.0       # 音量 0.0-1.0

class TTSService:
    """TTS服务主类"""
    
    def __init__(self):
        self.platform = platform.system()
        self.engines = self._init_engines()
        self.current_engine = self._select_best_engine()
        self.cache_dir = Path("cache/tts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _init_engines(self) -> Dict[str, Any]:
        """初始化可用的TTS引擎"""
        engines = {}
        
        # macOS原生语音
        if self.platform == "Darwin":
            engines["macos"] = MacOSTTS()
        
        # Edge TTS（跨平台）
        try:
            import edge_tts
            engines["edge"] = EdgeTTS()
        except ImportError:
            logger.warning("Edge TTS not available")
        
        # Pyttsx3（跨平台）
        try:
            import pyttsx3
            engines["pyttsx3"] = Pyttsx3TTS()
        except ImportError:
            logger.warning("Pyttsx3 not available")
        
        return engines
    
    def _select_best_engine(self) -> str:
        """选择最佳的TTS引擎"""
        if "macos" in self.engines and self.platform == "Darwin":
            return "macos"
        elif "edge" in self.engines:
            return "edge"
        elif "pyttsx3" in self.engines:
            return "pyttsx3"
        else:
            raise RuntimeError("No TTS engine available")
    
    async def synthesize(self, 
                        text: str, 
                        voice: str = "alloy",
                        speed: float = 1.0,
                        output_format: str = "mp3") -> bytes:
        """合成语音"""
        # 生成缓存键
        cache_key = self._generate_cache_key(text, voice, speed)
        cache_file = self.cache_dir / f"{cache_key}.{output_format}"
        
        # 检查缓存
        if cache_file.exists():
            logger.debug(f"TTS cache hit: {cache_key}")
            return cache_file.read_bytes()
        
        # 选择引擎
        engine = self.engines.get(self.current_engine)
        if not engine:
            raise ValueError(f"Engine {self.current_engine} not available")
        
        # 合成语音
        logger.info(f"Synthesizing speech with {self.current_engine}")
        audio_data = await engine.synthesize(text, voice, speed)
        
        # 转换格式
        if output_format != "wav":
            audio_data = await self._convert_audio(audio_data, "wav", output_format)
        
        # 缓存结果
        cache_file.write_bytes(audio_data)
        
        return audio_data
    
    async def synthesize_with_emotion(self,
                                    text: str,
                                    emotion: str = "neutral",
                                    voice: str = "alloy",
                                    intensity: float = 1.0) -> bytes:
        """带情感的语音合成"""
        # 根据情感调整语音参数
        voice_config = self._get_emotion_config(emotion, intensity)
        
        # 修改文本以增强情感表达
        enhanced_text = self._enhance_text_for_emotion(text, emotion)
        
        # 合成语音
        return await self.synthesize(
            enhanced_text,
            voice=voice,
            speed=voice_config.rate
        )
    
    def _get_emotion_config(self, emotion: str, intensity: float) -> VoiceConfig:
        """获取情感配置"""
        emotion_configs = {
            "happy": VoiceConfig(
                voice_type=VoiceType.NOVA,
                pitch=1.1 * intensity,
                rate=1.1 * intensity,
                volume=1.0
            ),
            "sad": VoiceConfig(
                voice_type=VoiceType.ECHO,
                pitch=0.9 / intensity,
                rate=0.9 / intensity,
                volume=0.8
            ),
            "angry": VoiceConfig(
                voice_type=VoiceType.ONYX,
                pitch=1.2 * intensity,
                rate=1.2 * intensity,
                volume=1.2
            ),
            "calm": VoiceConfig(
                voice_type=VoiceType.ALLOY,
                pitch=1.0,
                rate=0.9,
                volume=0.9
            ),
            "excited": VoiceConfig(
                voice_type=VoiceType.SHIMMER,
                pitch=1.3 * intensity,
                rate=1.3 * intensity,
                volume=1.1
            )
        }
        
        return emotion_configs.get(emotion, VoiceConfig(voice_type=VoiceType.ALLOY))
    
    def _enhance_text_for_emotion(self, text: str, emotion: str) -> str:
        """增强文本的情感表达"""
        # 这里可以添加SSML标记或其他处理
        # 简单示例：为不同情感添加标点
        enhancements = {
            "happy": lambda t: t.replace("。", "！").replace("，", "，"),
            "sad": lambda t: t.replace("。", "...").replace("！", "..."),
            "angry": lambda t: t.upper().replace("。", "！！"),
            "excited": lambda t: t.replace("。", "！！").replace("，", "！")
        }
        
        enhancer = enhancements.get(emotion)
        return enhancer(text) if enhancer else text
    
    async def _convert_audio(self, audio_data: bytes, from_format: str, to_format: str) -> bytes:
        """转换音频格式"""
        with tempfile.NamedTemporaryFile(suffix=f".{from_format}", delete=False) as tmp_input:
            tmp_input.write(audio_data)
            tmp_input_path = tmp_input.name
        
        tmp_output_path = tmp_input_path.replace(f".{from_format}", f".{to_format}")
        
        try:
            # 使用ffmpeg转换
            cmd = [
                "ffmpeg", "-i", tmp_input_path,
                "-y",  # 覆盖输出文件
                tmp_output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError("Audio conversion failed")
            
            with open(tmp_output_path, 'rb') as f:
                converted_data = f.read()
            
            return converted_data
            
        finally:
            # 清理临时文件
            for path in [tmp_input_path, tmp_output_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def _generate_cache_key(self, text: str, voice: str, speed: float) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{text}:{voice}:{speed}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def list_voices(self) -> List[Dict[str, str]]:
        """列出可用的语音"""
        engine = self.engines.get(self.current_engine)
        if engine:
            return engine.list_voices()
        return []
    
    async def stream_synthesis(self, text: str, voice: str = "alloy", chunk_size: int = 1024):
        """流式语音合成"""
        # 先完整合成
        audio_data = await self.synthesize(text, voice)
        
        # 分块返回
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

class MacOSTTS:
    """macOS原生TTS引擎"""
    
    def __init__(self):
        self.voices = self._get_system_voices()
    
    def _get_system_voices(self) -> Dict[str, str]:
        """获取系统语音列表"""
        try:
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True
            )
            
            voices = {}
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    voice_name = parts[0]
                    lang = parts[1]
                    voices[voice_name] = lang
            
            return voices
        except Exception as e:
            logger.error(f"Failed to get system voices: {e}")
            return {}
    
    async def synthesize(self, text: str, voice: str = "Ting-Ting", speed: float = 1.0) -> bytes:
        """使用macOS say命令合成语音"""
        # 映射语音
        voice_map = {
            "alloy": "Samantha",
            "echo": "Alex",
            "fable": "Victoria",
            "onyx": "Fred",
            "nova": "Ting-Ting",
            "shimmer": "Karen"
        }
        
        system_voice = voice_map.get(voice, "Ting-Ting")
        
        # 如果是中文，使用中文语音
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            system_voice = "Ting-Ting"
        
        # 计算语速（say命令的速率参数）
        rate = int(175 * speed)  # 默认175词/分钟
        
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 使用say命令生成音频
            cmd = [
                "say",
                "-v", system_voice,
                "-r", str(rate),
                "-o", tmp_path,
                text
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError("TTS synthesis failed")
            
            # 转换为WAV格式
            wav_path = tmp_path.replace(".aiff", ".wav")
            
            convert_cmd = [
                "afconvert", "-f", "WAVE", "-d", "LEI16",
                tmp_path, wav_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *convert_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await process.communicate()
            
            with open(wav_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            # 清理临时文件
            for path in [tmp_path, wav_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def list_voices(self) -> List[Dict[str, str]]:
        """列出可用语音"""
        voices = []
        for name, lang in self.voices.items():
            voices.append({
                "name": name,
                "language": lang,
                "gender": "unknown"
            })
        return voices

class EdgeTTS:
    """Edge TTS引擎"""
    
    def __init__(self):
        import edge_tts
        self.edge_tts = edge_tts
    
    async def synthesize(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural", speed: float = 1.0) -> bytes:
        """使用Edge TTS合成语音"""
        # 映射语音
        voice_map = {
            "alloy": "zh-CN-YunxiNeural",
            "echo": "zh-CN-YunjianNeural",
            "fable": "zh-CN-XiaoyiNeural",
            "onyx": "zh-CN-YunyangNeural",
            "nova": "zh-CN-XiaoxiaoNeural",
            "shimmer": "zh-CN-XiaoxuanNeural"
        }
        
        edge_voice = voice_map.get(voice, "zh-CN-XiaoxiaoNeural")
        
        # 调整语速
        rate = f"{int((speed - 1) * 100):+d}%"
        
        communicate = self.edge_tts.Communicate(text, edge_voice, rate=rate)
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            await communicate.save(tmp_path)
            
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def list_voices(self) -> List[Dict[str, str]]:
        """列出可用语音"""
        # Edge TTS有很多语音，这里只列出中文的
        return [
            {"name": "zh-CN-XiaoxiaoNeural", "language": "zh-CN", "gender": "female"},
            {"name": "zh-CN-YunyangNeural", "language": "zh-CN", "gender": "male"},
            {"name": "zh-CN-XiaoyiNeural", "language": "zh-CN", "gender": "female"},
            {"name": "zh-CN-YunjianNeural", "language": "zh-CN", "gender": "male"},
            {"name": "zh-CN-XiaoxuanNeural", "language": "zh-CN", "gender": "female"},
            {"name": "zh-CN-YunxiNeural", "language": "zh-CN", "gender": "male"}
        ]

class Pyttsx3TTS:
    """Pyttsx3 TTS引擎"""
    
    def __init__(self):
        import pyttsx3
        self.engine = pyttsx3.init()
    
    async def synthesize(self, text: str, voice: str = "default", speed: float = 1.0) -> bytes:
        """使用pyttsx3合成语音"""
        # 设置语速
        self.engine.setProperty('rate', 150 * speed)
        
        # 设置音量
        self.engine.setProperty('volume', 1.0)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 保存到文件
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()
            
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def list_voices(self) -> List[Dict[str, str]]:
        """列出可用语音"""
        voices = []
        for voice in self.engine.getProperty('voices'):
            voices.append({
                "name": voice.id,
                "language": voice.languages[0] if voice.languages else "unknown",
                "gender": voice.gender if hasattr(voice, 'gender') else "unknown"
            })
        return voices

# 音频处理工具
class AudioProcessor:
    """音频处理器"""
    
    @staticmethod
    def adjust_speed(audio_data: bytes, speed_factor: float) -> bytes:
        """调整音频速度"""
        # 使用numpy处理音频
        with wave.open(io.BytesIO(audio_data), 'rb') as wav_in:
            params = wav_in.getparams()
            frames = wav_in.readframes(params.nframes)
        
        # 转换为numpy数组
        audio_array = np.frombuffer(frames, dtype=np.int16)
        
        # 重采样调整速度
        indices = np.round(np.arange(0, len(audio_array), speed_factor)).astype(int)
        indices = indices[indices < len(audio_array)]
        resampled = audio_array[indices]
        
        # 转换回bytes
        with io.BytesIO() as output:
            with wave.open(output, 'wb') as wav_out:
                wav_out.setparams(params)
                wav_out.writeframes(resampled.tobytes())
            
            return output.getvalue()
    
    @staticmethod
    def add_silence(audio_data: bytes, duration_ms: int, position: str = "end") -> bytes:
        """添加静音"""
        with wave.open(io.BytesIO(audio_data), 'rb') as wav_in:
            params = wav_in.getparams()
            frames = wav_in.readframes(params.nframes)
            
        # 生成静音
        silence_samples = int(params.framerate * duration_ms / 1000)
        silence = np.zeros(silence_samples * params.nchannels, dtype=np.int16)
        
        # 合并音频
        audio_array = np.frombuffer(frames, dtype=np.int16)
        
        if position == "start":
            combined = np.concatenate([silence, audio_array])
        elif position == "end":
            combined = np.concatenate([audio_array, silence])
        else:  # both
            combined = np.concatenate([silence, audio_array, silence])
        
        # 转换回bytes
        with io.BytesIO() as output:
            with wave.open(output, 'wb') as wav_out:
                wav_out.setparams(params)
                wav_out.writeframes(combined.tobytes())
            
            return output.getvalue()