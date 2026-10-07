from pathlib import Path
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
RUNTIME_DIR = ROOT / 'runtime'
load_dotenv(ROOT / '.env')

GDELT_URL = 'https://api.gdeltproject.org/api/v2/doc/doc'
GOOGLE_NEWS_RSS = 'https://news.google.com/rss/search'
NEWSAPI_URL = 'https://newsapi.org/v2/everything'

SENTIMENT_MODEL = os.getenv('SENTIMENT_MODEL', 'ProsusAI/finbert')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_URL = os.getenv('GROQ_URL', 'https://api.groq.com/openai/v1/chat/completions')
GROQ_MODELS = tuple(
    model.strip()
    for model in os.getenv('GROQ_MODELS', 'openai/gpt-oss-120b,openai/gpt-oss-20b').split(',')
    if model.strip()
)

DEFAULT_GDELT_QUERY = '(bank OR markets OR inflation OR rates OR recession OR sanctions OR merger OR default OR liquidity)'
DEFAULT_RSS_QUERY = 'banking OR inflation OR recession OR sanctions OR credit when:1d'

MAX_TEXT_CHARS = 3500
IMPACT_MODEL_FILE = ROOT / 'models' / 'impact_xgb.json'
IMPACT_CALIBRATION_FILE = ROOT / 'models' / 'impact_calibration.json'
