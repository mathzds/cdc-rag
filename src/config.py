from pathlib import Path

CDC_URL = "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "bge-m3"
CHAT_MODEL = "qwen3:8b"
THINK = False
NUM_CTX = 8192
TOP_K = 5
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "rag.db"
