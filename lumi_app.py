"""
Lumi Assistant — UI full code + Logo hố đen + Bubble khít + Streaming mượt
"""
import sys, os, re, html, base64, math, random, json, datetime, subprocess, platform
from pathlib import Path

# ─── Windows AppUserModelID (PHẢI trước QApplication) ────────
import ctypes
from lumi_config import APP_ID
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception as e:
        print(f"[ICON] AppUserModelID lỗi: {e}")

from PySide6.QtCore import (Qt, QTimer, QThread, Signal, QObject, QPointF,
                             QSize, QFile, QIODevice, QDateTime)
from PySide6.QtGui  import (QPainter, QColor, QRadialGradient, QPen, QBrush,
                             QLinearGradient, QFont, QFontDatabase,
                             QTextCursor, QTextCharFormat, QAction, QIcon,
                             QPixmap, QCursor)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                                QComboBox, QPushButton, QTextBrowser, QTextEdit,
                                QPlainTextEdit, QFrame, QStatusBar,
                                QVBoxLayout, QHBoxLayout, QSpacerItem,
                                QSizePolicy, QFileDialog, QMessageBox,
                                QScrollArea, QMenu, QInputDialog, QToolButton)

from lumi_config import (LUMI_NAME, LUMI_TAGLINE, LUMI_VERSION, LUMI_AVATAR,
                          PROVIDERS, MODES, DEFAULT_MODE, MAX_CHARS,
                          LOGO_FILE, LOGO_SMALL, ICON_FILE, ICON_PNG, BASE_DIR)
from lumi_ai import LumiClient
from lumi_storage import ConvStore, SettingsStore, CONV_FILE, DATA_DIR


# ═══════════════════════════════════════════════════════════════
#  LOGO LOADER
# ═══════════════════════════════════════════════════════════════
_PIXMAP_CACHE = {}

def load_logo(size=64, path=None):
    key = (size, path)
    if key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[key]
    candidates = [path] if path else [LOGO_SMALL, LOGO_FILE, ICON_PNG]
    for p in candidates:
        if p and os.path.isfile(p):
            pix = QPixmap(p)
            if not pix.isNull():
                pix = pix.scaled(size, size, Qt.KeepAspectRatio,
                                  Qt.SmoothTransformation)
                _PIXMAP_CACHE[key] = pix
                return pix
    _PIXMAP_CACHE[key] = None
    return None


def has_logo():
    return any(os.path.isfile(p) for p in [LOGO_SMALL, LOGO_FILE, ICON_PNG])


# ═══════════════════════════════════════════════════════════════
#  QSS — DARK
# ═══════════════════════════════════════════════════════════════
QSS_DARK = """
QMainWindow { background: transparent; }
#centralWidget { background: transparent; }

QWidget#sidebar {
    background: rgba(6,11,24,0.88);
    border-right: 1px solid rgba(120,220,255,0.14);
}
QPushButton#btnNewChat {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(29,155,209,0.28), stop:1 rgba(124,77,255,0.28));
    color:#d6f6ff; border:1px solid rgba(120,220,255,0.35);
    border-radius:10px; padding:8px 12px;
    font-size:13px; font-weight:600; text-align:left;
}
QPushButton#btnNewChat:hover { border-color:#7bdcff;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(29,155,209,0.4), stop:1 rgba(124,77,255,0.4)); }

QLabel#sidebarGroup {
    color:#5a8aaa; font-size:10.5px;
    font-weight:600; letter-spacing:1.2px;
    padding: 10px 12px 4px 12px;
}
QLabel#sidebarEmpty { color:#4a6a85; font-size:11px;
    padding: 20px 16px; font-style:italic; }

QFrame#convItem {
    background: transparent; border-radius:8px;
    border: 1px solid transparent;
}
QFrame#convItem:hover {
    background: rgba(120,220,255,0.06);
    border-color: rgba(120,220,255,0.18);
}
QFrame#convItem[active="true"] {
    background: rgba(120,220,255,0.12);
    border-color: rgba(120,220,255,0.4);
}
QPushButton#convTitle {
    background: transparent; color:#c8e8ff;
    border:none; padding: 6px 4px;
    font-size:12.5px; text-align:left;
}
QPushButton#convTitle:hover { color:#fff; }
QPushButton#convMenu {
    background: transparent; color:#7ba8c9;
    border:none; padding:0; font-size:14px;
    min-width:22px; max-width:22px;
    min-height:22px; max-height:22px;
    border-radius:11px;
}
QPushButton#convMenu:hover {
    background: rgba(120,220,255,0.15); color:#fff;
}
QLabel#sidebarBottom {
    color:#4a6a85; font-size:10.5px;
    padding: 8px 12px;
    border-top: 1px solid rgba(120,220,255,0.12);
}

QFrame#topBar {
    background: rgba(8,14,28,0.72);
    border-bottom: 1px solid rgba(120,220,255,0.18);
}
QLabel#lblAvatar { background: transparent; }
QLabel#lblName {
    color:#9be7ff; font-size:17px; font-weight:700;
    letter-spacing:5px; font-family:'Segoe UI','Inter',sans-serif;
}
QLabel#lblTagline { color:#6fa8c7; font-size:11px; letter-spacing:0.5px; }
QLabel#lblProvider, QLabel#lblMode { color:#7ba8c9; font-size:11px; }

QComboBox {
    background: rgba(20,32,52,0.92); color:#d6f6ff;
    border:1px solid rgba(120,220,255,0.3); border-radius:8px;
    padding:4px 10px; font-size:12px; min-height:26px;
}
QComboBox:hover { border-color: rgba(120,220,255,0.75); }
QComboBox::drop-down { border:none; width:22px; }
QComboBox::down-arrow { image:none; width:0; height:0;
    border-left:4px solid transparent; border-right:4px solid transparent;
    border-top:5px solid #9be7ff; }
QComboBox QAbstractItemView { background:#0a1422; color:#d6f6ff;
    border:1px solid rgba(120,220,255,0.3);
    selection-background-color: rgba(120,220,255,0.25);
    outline:none; padding:4px; }

QPushButton {
    background: rgba(20,32,52,0.88); color:#d6f6ff;
    border:1px solid rgba(120,220,255,0.25); border-radius:10px;
    padding:6px 14px; font-size:13px; min-height:32px;
}
QPushButton:hover { background: rgba(30,55,85,0.95);
    border-color: rgba(120,220,255,0.75); }
QPushButton:pressed { background: rgba(60,130,180,0.7); }
QPushButton:disabled { color:#5a7a94; border-color: rgba(120,220,255,0.1); }
QPushButton:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(60,200,255,0.4), stop:1 rgba(180,120,255,0.4));
    border-color:#7bdcff; }
QPushButton[flatIcon="true"] {
    min-width:38px; max-width:38px; min-height:34px; max-height:34px;
    padding:0; font-size:15px; }

QTextBrowser#chatView {
    background: rgba(4,8,18,0.55); border:none;
    color:#e0f7fa; padding:14px 20px; font-size:13.5px;
    selection-background-color: rgba(120,220,255,0.35); }

QFrame#inputBar {
    background: rgba(8,14,28,0.72);
    border-top: 1px solid rgba(120,220,255,0.18); }
QTextEdit#txtInput {
    background: rgba(12,22,38,0.92); color:#e0f7fa;
    border:1px solid rgba(120,220,255,0.3); border-radius:14px;
    padding:10px 16px; font-size:13.5px;
    selection-background-color: rgba(120,220,255,0.35); }
QTextEdit#txtInput:focus { border-color: rgba(120,220,255,0.85); }

QPushButton#btnSend {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #1d9bd1, stop:1 #7c4dff);
    color:white; border:none; border-radius:14px;
    font-weight:700; font-size:13px; min-height:44px; }
QPushButton#btnSend:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
    stop:0 #23b0e8, stop:1 #9166ff); }
QPushButton#btnSend:disabled { background: rgba(40,60,90,0.7); color:#7f9bb3; }

QFrame#continueBar {
    background: rgba(255,190,100,0.12);
    border-top: 1px solid rgba(255,190,100,0.35); }
QLabel#lblContinueWarn { color:#ffd28a; font-size:12px; }
QPushButton#btnContinue {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #ff8c42, stop:1 #ff5e7a);
    color:white; font-weight:600; border:none;
    border-radius:10px; padding:6px 16px; }

QStatusBar { background: rgba(5,10,20,0.85); color:#7ba8c9; font-size:11px; }

QScrollBar:vertical { background:transparent; width:10px; margin:0; }
QScrollBar::handle:vertical { background: rgba(120,220,255,0.25);
    border-radius:5px; min-height:30px; }
QScrollBar::handle:vertical:hover { background: rgba(120,220,255,0.6); }
QScrollBar::add-line, QScrollBar::sub-line { height:0; }
QScrollBar::add-page, QScrollBar::sub-page { background:transparent; }

QFrame[role="user"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(29,155,209,0.30), stop:1 rgba(124,77,255,0.30));
    border:1px solid rgba(120,220,255,0.38); border-radius:14px; }
QFrame[role="assistant"] {
    background: rgba(18,30,52,0.75);
    border:1px solid rgba(120,220,255,0.22); border-radius:14px; }
QLabel#bubbleName { color:#9be7ff; font-size:11px; font-weight:600;
    letter-spacing:0.5px; }
QLabel#bubbleText { color:#e8f6ff; font-size:13.5px; }
QPushButton#btnCopyBubble {
    background: rgba(20,32,52,0.9); color:#b9e0ff;
    border:1px solid rgba(120,220,255,0.3);
    border-radius:7px; padding:2px 10px; font-size:11px;
    min-height:22px; max-height:24px; }
QPushButton#btnCopyBubble:hover { background: rgba(40,70,110,0.95);
    border-color:#7bdcff; }

QFrame[role="code"] {
    background: #0a1220;
    border:1px solid rgba(120,220,255,0.25); border-radius:10px; }
QLabel#codeLang { color:#7bdcff; font-size:10.5px;
    letter-spacing:1px; font-weight:600; }
QPlainTextEdit#codeText {
    background: transparent; color:#d4f1ff;
    border:none; font-family:'Cascadia Code','Consolas','Menlo',monospace;
    font-size:12.5px; }
QPushButton#btnCopyCode {
    background: rgba(20,32,52,0.9); color:#b9e0ff;
    border:1px solid rgba(120,220,255,0.3);
    border-radius:7px; padding:3px 12px; font-size:11px;
    min-height:24px; max-height:26px; }
QPushButton#btnCopyCode:hover { background: rgba(40,70,110,0.95);
    border-color:#7bdcff; }
"""

