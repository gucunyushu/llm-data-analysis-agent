"""配置：从环境变量 / .env 读取 LLM 后端，支持 DeepSeek / Qwen / GLM 等 OpenAI 兼容接口。"""
import os
from dotenv import load_dotenv

load_dotenv()  # 读取项目根目录的 .env（如果存在）

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")


def check_config():
    if not API_KEY:
        raise RuntimeError("未设置 LLM_API_KEY：请复制 .env.example 为 .env 并填入你的 API Key")
