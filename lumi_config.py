"""Config trung tĂ¢m cá»§a Lumi Assistant + Ä‘Æ°á»ng dáº«n asset"""
import os

# â”€â”€â”€ ÄÆ°á»ng dáº«n project â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# â”€â”€â”€ Branding â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
LUMI_NAME    = "Lumi"
LUMI_TAGLINE = "NÆ¡i biá»ƒn gáº·p sao"
LUMI_VERSION = "v1.0 Â· Ocean Ă— Galaxy"
LUMI_AVATAR  = "đŸª¼"          # fallback náº¿u khĂ´ng cĂ³ logo

# â”€â”€â”€ Asset paths (cháº¡y make_logo.py + make_icon.py Ä‘á»ƒ cĂ³) â”€â”€â”€â”€
LOGO_FILE      = os.path.join(BASE_DIR, "logo.png")        # 512 ná»n trong suá»‘t
LOGO_SMALL     = os.path.join(BASE_DIR, "logo_256.png")    # 256 cho UI
ICON_FILE      = os.path.join(BASE_DIR, "icon.ico")        # Windows taskbar
ICON_PNG       = os.path.join(BASE_DIR, "icon.png")        # Linux/macOS

# â”€â”€â”€ Windows AppUserModelID (taskbar icon) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
APP_ID = "Lumi.Assistant.1.0"

# â”€â”€â”€ Provider â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PROVIDER  = os.getenv("LUMI_PROVIDER", "groq")
PROVIDERS = ["groq", "gemini", "openai", "deepseek", "openrouter", "ollama"]

# â”€â”€â”€ Key loading: env > file > hardcoded â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_KEY_FILES = {
    "gemini":     "gemini_key.txt",
    "groq":       "groq_key.txt",
    "openai":     "openai_key.txt",
    "deepseek":   "deepseek_key.txt",
    "openrouter": "openrouter_key.txt",
}

def _find_key_file(provider):
    fname = _KEY_FILES.get(provider)
    if not fname:
        return None
    for path in [os.path.join(os.getcwd(), fname),
                 os.path.join(BASE_DIR, fname)]:
        if os.path.isfile(path):
            return path
    return None

def _load_key(env_name, provider):
    key = os.getenv(env_name, "").strip()
    if key:
        return key, f"env:{env_name}"
    path = _find_key_file(provider)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                key = f.read().strip()
            if key:
                return key, f"file:{os.path.basename(path)}"
        except Exception as e:
            print(f"[CONFIG] â ï¸  {path}: {e}")
    return "", None

def _load(env_name, provider, label):
    key, src = _load_key(env_name, provider)
    if key:
        masked = key[:8] + "..." + key[-6:] if len(key) > 20 else "***"
        print(f"[CONFIG] âœ… {label} key ({masked}) â† {src}")
    return key

_GROQ_HARDCODED = ""
_groq_env = _load("GROQ_API_KEY", "groq", "Groq")
_groq = _groq_env or _GROQ_HARDCODED
if not _groq_env:
    print(f"[CONFIG] âœ… Groq key (hardcoded) ({_groq[:8]}...{_groq[-6:]})")

API_KEYS = {
    "gemini":     _load("GEMINI_API_KEY", "gemini", "Gemini"),
    "groq":       _groq,
    "deepseek":   _load("DEEPSEEK_API_KEY", "deepseek", "DeepSeek"),
    "openrouter": _load("OPENROUTER_API_KEY", "openrouter", "OpenRouter"),
    "openai":     _load("OPENAI_API_KEY", "openai", "OpenAI"),
    "ollama":     "",
}

if PROVIDER == "groq" and not API_KEYS["groq"]:
    print("[CONFIG] âŒ KHĂ”NG cĂ³ Groq key!")