QSS_LIGHT = """
QMainWindow { background: transparent; }
#centralWidget { background: transparent; }

QWidget#sidebar {
    background: rgba(245,249,253,0.92);
    border-right: 1px solid rgba(80,140,200,0.22);
}
QPushButton#btnNewChat {
    background: white; color:#1565a0;
    border:1px solid rgba(80,140,200,0.4);
    border-radius:10px; padding:8px 12px;
    font-size:13px; font-weight:600; text-align:left; }
QPushButton#btnNewChat:hover { border-color:#5aa0e0; background:#eaf4ff; }

QLabel#sidebarGroup { color:#4a7fa3; font-size:10.5px;
    font-weight:600; letter-spacing:1.2px;
    padding: 10px 12px 4px 12px; }
QLabel#sidebarEmpty { color:#8aa8bf; font-size:11px;
    padding: 20px 16px; font-style:italic; }

QFrame#convItem {
    background: transparent; border-radius:8px;
    border: 1px solid transparent; }
QFrame#convItem:hover {
    background: rgba(90,160,224,0.1);
    border-color: rgba(90,160,224,0.3); }
QFrame#convItem[active="true"] {
    background: rgba(90,160,224,0.18);
    border-color: rgba(90,160,224,0.5); }
QPushButton#convTitle {
    background: transparent; color:#1a3d5c;
    border:none; padding: 6px 4px;
    font-size:12.5px; text-align:left; }
QPushButton#convTitle:hover { color:#0a2540; }
QPushButton#convMenu {
    background: transparent; color:#5a8aaa;
    border:none; padding:0; font-size:14px;
    min-width:22px; max-width:22px;
    min-height:22px; max-height:22px;
    border-radius:11px; }
QPushButton#convMenu:hover {
    background: rgba(90,160,224,0.2); color:#0a2540; }
QLabel#sidebarBottom { color:#8aa8bf; font-size:10.5px;
    padding: 8px 12px;
    border-top: 1px solid rgba(80,140,200,0.18); }

QFrame#topBar {
    background: rgba(255,255,255,0.85);
    border-bottom: 1px solid rgba(80,140,200,0.22); }
QLabel#lblAvatar { background: transparent; }
QLabel#lblName { color:#1565a0; font-size:17px; font-weight:700;
    letter-spacing:5px; }
QLabel#lblTagline { color:#4a7fa3; font-size:11px; }
QLabel#lblProvider, QLabel#lblMode { color:#3d6a8a; font-size:11px; }

QComboBox { background:white; color:#1a3d5c;
    border:1px solid rgba(80,140,200,0.4); border-radius:8px;
    padding:4px 10px; font-size:12px; min-height:26px; }
QComboBox:hover { border-color:#5aa0e0; }
QComboBox::drop-down { border:none; width:22px; }
QComboBox::down-arrow { image:none; width:0; height:0;
    border-left:4px solid transparent; border-right:4px solid transparent;
    border-top:5px solid #5a8aaa; }
QComboBox QAbstractItemView { background:white; color:#1a3d5c;
    border:1px solid rgba(80,140,200,0.4);
    selection-background-color: rgba(90,160,224,0.3);
    outline:none; padding:4px; }

QPushButton { background:white; color:#1a3d5c;
    border:1px solid rgba(80,140,200,0.4); border-radius:10px;
    padding:6px 14px; font-size:13px; min-height:32px; }
QPushButton:hover { background:#eaf4ff; border-color:#5aa0e0; }
QPushButton:pressed { background:#d6e9ff; }
QPushButton:checked { background:#d6e9ff; border-color:#5aa0e0; }
QPushButton[flatIcon="true"] {
    min-width:38px; max-width:38px; min-height:34px; max-height:34px;
    padding:0; font-size:15px; }

QTextBrowser#chatView {
    background: rgba(255,255,255,0.72); border:none;
    color:#0d2b45; padding:14px 20px; font-size:13.5px;
    selection-background-color: rgba(90,160,224,0.4); }

QFrame#inputBar {
    background: rgba(255,255,255,0.85);
    border-top: 1px solid rgba(80,140,200,0.22); }
QTextEdit#txtInput {
    background: white; color:#0d2b45;
    border:1px solid rgba(80,140,200,0.4); border-radius:14px;
    padding:10px 16px; font-size:13.5px; }
QTextEdit#txtInput:focus { border-color:#5aa0e0; }

QPushButton#btnSend {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #1565a0, stop:1 #7c4dff);
    color:white; border:none; border-radius:14px;
    font-weight:700; font-size:13px; min-height:44px; }
QPushButton#btnSend:disabled { background:#b0c8dd; color:#f0f0f0; }

QFrame#continueBar {
    background: rgba(255,190,100,0.2);
    border-top: 1px solid rgba(255,140,66,0.5); }
QLabel#lblContinueWarn { color:#a05a10; font-size:12px; }
QPushButton#btnContinue {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #ff8c42, stop:1 #ff5e7a);
    color:white; font-weight:600; border:none;
    border-radius:10px; padding:6px 16px; }

QStatusBar { background: rgba(230,240,250,0.95); color:#3d6a8a; font-size:11px; }

QScrollBar:vertical { background:transparent; width:10px; }
QScrollBar::handle:vertical { background: rgba(80,140,200,0.3);
    border-radius:5px; min-height:30px; }
QScrollBar::handle:vertical:hover { background: rgba(80,140,200,0.55); }
QScrollBar::add-line, QScrollBar::sub-line { height:0; }

QFrame[role="user"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 rgba(29,155,209,0.18), stop:1 rgba(124,77,255,0.18));
    border:1px solid rgba(80,140,200,0.35); border-radius:14px; }
QFrame[role="assistant"] {
    background: white;
    border:1px solid rgba(80,140,200,0.25); border-radius:14px; }
QLabel#bubbleName { color:#1565a0; font-size:11px; font-weight:600; }
QLabel#bubbleText { color:#0d2b45; font-size:13.5px; }
QPushButton#btnCopyBubble {
    background: white; color:#1565a0;
    border:1px solid rgba(80,140,200,0.4);
    border-radius:7px; padding:2px 10px; font-size:11px;
    min-height:22px; max-height:24px; }
QPushButton#btnCopyBubble:hover { background:#eaf4ff; }

QFrame[role="code"] { background: #f2f6fb;
    border:1px solid rgba(80,140,200,0.3); border-radius:10px; }
QLabel#codeLang { color:#1565a0; font-size:10.5px;
    letter-spacing:1px; font-weight:600; }
QPlainTextEdit#codeText {
    background: transparent; color:#0d2b45;
    border:none; font-family:'Cascadia Code','Consolas','Menlo',monospace;
    font-size:12.5px; }
QPushButton#btnCopyCode {
    background: white; color:#1565a0;
    border:1px solid rgba(80,140,200,0.4);
    border-radius:7px; padding:3px 12px; font-size:11px;
    min-height:24px; max-height:26px; }
QPushButton#btnCopyCode:hover { background:#eaf4ff; }
"""

