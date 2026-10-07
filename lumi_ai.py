"""Lumi AI Client — streaming, vision, multi-provider, continue (UTF-8 fixed)"""
import json
import requests

from lumi_config import (
    API_KEYS, MODELS, MODES, DEFAULT_MODE,
    GROQ_FALLBACK_MODELS, GEMINI_FALLBACK_MODELS,
    TIMEOUT, OLLAMA_URL, USER_AGENT, SYSTEM_PROMPT,
)

OPENAI_COMPAT = {
    "groq":       "https://api.groq.com/openai/v1/chat/completions",
    "openai":     "https://api.openai.com/v1/chat/completions",
    "deepseek":   "https://api.deepseek.com/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}

CONTINUE_PROMPT = ("[Tiếp tục viết từ chỗ bị ngắt. KHÔNG lặp lại nội dung đã viết. "
                   "Viết tiếp liền mạch, giữ đúng văn phong.]")


class LumiClient:
    def __init__(self, provider="groq", mode=DEFAULT_MODE, system_prompt=SYSTEM_PROMPT):
        self.provider = provider
        self.mode = mode
        self.system_prompt = system_prompt
        self.history = []

    def reset(self): self.history.clear()
    def set_mode(self, mode): self.mode = mode
    def set_provider(self, p): self.provider = p

    def stream_chat(self, text, image_b64=None, image_mime="image/jpeg"):
        content = text
        if image_b64:
            content = [
                {"type": "text", "text": text},
                {"type": "image_url",
                 "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}},
            ]
        self.history.append({"role": "user", "content": content})
        try:
            yield from self._dispatch()
        except Exception:
            self.history.pop()
            raise

    def continue_from(self, partial_text):
        self.history.append({"role": "assistant", "content": partial_text})
        self.history.append({"role": "user", "content": CONTINUE_PROMPT})
        try:
            yield from self._dispatch()
        except Exception:
            self.history.pop(); self.history.pop()
            raise

    def _dispatch(self):
        if self.provider in OPENAI_COMPAT: yield from self._stream_openai()
        elif self.provider == "gemini":    yield from self._stream_gemini()
        elif self.provider == "ollama":    yield from self._stream_ollama()
        else: raise RuntimeError(f"Provider '{self.provider}' chưa hỗ trợ.")

    def _s(self): return MODES.get(self.mode, MODES[DEFAULT_MODE])

    def _headers(self):
        h = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Accept-Charset": "utf-8",
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {API_KEYS.get(self.provider, '')}",
        }
        if self.provider == "openrouter":
            h["HTTP-Referer"] = "http://localhost"
            h["X-Title"] = "Lumi Assistant"
        return h

    def _messages(self):
        return [{"role": "system", "content": self.system_prompt}] + self.history

    def _stream_openai(self):
        url = OPENAI_COMPAT[self.provider]
        s = self._s()
        if self.provider == "groq":
            preferred = s.get("groq_model")
            models = ([preferred] if preferred else []) + \
                     [m for m in GROQ_FALLBACK_MODELS if m != preferred]
        else:
            models = [MODELS.get(self.provider)]

        last_err = None
        for model in models:
            if not model: continue
            try:
                payload = {
                    "model": model,
                    "messages": self._messages(),
                    "temperature": s["temp"],
                    "max_tokens": s["max_tokens"],
                    "stream": True,
                }
                with requests.post(url, headers=self._headers(), json=payload,
                                   timeout=TIMEOUT, stream=True) as r:
                    if r.status_code != 200:
                        last_err = f"[{model}] HTTP {r.status_code}: {r.text[:180]}"
                        continue
                    r.encoding = "utf-8"
                    finish = None
                    for raw in r.iter_lines(decode_unicode=True):
                        if not raw or not raw.startswith("data: "): continue
                        data = raw[6:].strip()
                        if data == "[DONE]": break
                        try: chunk = json.loads(data)
                        except Exception: continue
                        ch = chunk.get("choices", [{}])[0]
                        delta = ch.get("delta", {}).get("content") or ""
                        if delta: yield delta, None
                        if ch.get("finish_reason"): finish = ch["finish_reason"]
                    yield "", (finish or "stop")
                    return
            except Exception as e:
                last_err = f"[{model}] {e}"
        raise RuntimeError(f"Tất cả model thất bại. Lỗi cuối: {last_err}")

    def _stream_gemini(self):
        key = API_KEYS.get("gemini", "")
        if not key: raise RuntimeError("Chưa có Gemini API key.")
        s = self._s()
        contents = []
        for m in self.history:
            role = "user" if m["role"] == "user" else "model"
            c = m["content"]
            if isinstance(c, list):
                parts = []
                for item in c:
                    if item["type"] == "text":
                        parts.append({"text": item["text"]})
                    elif item["type"] == "image_url":
                        url = item["image_url"]["url"]
                        if ";base64," in url:
                            mime, b64 = url.split(";base64,", 1)
                            parts.append({"inline_data": {
                                "mime_type": mime.replace("data:", ""),
                                "data": b64}})
                contents.append({"role": role, "parts": parts})
            else:
                contents.append({"role": role, "parts": [{"text": c}]})

        last_err = None
        for model in GEMINI_FALLBACK_MODELS:
            try:
                url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                       f"{model}:streamGenerateContent?alt=sse&key={key}")
                payload = {
                    "contents": contents,
                    "systemInstruction": {"parts": [{"text": self.system_prompt}]},
                    "generationConfig": {"temperature": s["temp"],
                                          "maxOutputTokens": s["max_tokens"]},
                }
                with requests.post(url, json=payload, timeout=TIMEOUT, stream=True,
                                   headers={"Content-Type": "application/json",
                                            "Accept-Charset": "utf-8",
                                            "User-Agent": USER_AGENT}) as r:
                    if r.status_code != 200:
                        last_err = f"[{model}] HTTP {r.status_code}: {r.text[:180]}"
                        continue
                    r.encoding = "utf-8"
                    finish = None
                    for raw in r.iter_lines(decode_unicode=True):
                        if not raw or not raw.startswith("data: "): continue
                        try: chunk = json.loads(raw[6:].strip())
                        except Exception: continue
                        for cand in chunk.get("candidates", []):
                            for p in cand.get("content", {}).get("parts", []):
                                if "text" in p: yield p["text"], None
                            if cand.get("finishReason"):
                                fr = cand["finishReason"]
                                finish = "length" if fr == "MAX_TOKENS" else fr.lower()
                    yield "", (finish or "stop")
                    return
            except Exception as e:
                last_err = f"[{model}] {e}"
        raise RuntimeError(f"Gemini thất bại: {last_err}")

    def _stream_ollama(self):
        payload = {
            "model": MODELS.get("ollama", "llama3.2"),
            "messages": self._messages(),
            "stream": True,
        }
        with requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                           timeout=TIMEOUT, stream=True) as r:
            if r.status_code != 200:
                raise RuntimeError(f"Ollama HTTP {r.status_code}: {r.text[:180]}")
            r.encoding = "utf-8"
            finish = None
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                try: chunk = json.loads(raw)
                except Exception: continue
                msg = chunk.get("message", {})
                if msg.get("content"): yield msg["content"], None
                if chunk.get("done"): finish = "stop"
            yield "", (finish or "stop")