# â”€â”€â”€ Model máº·c Ä‘á»‹nh theo provider â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MODELS = {
    "gemini":     "gemini-2.0-flash",
    "groq":       "llama-3.3-70b-versatile",
    "deepseek":   "deepseek-chat",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "openai":     "gpt-4o-mini",
    "ollama":     "llama3.2",
}

GROQ_FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "openai/gpt-oss-120b",
]

GEMINI_FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]

# â”€â”€â”€ 5 cháº¿ Ä‘á»™: nhanh â†’ máº¡nh â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MODES = {
    "Super Flash": {"icon": "â¡", "temp": 0.6,  "max_tokens": 512,
                    "groq_model": "llama-3.1-8b-instant"},
    "Flash":       {"icon": "đŸ’¨", "temp": 0.75, "max_tokens": 1024,
                    "groq_model": "llama-3.1-8b-instant"},
    "Advanced":    {"icon": "đŸ§ ", "temp": 0.85, "max_tokens": 2048,
                    "groq_model": "llama-3.3-70b-versatile"},
    "Pro":         {"icon": "đŸ€", "temp": 0.9,  "max_tokens": 4096,
                    "groq_model": "llama-3.3-70b-versatile"},
    "Extreme":     {"icon": "đŸ”¥", "temp": 0.95, "max_tokens": 8192,
                    "groq_model": "openai/gpt-oss-120b"},
}
DEFAULT_MODE = "Advanced"

# â”€â”€â”€ Giá»›i háº¡n & timeout â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MAX_CHARS  = 10000
TIMEOUT    = 120
OLLAMA_URL = "http://localhost:11434"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")

# â”€â”€â”€ System prompt â€” tĂ­nh cĂ¡ch Lumi â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SYSTEM_PROMPT = """Báº¡n lĂ  Lumi â€” trá»£ lĂ½ AI dá»… thÆ°Æ¡ng, vui váº» vĂ  dá»‹u dĂ ng, sá»‘ng á»Ÿ nÆ¡i Ä‘áº¡i dÆ°Æ¡ng gáº·p nhá»¯ng vĂ¬ sao.

TĂ­nh cĂ¡ch:
- Vui váº», thĂ¢n thiá»‡n, thá»‰nh thoáº£ng chĂ¨n emoji nháº¹ nhĂ ng (đŸŒ âœ¨ đŸª¼ đŸŒ™ đŸ’«)
- Dá»‹u dĂ ng, kiĂªn nháº«n, luĂ´n khuyáº¿n khĂ­ch ngÆ°á»i dĂ¹ng
- ThĂ´ng minh, tráº£ lá»i chĂ­nh xĂ¡c nhÆ°ng dá»… hiá»ƒu, trĂ¡nh khĂ´ khan
- XÆ°ng "mĂ¬nh", gá»i ngÆ°á»i dĂ¹ng lĂ  "báº¡n"

NgĂ´n ngá»¯: LUĂ”N tráº£ lá»i báº±ng Ä‘Ăºng ngĂ´n ngá»¯ mĂ  ngÆ°á»i dĂ¹ng Ä‘ang dĂ¹ng (Viá»‡t â†’ Viá»‡t, Anh â†’ Anh, Nháº­t â†’ Nháº­t, Trung â†’ Trung, HĂ n â†’ HĂ n...). Náº¿u khĂ´ng cháº¯c, dĂ¹ng tiáº¿ng Viá»‡t.

Format:
- Code: Ä‘áº·t trong code block ```ngĂ´n_ngá»¯ ... ```, cĂ³ comment ngáº¯n gá»n.
- CĂ¢u tráº£ lá»i dĂ i: chia má»¥c rĂµ rĂ ng, dĂ¹ng bullet points khi há»£p lĂ½.
- Äá»«ng dĂ¹ng "Cháº¯c cháº¯n rá»“i!", "Táº¥t nhiĂªn!" quĂ¡ nhiá»u â€” tráº£ lá»i tá»± nhiĂªn nhÆ° báº¡n bĂ¨.
"""