# ═══════════════════════════════════════════════════════════════
#  STARFIELD
# ═══════════════════════════════════════════════════════════════
class _Star:
    __slots__ = ("x","y","size","phase","speed","alpha","color")

class _Shooting:
    __slots__ = ("x","y","vx","vy","life","max_life")

class StarfieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.stars, self.shooting = [], []
        self.mouse_pos, self.t = None, 0.0
        self.dark = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_dark(self, dark):
        self.dark = dark
        self.stars.clear()
        self.update()

    def _new_star(self, w, h):
        s = _Star()
        s.x, s.y = random.uniform(0, w), random.uniform(0, h)
        s.size = random.uniform(0.6, 2.3)
        s.phase = random.uniform(0, math.tau)
        s.speed = random.uniform(0.5, 2.0)
        s.alpha = random.uniform(0.35, 1.0)
        if self.dark:
            s.color = random.choice([(150,240,255),(255,255,255),
                (200,180,255),(255,200,230),(140,230,200)])
        else:
            s.color = random.choice([(140,180,230),(170,140,240),
                (120,170,220),(200,160,230)])
        return s

    def _new_shoot(self, w, h):
        ss = _Shooting()
        ss.x, ss.y = random.uniform(0, w), random.uniform(-50, h*0.3)
        sp = random.uniform(7, 13)
        ang = random.uniform(math.pi*0.15, math.pi*0.35)
        ss.vx, ss.vy = math.cos(ang)*sp, math.sin(ang)*sp
        ss.max_life = random.randint(45, 85)
        ss.life = ss.max_life
        return ss

    def _tick(self):
        self.t += 0.033
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0: return
        target = max(90, (w*h)//7500)
        while len(self.stars) < target:
            self.stars.append(self._new_star(w, h))
        if random.random() < 0.006 and len(self.shooting) < 3:
            self.shooting.append(self._new_shoot(w, h))
        alive = []
        for ss in self.shooting:
            ss.life -= 1; ss.x += ss.vx; ss.y += ss.vy
            if ss.life > 0 and -60 < ss.x < w+60 and -60 < ss.y < h+60:
                alive.append(ss)
        self.shooting = alive
        try:
            lp = self.mapFromGlobal(QCursor.pos())
            self.mouse_pos = lp if self.rect().contains(lp) else None
        except Exception:
            self.mouse_pos = None
        self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        grad = QLinearGradient(0, 0, w, h)
        if self.dark:
            grad.setColorAt(0, QColor(4, 9, 20))
            grad.setColorAt(0.45, QColor(8, 12, 30))
            grad.setColorAt(1, QColor(16, 8, 34))
        else:
            grad.setColorAt(0, QColor(230, 244, 255))
            grad.setColorAt(0.5, QColor(238, 240, 252))
            grad.setColorAt(1, QColor(246, 236, 254))
        p.fillRect(self.rect(), grad)

        for s in self.stars:
            tw = 0.55 + 0.45*math.sin(self.t*s.speed + s.phase)
            a = int(255 * s.alpha * tw)
            if self.mouse_pos:
                dx, dy = s.x - self.mouse_pos.x(), s.y - self.mouse_pos.y()
                d2 = dx*dx + dy*dy
                if d2 < 230*230:
                    a = min(255, int(a + 140*(1 - math.sqrt(d2)/230)))
            col = QColor(*s.color); col.setAlpha(a)
            p.setPen(Qt.NoPen); p.setBrush(col)
            p.drawEllipse(QPointF(s.x, s.y), s.size, s.size)
            if s.size > 1.7:
                glow = QRadialGradient(QPointF(s.x, s.y), s.size*6)
                c2 = QColor(*s.color); c2.setAlpha(int(a*0.28))
                c3 = QColor(*s.color); c3.setAlpha(0)
                glow.setColorAt(0, c2); glow.setColorAt(1, c3)
                p.setBrush(glow)
                p.drawEllipse(QPointF(s.x, s.y), s.size*6, s.size*6)

        for ss in self.shooting:
            prog = ss.life / ss.max_life
            a = int(255 * prog)
            tx, ty = ss.x - ss.vx*12, ss.y - ss.vy*12
            g2 = QLinearGradient(ss.x, ss.y, tx, ty)
            g2.setColorAt(0, QColor(200, 240, 255, a))
            g2.setColorAt(1, QColor(200, 240, 255, 0))
            p.setPen(QPen(QBrush(g2), 2.2))
            p.drawLine(QPointF(ss.x, ss.y), QPointF(tx, ty))
            p.setPen(Qt.NoPen); p.setBrush(QColor(255,255,255,a))
            p.drawEllipse(QPointF(ss.x, ss.y), 2.2, 2.2)

        if self.mouse_pos:
            glow = QRadialGradient(QPointF(self.mouse_pos), 200)
            base = (120,220,255,35) if self.dark else (120,160,240,25)
            glow.setColorAt(0, QColor(*base))
            glow.setColorAt(1, QColor(base[0],base[1],base[2],0))
            p.setBrush(glow); p.setPen(Qt.NoPen)
            p.drawEllipse(self.mouse_pos, 200, 200)

# ═══════════════════════════════════════════════════════════════
#  WORKER
# ═══════════════════════════════════════════════════════════════
class StreamWorker(QObject):
    chunk = Signal(str); done = Signal(str); error = Signal(str)
    def __init__(self, client, text="", image_b64=None, image_mime=None, continue_from=None):
        super().__init__()
        self.client, self.text = client, text
        self.image_b64, self.image_mime = image_b64, image_mime or "image/jpeg"
        self.continue_from = continue_from

    def run(self):
        try:
            gen = (self.client.continue_from(self.continue_from)
                   if self.continue_from is not None
                   else self.client.stream_chat(self.text, self.image_b64, self.image_mime))
            finish = None
            for delta, fr in gen:
                if delta: self.chunk.emit(delta)
                if fr: finish = fr
            self.done.emit(finish or "stop")
        except Exception as e:
            self.error.emit(str(e))

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════
class ConvItem(QFrame):
    clicked = Signal(str)
    delete_requested = Signal(str)
    rename_requested = Signal(str)
    copy_requested = Signal(str)
    pin_requested = Signal(str)

    def __init__(self, conv, active=False, parent=None):
        super().__init__(parent)
        self.setObjectName("convItem")
        self.conv_id = conv["id"]
        self.setProperty("active", "true" if active else "false")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 6, 4)
        lay.setSpacing(2)

        title = conv["title"] or "Trò chuyện mới"
        display = ("📌 " if conv.get("pinned") else "") + (
            title if len(title) <= 32 else title[:31] + "…")
        self.btn = QPushButton(display)
        self.btn.setObjectName("convTitle")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(lambda: self.clicked.emit(self.conv_id))
        lay.addWidget(self.btn, 1)

        self.menu = QToolButton()
        self.menu.setObjectName("convMenu")
        self.menu.setText("⋯")
        self.menu.setCursor(Qt.PointingHandCursor)
        self.menu.setPopupMode(QToolButton.InstantPopup)
        m = QMenu(self.menu)
        m.setStyleSheet("""
            QMenu { background:#0a1422; color:#d6f6ff;
                border:1px solid rgba(120,220,255,0.3); padding:4px; }
            QMenu::item { padding:6px 16px; border-radius:6px; }
            QMenu::item:selected { background: rgba(120,220,255,0.2); }
        """)
        pin_label = "📌  Bỏ ghim" if conv.get("pinned") else "📌  Ghim lên đầu"
        m.addAction(pin_label, lambda: self.pin_requested.emit(self.conv_id))
        m.addAction("✏️  Đổi tên", lambda: self.rename_requested.emit(self.conv_id))
        m.addAction("📋  Copy tiêu đề", lambda: self.copy_requested.emit(self.conv_id))
        m.addSeparator()
        m.addAction("🗑️  Xoá", lambda: self.delete_requested.emit(self.conv_id))
        self.menu.setMenu(m)
        lay.addWidget(self.menu)


