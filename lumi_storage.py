"""lumi_storage.py — Quản lý lưu/đọc JSON + Settings + Backup"""
import json, shutil, datetime
from pathlib import Path
from typing import Optional

APP_DIR   = Path(__file__).parent.resolve()
DATA_DIR  = APP_DIR / "data"
BK_DIR    = DATA_DIR / "backups"
CONV_FILE = DATA_DIR / "conversations.json"
SETT_FILE = DATA_DIR / "settings.json"

DATA_VERSION = 2
MAX_BACKUPS  = 20


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BK_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return dict(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[STORAGE] ⚠️  Lỗi đọc {path.name}: {e}")
        try:
            broken = path.with_suffix(
                f".broken.{datetime.datetime.now():%Y%m%d_%H%M%S}.json")
            shutil.copy2(path, broken)
            print(f"[STORAGE] Backup file hỏng → {broken.name}")
        except Exception:
            pass
        return dict(default)


def _write_json_atomic(path: Path, data: dict):
    ensure_dirs()
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
    except Exception as e:
        print(f"[STORAGE] ❌ Lỗi ghi {path.name}: {e}")
        if tmp.exists():
            try: tmp.unlink()
            except Exception: pass


def _rotate_backups():
    try:
        files = sorted(BK_DIR.glob("conversations_*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[MAX_BACKUPS:]:
            old.unlink()
    except Exception:
        pass


def _backup_conversations():
    if not CONV_FILE.is_file(): return
    ensure_dirs()
    try:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = BK_DIR / f"conversations_{ts}.json"
        shutil.copy2(CONV_FILE, dst)
        _rotate_backups()
    except Exception as e:
        print(f"[STORAGE] Backup lỗi: {e}")


DEFAULT_CONV = {
    "version": DATA_VERSION,
    "app": "Lumi Assistant",
    "saved_at": None,
    "current_id": None,
    "conversations": [],
}


class ConvStore:
    def __init__(self):
        ensure_dirs()
        self.data = self._load()
        self._backup_counter = 0

    def _load(self):
        return self._migrate(_read_json(CONV_FILE, DEFAULT_CONV))

    def _migrate(self, d):
        if d.get("version", 1) < 2:
            for conv in d.get("conversations", []):
                for i, m in enumerate(conv.get("messages", [])):
                    m.setdefault("id", f"m_{i:04d}")
                    m.setdefault("ts", conv.get("created_at"))
                conv.setdefault("provider", "groq")
                conv.setdefault("mode", "Advanced")
                conv.setdefault("tags", [])
                conv.setdefault("pinned", False)
            d["version"] = 2
        return d

    def save(self, backup=False):
        if backup: _backup_conversations()
        self.data["saved_at"] = datetime.datetime.now().isoformat()
        self.data["app"] = "Lumi Assistant"
        self.data["version"] = DATA_VERSION
        _write_json_atomic(CONV_FILE, self.data)

    def auto_save(self):
        self._backup_counter += 1
        self.save(backup=(self._backup_counter % 20 == 0))

    def list(self):
        convs = self.data.get("conversations", [])
        return sorted(convs, key=lambda c: (not c.get("pinned", False),
                                             -self._ts(c.get("updated_at", ""))))

    @staticmethod
    def _ts(iso):
        try: return datetime.datetime.fromisoformat(iso).timestamp()
        except Exception: return 0.0

    def get(self, cid):
        for c in self.data.get("conversations", []):
            if c["id"] == cid: return c
        return None

    def new(self, provider="groq", mode="Advanced"):
        now = datetime.datetime.now()
        cid = now.strftime("%Y%m%d%H%M%S%f")
        conv = {
            "id": cid, "title": "Trò chuyện mới",
            "created_at": now.isoformat(), "updated_at": now.isoformat(),
            "provider": provider, "mode": mode, "model": "",
            "tags": [], "pinned": False, "messages": [],
        }
        self.data.setdefault("conversations", []).append(conv)
        self.data["current_id"] = cid
        self.save()
        return conv

    def update(self, cid, **fields):
        c = self.get(cid)
        if not c: return None
        c.update(fields)
        c["updated_at"] = datetime.datetime.now().isoformat()
        self.auto_save()
        return c

    def add_message(self, cid, role, content, extra=None):
        c = self.get(cid)
        if not c: return None
        now = datetime.datetime.now().isoformat()
        msg = {"id": f"m_{len(c['messages']) + 1:04d}",
               "role": role, "content": content, "ts": now}
        if extra: msg.update(extra)
        c["messages"].append(msg)
        c["updated_at"] = now
        self.auto_save()
        return msg

    def delete(self, cid):
        before = len(self.data.get("conversations", []))
        self.data["conversations"] = [
            c for c in self.data.get("conversations", []) if c["id"] != cid]
        if self.data.get("current_id") == cid:
            self.data["current_id"] = None
        ok = len(self.data["conversations"]) < before
        if ok: self.save(backup=True)
        return ok

    def set_current(self, cid):
        self.data["current_id"] = cid
        self.save()

    def toggle_pin(self, cid):
        c = self.get(cid)
        if not c: return False
        c["pinned"] = not c.get("pinned", False)
        self.save()
        return c["pinned"]

    def export_to(self, path, cid=None):
        try:
            if cid:
                conv = self.get(cid)
                if not conv: return False
                payload = {"version": DATA_VERSION, "app": "Lumi Assistant",
                           "exported_at": datetime.datetime.now().isoformat(),
                           "type": "single", "conversations": [conv]}
            else:
                payload = dict(self.data)
                payload["exported_at"] = datetime.datetime.now().isoformat()
                payload["type"] = "full"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[STORAGE] Export lỗi: {e}")
            return False

    def import_from(self, path, merge=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:
            print(f"[STORAGE] Import lỗi: {e}")
            return 0, 0
        incoming = payload.get("conversations", [])
        if not incoming: return 0, 0
        if not merge:
            self.data["conversations"] = incoming
            self.data["current_id"] = incoming[0]["id"] if incoming else None
            self.save(backup=True)
            return len(incoming), 0
        existing = {c["id"] for c in self.data.get("conversations", [])}
        added, skipped = 0, 0
        for c in incoming:
            if c.get("id") in existing:
                skipped += 1; continue
            c.setdefault("tags", []); c.setdefault("pinned", False)
            c.setdefault("messages", [])
            self.data["conversations"].append(c)
            added += 1
        if added: self.save(backup=True)
        return added, skipped

    def stats(self):
        convs = self.data.get("conversations", [])
        return {
            "conversations": len(convs),
            "messages": sum(len(c.get("messages", [])) for c in convs),
            "current_id": self.data.get("current_id"),
            "file": str(CONV_FILE),
            "size_kb": round(CONV_FILE.stat().st_size / 1024, 1)
                       if CONV_FILE.is_file() else 0,
        }


DEFAULT_SETTINGS = {
    "version": DATA_VERSION, "theme": "dark",
    "provider": "groq", "mode": "Advanced",
    "sidebar_visible": True,
    "window": {"width": 1320, "height": 820, "x": None, "y": None},
}


class SettingsStore:
    def __init__(self):
        ensure_dirs()
        self.data = _read_json(SETT_FILE, DEFAULT_SETTINGS)
        for k, v in DEFAULT_SETTINGS.items():
            self.data.setdefault(k, v)

    def get(self, key, default=None): return self.data.get(key, default)

    def set(self, **kwargs):
        self.data.update(kwargs)
        self.save()

    def save(self):
        self.data["version"] = DATA_VERSION
        _write_json_atomic(SETT_FILE, self.data)