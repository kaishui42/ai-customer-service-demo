import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

# DeepSeek / 大模型 API 配置（Demo 默认走模拟模式）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "") or DEEPSEEK_API_KEY
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_MOCK_MODE = os.getenv("LLM_MOCK_MODE", "true").lower() == "true"

# 本地知识文件目录（报价表等）
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