class Sidebar(QWidget):
    new_chat_requested = Signal()
    conversation_selected = Signal(str)
    conversation_deleted = Signal(str)
    conversation_renamed = Signal(str, str)
    conversation_copied = Signal(str)
    conversation_pin_toggled = Signal(str)

    def __init__(self, store: ConvStore, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(262)
        self.store = store

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 12, 10, 6)
        root.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        if has_logo():
            logo_lbl = QLabel()
            pix = load_logo(28)
            if pix:
                logo_lbl.setPixmap(pix)
            logo_lbl.setFixedSize(28, 28)
            logo_lbl.setScaledContents(True)
            header.addWidget(logo_lbl)

        self.btn_new = QPushButton("  ✚   Trò chuyện mới")
        self.btn_new.setObjectName("btnNewChat")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setMinimumHeight(38)
        self.btn_new.clicked.connect(self.new_chat_requested.emit)
        header.addWidget(self.btn_new, 1)
        root.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border:none; }")
        self.inner = QWidget()
        self.inner.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.inner)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.inner)
        root.addWidget(self.scroll, 1)

        self.lbl_bottom = QLabel(f"{LUMI_NAME} {LUMI_VERSION}")
        self.lbl_bottom.setObjectName("sidebarBottom")
        self.lbl_bottom.setAlignment(Qt.AlignCenter)
        root.addWidget(self.lbl_bottom)

        self.refresh()

    def refresh(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        convs = self.store.list()
        current = self.store.data.get("current_id")

        if not convs:
            empty = QLabel("Chưa có cuộc trò chuyện nào.\nBấm 'Trò chuyện mới' để bắt đầu ✨")
            empty.setObjectName("sidebarEmpty")
            empty.setWordWrap(True)
            self.list_layout.insertWidget(0, empty)
            return

        now = datetime.datetime.now()
        groups = {"Hôm nay": [], "7 ngày": [], "30 ngày": [], "Cũ hơn": []}
        for c in convs:
            try:
                dt = datetime.datetime.fromisoformat(c.get("updated_at", c["created_at"]))
            except Exception:
                dt = now
            delta = (now - dt).days
            if delta < 1: groups["Hôm nay"].append(c)
            elif delta < 7: groups["7 ngày"].append(c)
            elif delta < 30: groups["30 ngày"].append(c)
            else: groups["Cũ hơn"].append(c)

        idx = 0
        for gname, items in groups.items():
            if not items: continue
            lbl = QLabel(gname)
            lbl.setObjectName("sidebarGroup")
            self.list_layout.insertWidget(idx, lbl); idx += 1
            for c in items:
                item = ConvItem(c, active=(c["id"] == current))
                item.clicked.connect(self.conversation_selected.emit)
                item.delete_requested.connect(self.conversation_deleted.emit)
                item.rename_requested.connect(self.conversation_renamed.emit)
                item.copy_requested.connect(self.conversation_copied.emit)
                item.pin_requested.connect(self.conversation_pin_toggled.emit)
                self.list_layout.insertWidget(idx, item); idx += 1

# ═══════════════════════════════════════════════════════════════
#  BUBBLE — ôm khít chữ
# ═══════════════════════════════════════════════════════════════
class ChatBubble(QFrame):
    copy_requested = Signal(str)
    def __init__(self, role="assistant", name="Lumi", text="", parent=None):
        super().__init__(parent)
        self.setProperty("role", "user" if role == "user" else "assistant")
        self.role, self.raw_text = role, text
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMaximumWidth(720)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 6)
        outer.setSpacing(10)

        # Avatar
        av = QLabel()
        av.setFixedSize(38, 38)
        av.setAlignment(Qt.AlignCenter)
        if role == "user":
            av.setText("🧑")
            av.setStyleSheet(
                "background: qradialgradient(cx:0.5,cy:0.5,radius:0.5,"
                "stop:0 rgba(120,220,255,0.35), stop:1 rgba(120,220,255,0));"
                "border-radius:19px; font-size:20px;")
        else:
            pix = load_logo(38)
            if pix:
                av.setPixmap(pix)
                av.setStyleSheet(
                    "background: qradialgradient(cx:0.5,cy:0.5,radius:0.5,"
                    "stop:0 rgba(120,220,255,0.18), stop:1 rgba(120,220,255,0));"
                    "border-radius:19px;")
            else:
                av.setText(LUMI_AVATAR)
                av.setStyleSheet("font-size:20px;")

        # Box nội dung
        self.box = QFrame()
        self.box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.box.setStyleSheet("background: transparent;")
        box_l = QVBoxLayout(self.box)
        box_l.setContentsMargins(14, 10, 14, 12)
        box_l.setSpacing(6)

        head = QHBoxLayout(); head.setSpacing(8)
        nm = QLabel(name.upper()); nm.setObjectName("bubbleName")
        head.addWidget(nm); head.addStretch(1)
        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setObjectName("btnCopyBubble")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.clicked.connect(lambda: self.copy_requested.emit(self.raw_text))
        head.addWidget(self.btn_copy)
        box_l.addLayout(head)

        self.lbl = QLabel(text); self.lbl.setObjectName("bubbleText")
        self.lbl.setTextFormat(Qt.RichText)
        self.lbl.setWordWrap(True)
        self.lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.lbl.setOpenExternalLinks(True)
        box_l.addWidget(self.lbl)

        if role == "user":
            outer.addStretch(1)
            outer.addWidget(self.box, 0)
            outer.addWidget(av, 0, Qt.AlignTop)
        else:
            outer.addWidget(av, 0, Qt.AlignTop)
            outer.addWidget(self.box, 0)
            outer.addStretch(1)

    def set_html(self, html_text):
        self.lbl.setText(html_text)


class CodeBlock(QFrame):
    def __init__(self, lang, code, parent=None):
        super().__init__(parent)
        self.setProperty("role", "code")
        self.raw_code = code
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 10); lay.setSpacing(6)
        head = QHBoxLayout(); head.setSpacing(8)
        lbl = QLabel((lang or "code").upper()); lbl.setObjectName("codeLang")
        head.addWidget(lbl); head.addStretch(1)
        btn = QPushButton("📋 Copy code"); btn.setObjectName("btnCopyCode")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: QApplication.clipboard().setText(self.raw_code))
        head.addWidget(btn)
        lay.addLayout(head)
        self.txt = QPlainTextEdit()
        self.txt.setObjectName("codeText")
        self.txt.setPlainText(code); self.txt.setReadOnly(True)
        lines = min(code.count("\n") + 1, 30)
        self.txt.setFixedHeight(min(520, 20 + lines*18))
        lay.addWidget(self.txt)

# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════
class LumiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{LUMI_NAME} Assistant")
        self.resize(1320, 820)
        self.setMinimumSize(920, 620)

        icon_path = ICON_FILE if os.path.isfile(ICON_FILE) else ICON_PNG
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.dark_mode = True
        self.streaming_text = ""
        self.attached_image = None
        self.store = ConvStore()
        self.settings = SettingsStore()

        # Buffer stream cho mượt
        self._pending_flush = False
        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_stream)
        self._flush_timer.start(33)

        self._build_ui()
        self._wire_events()
        self._apply_theme()
        self._load_or_create_conversation()

    # ─── Build ──────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        self.starfield = StarfieldWidget(central)
        self.starfield.lower()

        main_h = QHBoxLayout(central)
        main_h.setContentsMargins(0, 0, 0, 0); main_h.setSpacing(0)

        self.sidebar = Sidebar(self.store)
        main_h.addWidget(self.sidebar)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(0)

        # TOPBAR
        self.topBar = QFrame(); self.topBar.setObjectName("topBar")
        self.topBar.setFixedHeight(78)
        tl = QHBoxLayout(self.topBar)
        tl.setContentsMargins(18, 10, 18, 10); tl.setSpacing(10)

        self.btnToggleSidebar = QPushButton("☰")
        self.btnToggleSidebar.setProperty("flatIcon", "true")
        self.btnToggleSidebar.setToolTip("Ẩn/hiện sidebar")
        tl.addWidget(self.btnToggleSidebar)

        self.lblAvatar = QLabel()
        self.lblAvatar.setObjectName("lblAvatar")
        self.lblAvatar.setFixedSize(54, 54)
        self.lblAvatar.setAlignment(Qt.AlignCenter)
        pix = load_logo(48)
        if pix:
            self.lblAvatar.setPixmap(pix)
        else:
            self.lblAvatar.setText(LUMI_AVATAR)
            self.lblAvatar.setStyleSheet("font-size:30px;")
        tl.addWidget(self.lblAvatar)

        nameCol = QVBoxLayout(); nameCol.setSpacing(0)
        self.lblName = QLabel(" ".join(LUMI_NAME.upper())); self.lblName.setObjectName("lblName")
        self.lblTagline = QLabel(LUMI_TAGLINE); self.lblTagline.setObjectName("lblTagline")
        nameCol.addWidget(self.lblName); nameCol.addWidget(self.lblTagline)
        tl.addLayout(nameCol)
        tl.addStretch(1)

        self.lblProvider = QLabel("Provider"); self.lblProvider.setObjectName("lblProvider")
        tl.addWidget(self.lblProvider)
        self.comboProvider = QComboBox(); self.comboProvider.addItems(PROVIDERS)
        self.comboProvider.setMinimumWidth(120)
        tl.addWidget(self.comboProvider)

        self.lblMode = QLabel("Mode"); self.lblMode.setObjectName("lblMode")
        tl.addWidget(self.lblMode)
        self.comboMode = QComboBox()
        for m, cfg in MODES.items():
            self.comboMode.addItem(f"{cfg['icon']}  {m}", m)
        self.comboMode.setCurrentText(f"{MODES[DEFAULT_MODE]['icon']}  {DEFAULT_MODE}")
        self.comboMode.setMinimumWidth(160)
        tl.addWidget(self.comboMode)

        self.btnTheme = QPushButton("🌙"); self.btnTheme.setProperty("flatIcon", "true")
        self.btnTheme.setToolTip("Đổi Dark / Light"); tl.addWidget(self.btnTheme)
        self.btnSave = QPushButton("💾"); self.btnSave.setProperty("flatIcon", "true")
        self.btnSave.setToolTip("Lưu hội thoại ra file .txt"); tl.addWidget(self.btnSave)
        self.btnExport = QPushButton("📤"); self.btnExport.setProperty("flatIcon", "true")
        self.btnExport.setToolTip("Export JSON")
        self.btnExport.setCursor(Qt.PointingHandCursor); tl.addWidget(self.btnExport)
        self.btnImport = QPushButton("📥"); self.btnImport.setProperty("flatIcon", "true")
        self.btnImport.setToolTip("Import JSON")
        self.btnImport.setCursor(Qt.PointingHandCursor); tl.addWidget(self.btnImport)
        self.btnOpenData = QPushButton("📂"); self.btnOpenData.setProperty("flatIcon", "true")
        self.btnOpenData.setToolTip(f"Mở folder data: {DATA_DIR}")
        self.btnOpenData.setCursor(Qt.PointingHandCursor); tl.addWidget(self.btnOpenData)
        self.btnClear = QPushButton("🗑️"); self.btnClear.setProperty("flatIcon", "true")
        self.btnClear.setToolTip("Xoá hội thoại hiện tại"); tl.addWidget(self.btnClear)

        cl.addWidget(self.topBar)

        # CHAT SCROLL
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: rgba(4,8,18,0.55); border:none; }")
        self.chatContainer = QWidget()
        self.chatContainer.setStyleSheet("background: transparent;")
        self.chatLayout = QVBoxLayout(self.chatContainer)
        self.chatLayout.setContentsMargins(20, 12, 20, 12); self.chatLayout.setSpacing(6)
        self.chatLayout.addStretch(1)
        self.scroll.setWidget(self.chatContainer)
        cl.addWidget(self.scroll, 1)

        # CONTINUE BAR
        self.continueBar = QFrame(); self.continueBar.setObjectName("continueBar")
        cbl = QHBoxLayout(self.continueBar)
        cbl.setContentsMargins(16, 6, 16, 6); cbl.setSpacing(10)
        cbl.addStretch(1)
        self.lblContinueWarn = QLabel("⚠️ Câu trả lời đã chạm giới hạn")
        self.lblContinueWarn.setObjectName("lblContinueWarn")
        cbl.addWidget(self.lblContinueWarn)
        self.btnContinue = QPushButton("⏵ Tiếp tục viết"); self.btnContinue.setObjectName("btnContinue")
        cbl.addWidget(self.btnContinue); cbl.addStretch(1)
        self.continueBar.setVisible(False)
        cl.addWidget(self.continueBar)

        # INPUT BAR
        self.inputBar = QFrame(); self.inputBar.setObjectName("inputBar")
        self.inputBar.setMinimumHeight(76)
        il = QHBoxLayout(self.inputBar)
        il.setContentsMargins(16, 10, 16, 10); il.setSpacing(8)
        self.btnAttach = QPushButton("📎"); self.btnAttach.setProperty("flatIcon", "true")
        self.btnAttach.setToolTip("Gửi ảnh"); il.addWidget(self.btnAttach)
        self.btnMic = QPushButton("🎤"); self.btnMic.setProperty("flatIcon", "true")
        self.btnMic.setToolTip("Nhập giọng nói"); il.addWidget(self.btnMic)
        self.btnSpeak = QPushButton("🔊"); self.btnSpeak.setProperty("flatIcon", "true")
        self.btnSpeak.setToolTip("Đọc trả lời cuối"); il.addWidget(self.btnSpeak)
        self.btnSearch = QPushButton("🔍"); self.btnSearch.setProperty("flatIcon", "true")
        self.btnSearch.setCheckable(True); self.btnSearch.setToolTip("Tìm web")
        il.addWidget(self.btnSearch)

        self.txtInput = QTextEdit(); self.txtInput.setObjectName("txtInput")
        self.txtInput.setPlaceholderText("Nhập tin nhắn... (Enter gửi · Shift+Enter xuống dòng)")
        self.txtInput.setMinimumHeight(44); self.txtInput.setMaximumHeight(110)
        il.addWidget(self.txtInput, 1)

        self.btnSend = QPushButton("Gửi  ▸"); self.btnSend.setObjectName("btnSend")
        self.btnSend.setMinimumWidth(110); self.btnSend.setMaximumWidth(130)
        il.addWidget(self.btnSend)
        cl.addWidget(self.inputBar)

        main_h.addWidget(content, 1)
        self.setStatusBar(QStatusBar(self))

        central.installEventFilter(self)
        self.starfield.setGeometry(0, 0, central.width(), central.height())

    def eventFilter(self, obj, ev):
        if obj is self.centralWidget() and ev.type() == ev.Type.Resize:
            self.starfield.setGeometry(0, 0, obj.width(), obj.height())
        if hasattr(self, "txtInput") and obj is self.txtInput and ev.type() == ev.Type.KeyPress:
            if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                if ev.modifiers() & Qt.ShiftModifier:
                    return False
                self._send(); return True
        return super().eventFilter(obj, ev)

    # ─── Wire ───────────────────────────────────────────────
    def _wire_events(self):
        self.client = LumiClient(provider=self.comboProvider.currentText(),
                                 mode=self.comboMode.currentData())
        self.comboProvider.currentTextChanged.connect(self._on_provider_change)
        self.comboMode.currentIndexChanged.connect(self._on_mode_change)
        self.btnClear.clicked.connect(self._clear_chat)
        self.btnSave.clicked.connect(self._save_chat)
        self.btnExport.clicked.connect(self._export_json)
        self.btnImport.clicked.connect(self._import_json)
        self.btnOpenData.clicked.connect(self._open_data_folder)
        self.btnTheme.clicked.connect(self._toggle_theme)
        self.btnSend.clicked.connect(self._send)
        self.btnContinue.clicked.connect(self._continue_writing)
        self.btnAttach.clicked.connect(self._pick_image)
        self.btnSpeak.clicked.connect(self._speak_last)
        self.btnMic.clicked.connect(self._mic_input)
        self.btnToggleSidebar.clicked.connect(self._toggle_sidebar)
        self.txtInput.installEventFilter(self)

        self.sidebar.new_chat_requested.connect(self._new_conversation)
        self.sidebar.conversation_selected.connect(self._load_conversation)
        self.sidebar.conversation_deleted.connect(self._delete_conversation)
        self.sidebar.conversation_renamed.connect(self._rename_conversation)
        self.sidebar.conversation_copied.connect(
            lambda cid: (QApplication.clipboard().setText(self.store.get(cid)["title"]),
                         self.statusBar().showMessage("Đã copy tiêu đề", 2000)))
        self.sidebar.conversation_pin_toggled.connect(self._toggle_pin)

    # ─── Conversation ───────────────────────────────────────
    def _load_or_create_conversation(self):
        cid = self.store.data.get("current_id")
        if cid and self.store.get(cid):
            self._load_conversation(cid)
        else:
            self._new_conversation()

    def _new_conversation(self):
        cid = self.store.data.get("current_id")
        if cid:
            cur = self.store.get(cid)
            if cur and len(cur.get("messages", [])) == 0:
                self._clear_chat_view(); self._greet()
                self.sidebar.refresh(); return
        self.store.new(provider=self.comboProvider.currentText(),
                       mode=self.comboMode.currentData())
        self._clear_chat_view(); self.client.reset(); self._greet()
        self.sidebar.refresh()
        self.statusBar().showMessage("Đã tạo cuộc trò chuyện mới", 2500)

    def _load_conversation(self, cid):
        conv = self.store.get(cid)
        if not conv: return
        self.store.set_current(cid)
        self.client.reset()
        self._clear_chat_view()

        if not conv["messages"]:
            self._greet()
        else:
            for m in conv["messages"]:
                role = m["role"]
                name = "Bạn" if role == "user" else LUMI_NAME
                self._render_message(role, name, m["content"], save=False)
                self.client.history.append({"role": role, "content": m["content"]})
        self.sidebar.refresh()
        self.statusBar().showMessage(f"Đã mở: {conv['title']}", 2500)

    def _delete_conversation(self, cid):
        conv = self.store.get(cid)
        if not conv: return
        if QMessageBox.question(self, "Xoá cuộc trò chuyện",
                f"Xoá '{conv['title']}'?") != QMessageBox.Yes: return
        self.store.delete(cid)
        self.sidebar.refresh()
        if self.store.data.get("current_id") is None:
            self._load_or_create_conversation()

    def _rename_conversation(self, cid):
        conv = self.store.get(cid)
        if not conv: return
        new, ok = QInputDialog.getText(self, "Đổi tên", "Tên mới:", text=conv["title"])
        if ok and new.strip():
            self.store.update(cid, title=new.strip())
            self.sidebar.refresh()
            self.statusBar().showMessage("Đã đổi tên", 2000)

    def _toggle_pin(self, cid):
        pinned = self.store.toggle_pin(cid)
        self.sidebar.refresh()
        self.statusBar().showMessage("📌 Đã ghim" if pinned else "Đã bỏ ghim", 2000)

    def _update_current_title(self, first_user_msg):
        cid = self.store.data.get("current_id")
        if not cid: return
        conv = self.store.get(cid)
        if not conv: return
        if conv["title"] in ("Trò chuyện mới", ""):
            title = first_user_msg.strip().split("\n")[0][:50] or "Trò chuyện mới"
            self.store.update(cid, title=title)
            self.sidebar.refresh()

    def _toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    # ─── Theme ──────────────────────────────────────────────
    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.btnTheme.setText("☀️" if not self.dark_mode else "🌙")
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(QSS_DARK if self.dark_mode else QSS_LIGHT)
        self.starfield.set_dark(self.dark_mode)
        self.scroll.setStyleSheet(
            "QScrollArea { background: rgba(4,8,18,0.55); border:none; }" if self.dark_mode
            else "QScrollArea { background: rgba(255,255,255,0.72); border:none; }")

    # ─── Misc ───────────────────────────────────────────────
    def _on_provider_change(self, name):
        self.client.set_provider(name)
        self.statusBar().showMessage(f"Provider: {name}", 3000)

    def _on_mode_change(self):
        mode = self.comboMode.currentData()
        self.client.set_mode(mode)
        self.statusBar().showMessage(f"Mode: {mode}", 3000)

    def _scroll_bottom(self):
        sb = self.scroll.verticalScrollBar(); sb.setValue(sb.maximum())

    def _on_copy(self, txt):
        QApplication.clipboard().setText(txt)
        self.statusBar().showMessage("✅ Đã copy", 1500)

    def _to_html(self, md: str) -> str:
        s = html.escape(md, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)
        s = re.sub(r"`([^`\n]+?)`",
                   r'<span style="background:rgba(120,220,255,0.15); '
                   r'padding:1px 5px; border-radius:4px; '
                   r'font-family:Consolas,monospace;">\1</span>', s)
        s = re.sub(r"(https?://[^\s<]+)",
                   r'<a href="\1" style="color:#7bdcff;">\1</a>', s)
        s = re.sub(r"(?m)^\s*[-*]\s+(.+)$", r"• \1", s)
        return s.replace("\n", "<br>")

    def _append_bubble(self, role, name, html_text, raw_text=""):
        # Wrapper để bubble không kéo full width
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        wl = QHBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)

        b = ChatBubble(role=role, name=name, text=html_text)
        b.copy_requested.connect(self._on_copy)

        if role == "user":
            wl.addStretch(1)
            wl.addWidget(b, 0, Qt.AlignTop | Qt.AlignRight)
        else:
            wl.addWidget(b, 0, Qt.AlignTop | Qt.AlignLeft)
            wl.addStretch(1)

        self.chatLayout.insertWidget(self.chatLayout.count() - 1, wrapper)
        QTimer.singleShot(30, self._scroll_bottom)
        return b

    def _clear_chat_view(self):
        while self.chatLayout.count() > 1:
            item = self.chatLayout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

    def _render_message(self, role, name, content, save=True):
        parts = re.split(r"```([^\n]*)\n([\s\S]*?)```", content)
        if parts[0].strip() or len(parts) == 1:
            self._append_bubble(role, name, self._to_html(parts[0]), parts[0])
        i = 1
        while i + 1 < len(parts):
            lang, code = parts[i].strip(), parts[i+1]
            cb = CodeBlock(lang or "text", code)
            self.chatLayout.insertWidget(self.chatLayout.count()-1, cb)
            tail = parts[i+2] if i+2 < len(parts) else ""
            if tail.strip():
                self._append_bubble(role, name, self._to_html(tail), tail)
            i += 3
        QTimer.singleShot(30, self._scroll_bottom)
        if save:
            cid = self.store.data.get("current_id")
            if cid:
                self.store.add_message(cid, role, content)

    def _greet(self):
        hello = (f"Xin chào bạn 🌊 Mình là <b>{LUMI_NAME}</b> — "
                 f"trợ lý AI vui vẻ, dịu dàng, sống ở nơi biển gặp sao ✨<br>"
                 f"Hỏi mình bất cứ điều gì nhé — bằng bất kỳ ngôn ngữ nào! 🪼")
        self._append_bubble("assistant", LUMI_NAME, hello, hello)

    # ─── Send ───────────────────────────────────────────────
    def _send(self):
        text = self.txtInput.toPlainText().strip()
        if not text and not self.attached_image: return
        if len(text) > MAX_CHARS:
            QMessageBox.warning(self, "Quá dài", f"Vượt {MAX_CHARS} ký tự."); return
        self.txtInput.clear()

        img_b64, img_mime = (None, None)
        if self.attached_image:
            img_b64, img_mime = self.attached_image
            self.attached_image = None

        display = text or "[Đã gửi ảnh]"
        self._append_bubble("user", "Bạn", self._to_html(display), display)
        self._update_current_title(text or "Ảnh")
        self._render_message("user", "Bạn", text or "[image]", save=True)
        self._start_stream(text=text, img_b64=img_b64, img_mime=img_mime)

    def _continue_writing(self):
        self.continueBar.setVisible(False)
        self._start_stream(continue_from=self.streaming_text)

    def _start_stream(self, text="", img_b64=None, img_mime=None, continue_from=None):
        self.btnSend.setEnabled(False); self.btnSend.setText("⏳ Đang trả lời...")
        self.statusBar().showMessage("Lumi đang suy nghĩ...")
        self.current_bubble = self._append_bubble(
            "assistant", LUMI_NAME,
            '<i style="color:#7bdcff;">Lumi đang trả lời...</i>', "")
        self.streaming_text = ""

        self._thread = QThread(self)
        self._worker = StreamWorker(self.client, text=text, image_b64=img_b64,
                                     image_mime=img_mime, continue_from=continue_from)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.chunk.connect(self._on_chunk)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_chunk(self, delta):
        """Buffer chunk — KHÔNG update UI ngay."""
        self.streaming_text += delta
        self._pending_flush = True
        if len(self.streaming_text) > MAX_CHARS - 200:
            self.continueBar.setVisible(True)

    def _flush_stream(self):
        """Timer 30fps — update UI 1 lần/frame cho mượt."""
        if not self._pending_flush or not hasattr(self, "current_bubble"):
            return
        self._pending_flush = False
        try:
            self.current_bubble.set_html(self._to_html(self.streaming_text))
        except RuntimeError:
            return
        self._scroll_bottom()

    def _on_done(self, finish_reason):
        self.btnSend.setEnabled(True); self.btnSend.setText("Gửi  ▸")
        # Flush nốt phần còn lại
        self._pending_flush = False
        try:
            self.chatLayout.removeWidget(self.current_bubble.parentWidget() or self.current_bubble)
        except Exception:
            pass
        try:
            self.current_bubble.deleteLater()
        except Exception:
            pass

        self._render_message("assistant", LUMI_NAME, self.streaming_text, save=True)
        hit = (finish_reason == "length") or (len(self.streaming_text) >= MAX_CHARS - 100)
        self.continueBar.setVisible(hit)
        self.statusBar().showMessage("✅ Sẵn sàng", 2500)
        self._scroll_bottom()

    def _on_error(self, err):
        self.btnSend.setEnabled(True); self.btnSend.setText("Gửi  ▸")
        self.continueBar.setVisible(False)
        try:
            self.current_bubble.set_html(
                f'<span style="color:#ff8a8a;">⚠️ Lỗi: {html.escape(err)}</span>')
        except RuntimeError:
            pass
        self.statusBar().showMessage("❌ Lỗi", 4000)

    # ─── Export / Import / Folder ───────────────────────────
    def _export_json(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#0a1422; color:#d6f6ff;
                border:1px solid rgba(120,220,255,0.3); padding:4px; }
            QMenu::item { padding:8px 20px; border-radius:6px; }
            QMenu::item:selected { background: rgba(120,220,255,0.2); }
        """)
        act_cur = menu.addAction("📄  Export hội thoại hiện tại")
        act_all = menu.addAction("📦  Export toàn bộ hội thoại")
        chosen = menu.exec(self.btnExport.mapToGlobal(self.btnExport.rect().bottomLeft()))
        if chosen is act_cur:
            cid = self.store.data.get("current_id")
            if not cid:
                QMessageBox.information(self, "Trống", "Chưa có hội thoại nào."); return
            conv = self.store.get(cid)
            safe = re.sub(r'[<>:"/\\|?*]', '_', conv["title"])[:40]
            path, _ = QFileDialog.getSaveFileName(
                self, "Export JSON", f"lumi-{safe}.json", "JSON (*.json)")
            if path and self.store.export_to(path, cid=cid):
                self.statusBar().showMessage(f"✅ Export: {path}", 4000)
        elif chosen is act_all:
            default = f"lumi-all-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"
            path, _ = QFileDialog.getSaveFileName(
                self, "Export toàn bộ JSON", default, "JSON (*.json)")
            if path and self.store.export_to(path):
                s = self.store.stats()
                self.statusBar().showMessage(
                    f"✅ Export {s['conversations']} hội thoại → {path}", 4000)

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON (*.json)")
        if not path: return
        box = QMessageBox(self)
        box.setWindowTitle("Import JSON")
        box.setText(f"File: {os.path.basename(path)}\n\nBạn muốn làm gì?")
        btn_merge = box.addButton("🔀 Merge (thêm vào)", QMessageBox.AcceptRole)
        btn_over  = box.addButton("♻️  Ghi đè toàn bộ", QMessageBox.DestructiveRole)
        box.addButton("Huỷ", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_merge:
            added, skipped = self.store.import_from(path, merge=True)
            self.sidebar.refresh()
            self.statusBar().showMessage(
                f"✅ Import: +{added} mới, bỏ qua {skipped} trùng", 5000)
        elif clicked is btn_over:
            ok = QMessageBox.warning(
                self, "Xác nhận",
                "Ghi đè sẽ XOÁ toàn bộ hội thoại hiện tại. Tiếp tục?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
            if not ok: return
            added, _ = self.store.import_from(path, merge=False)
            self.sidebar.refresh()
            self._load_or_create_conversation()
            self.statusBar().showMessage(f"✅ Ghi đè: {added} hội thoại", 5000)

    def _open_data_folder(self):
        folder = str(DATA_DIR)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self.statusBar().showMessage(f"📂 {folder}", 3000)
        except Exception as e:
            QMessageBox.information(self, "Folder data", f"{folder}\n\n{e}")

    # ─── Utilities ──────────────────────────────────────────
    def _clear_chat(self):
        cid = self.store.data.get("current_id")
        if not cid: return
        conv = self.store.get(cid)
        if not conv or not conv.get("messages"):
            self._clear_chat_view(); self._greet(); return
        if QMessageBox.question(self, "Xoá hội thoại",
                "Xoá toàn bộ tin nhắn của cuộc trò chuyện này?") != QMessageBox.Yes:
            return
        self.store.update(cid, messages=[], title="Trò chuyện mới")
        self.client.reset()
        self._clear_chat_view(); self._greet()
        self.sidebar.refresh()

    def _save_chat(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu hội thoại",
            f"lumi-chat-{datetime.datetime.now():%Y%m%d-%H%M%S}.txt",
            "Text (*.txt);;Markdown (*.md)")
        if not path: return
        cid = self.store.data.get("current_id")
        conv = self.store.get(cid) if cid else None
        msgs = conv["messages"] if conv else []
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {LUMI_NAME} — {LUMI_VERSION}\n")
                f.write(f"# {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
                for m in msgs:
                    who = "🧑 Bạn" if m["role"] == "user" else f"{LUMI_NAME}"
                    f.write(f"### {who}\n{m['content']}\n\n")
            self.statusBar().showMessage(f"✅ Đã lưu: {path}", 4000)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.webp *.gif)")
        if not path: return
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            mime = "image/jpeg"
            ext = path.lower()
            if ext.endswith(".png"): mime = "image/png"
            elif ext.endswith(".webp"): mime = "image/webp"
            elif ext.endswith(".gif"): mime = "image/gif"
            self.attached_image = (b64, mime)
            self.txtInput.setPlaceholderText(f"📎 Đã đính kèm: {os.path.basename(path)}")
            self.statusBar().showMessage("📎 Ảnh đã sẵn sàng — nhấn Gửi", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))

    def _mic_input(self):
        try:
            import speech_recognition as sr
        except ImportError:
            QMessageBox.information(self, "Thiếu thư viện",
                "Cần: pip install SpeechRecognition pyaudio"); return
        try:
            r = sr.Recognizer()
            with sr.Microphone() as src:
                self.statusBar().showMessage("🎤 Đang nghe...")
                QApplication.processEvents()
                audio = r.listen(src, timeout=6, phrase_time_limit=10)
            self.statusBar().showMessage("🧠 Đang nhận dạng...")
            text = r.recognize_google(audio, language="vi-VN")
            self.txtInput.setPlainText(text)
            self.statusBar().showMessage("✅ Đã nhận giọng nói", 2500)
        except Exception as e:
            self.statusBar().showMessage(f"❌ {e}", 4000)

    def _speak_last(self):
        cid = self.store.data.get("current_id")
        conv = self.store.get(cid) if cid else None
        last = None
        if conv:
            for m in reversed(conv["messages"]):
                if m["role"] == "assistant": last = m["content"]; break
        if not last:
            self.statusBar().showMessage("Không có gì để đọc.", 2500); return
        try:
            import pyttsx3
            e = pyttsx3.init(); e.say(last[:3000]); e.runAndWait()
        except Exception as e:
            self.statusBar().showMessage(f"❌ TTS: {e}", 4000)


# ═══════════════════════════════════════════════════════════════
#  ENTRY — KHÔNG splash screen
# ═══════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(f"{LUMI_NAME} Assistant")
    app.setApplicationDisplayName(f"{LUMI_NAME} Assistant")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    icon_path = ICON_FILE if os.path.isfile(ICON_FILE) else ICON_PNG
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"[ICON] ✅ Đã nạp icon: {os.path.basename(icon_path)}")
    else:
        print(f"[ICON] ⚠️  Không tìm thấy icon — chạy `python make_logo.py` và `python make_icon.py` trước.")

    win = LumiWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()