# -*- coding: utf-8 -*-
"""DraveShot - schermafbeeldingen en schermopnames met annotaties (Dravenlock).

- Foto: vastleggen (gebied/volledig scherm) en annoteren (tekst, pijl, vormen,
  pen, markeerstift, vervagen, bijsnijden); opslaan of naar klembord.
- Video: schermopname (gebied/volledig) via ffmpeg; daarna annotaties met een
  tijdsbereik op de video tekenen en in de export laten inbranden.
Volledig lokaal en offline. Video gebruikt ffmpeg (gdigrab op Windows).
"""
import os
import sys
import json
import time
import shutil
import subprocess
import traceback

APP_NAAM = "DraveShot"
APP_VERSIE = "0.1.8"
DONATIE_URL = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"
WINDOWS = (os.name == "nt")

if getattr(sys, "frozen", False):
    BASIS = os.path.dirname(sys.executable)
else:
    BASIS = os.path.dirname(os.path.abspath(__file__))
FOUT_BESTAND = os.path.join(BASIS, "app-fout.txt")
DATA_MAP = os.path.join(BASIS, "DraveShot-data")
CONFIG_BESTAND = os.path.join(DATA_MAP, "instellingen.json")
OPNAME_MAP = os.path.join(DATA_MAP, "opnames")

BG = "#0e0e11"; PANEL = "#16161b"; PANEL2 = "#1c1c22"; TEXT = "#d4d4d4"
MUTED = "#8a8a94"; ACCENT = "#6fa3d6"; LINE = "#23232b"; WARN = "#d68a6f"
GOED = "#7fb069"


def zorg_voor_mappen():
    for m in (DATA_MAP, OPNAME_MAP):
        try:
            os.makedirs(m, exist_ok=True)
        except OSError:
            pass


def _excepthook(soort, waarde, tb):
    try:
        with open(FOUT_BESTAND, "w", encoding="utf-8") as f:
            f.write("DraveShot startfout\n\n")
            f.write("".join(traceback.format_exception(soort, waarde, tb)))
    except Exception:
        pass
    sys.__excepthook__(soort, waarde, tb)


sys.excepthook = _excepthook

STANDAARD_CONFIG = {"taal": "auto", "ffmpeg": "", "fps": 25, "vertraging": 0}

# Statische Windows-builds van ffmpeg (bevatten ffmpeg.exe en ffprobe.exe in /bin).
# Eerste die lukt wordt gebruikt.
FFMPEG_DOWNLOAD_URLS = [
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip",
]


def laad_config():
    cfg = dict(STANDAARD_CONFIG)
    try:
        with open(CONFIG_BESTAND, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            cfg.update(d)
    except Exception:
        pass
    return cfg


def bewaar_config(cfg):
    try:
        tmp = CONFIG_BESTAND + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_BESTAND)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ffmpeg-helpers
# ---------------------------------------------------------------------------
def _zonder_venster():
    if WINDOWS:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {"startupinfo": si}
    return {}


def _zoek_exe_in_map(map_pad, exe):
    """Zoek exe direct in map_pad en in submappen (bv. .../bin/ffmpeg.exe);
    hoofdletter-ongevoelig."""
    if not map_pad or not os.path.isdir(map_pad):
        return ""
    direct = os.path.join(map_pad, exe)
    if os.path.isfile(direct):
        return direct
    doel = exe.lower()
    try:
        for root, _dirs, files in os.walk(map_pad):
            for f in files:
                if f.lower() == doel:
                    return os.path.join(root, f)
    except OSError:
        pass
    return ""


def _kandidaat_bases():
    """Mappen waarin naar ffmpeg/DraveShot-data wordt gezocht (naast de app,
    de programmamap en de werkmap), zodat het ook wordt gevonden als het app-pad
    anders berekend wordt."""
    bases = [BASIS]
    extra = []
    try:
        if sys.argv and sys.argv[0]:
            extra.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    except Exception:
        pass
    try:
        extra.append(os.getcwd())
    except Exception:
        pass
    for b in extra:
        if b and b not in bases:
            bases.append(b)
    return bases


def vind_ffmpeg(cfg, naam="ffmpeg"):
    exe = naam + (".exe" if WINDOWS else "")
    # 1) expliciet aangewezen pad of map uit de instellingen
    p = cfg.get("ffmpeg", "")
    if p:
        if os.path.isfile(p):
            if naam == "ffmpeg":
                return p
            buur = os.path.join(os.path.dirname(p), exe)
            if os.path.isfile(buur):
                return buur
        elif os.path.isdir(p):
            gev = _zoek_exe_in_map(p, exe)
            if gev:
                return gev
    # 2) naast de app / in DraveShot-data (ook submappen), in meerdere basismappen
    for base in _kandidaat_bases():
        direct = os.path.join(base, exe)
        if os.path.isfile(direct):
            return direct
        gev = _zoek_exe_in_map(os.path.join(base, "DraveShot-data"), exe)
        if gev:
            return gev
    # 3) op het systeem-PATH
    return shutil.which(naam) or ""


def video_duur(cfg, pad):
    ffprobe = vind_ffmpeg(cfg, "ffprobe")
    if not ffprobe:
        return 0.0
    try:
        r = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                            "format=duration", "-of",
                            "default=nw=1:nk=1", pad],
                           capture_output=True, text=True, **_zonder_venster())
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def haal_frame(cfg, video, tijd, doel):
    ffmpeg = vind_ffmpeg(cfg)
    if not ffmpeg:
        return False
    try:
        subprocess.run([ffmpeg, "-y", "-ss", "%.3f" % tijd, "-i", video,
                        "-frames:v", "1", doel],
                       capture_output=True, **_zonder_venster())
        return os.path.isfile(doel)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QStatusBar, QGraphicsScene, QGraphicsView, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsPixmapItem,
    QGraphicsTextItem, QGraphicsItem, QColorDialog, QFileDialog, QToolButton,
    QButtonGroup, QInputDialog, QSlider, QDoubleSpinBox, QGraphicsLineItem,
    QProgressDialog,
)
from PyQt6.QtGui import (
    QAction, QIcon, QPixmap, QImage, QPainter, QPen, QColor, QFont,
    QPainterPath, QDesktopServices, QGuiApplication, QCursor, QTransform,
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal, QRectF, QPointF, QRect


def _bundel(naam):
    return os.path.join(getattr(sys, "_MEIPASS", BASIS), naam)


def app_icoon():
    for naam in ("app.ico", "logo.png"):
        p = _bundel(naam)
        if os.path.isfile(p):
            ic = QIcon(p)
            if not ic.isNull():
                return ic
    return QIcon()


def STIJL():
    return """
    QWidget { background: %(bg)s; color: %(text)s; font-size: 15px; }
    QLabel#titel { font-size: 24px; font-weight: bold; }
    QLabel#sub { color: %(muted)s; }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: %(panel2)s; color: %(text)s; border: 1px solid %(line)s;
        border-radius: 8px; padding: 7px; }
    QLineEdit:focus, QComboBox:focus { border: 1px solid %(accent)s; }
    QPushButton, QToolButton { background: %(panel2)s; color: %(text)s;
        border: 1px solid %(line)s; border-radius: 9px; padding: 8px 12px; }
    QPushButton:hover, QToolButton:hover { border: 1px solid %(accent)s; }
    QToolButton:checked { background: %(accent)s; color: #0b0b0e; border: none; }
    QPushButton#primair { background: %(accent)s; color: #0b0b0e; border: none; font-weight: bold; }
    QPushButton#primair:hover { background: #84b4e0; }
    QPushButton#gevaar { border: 1px solid %(warn)s; color: %(warn)s; }
    QGraphicsView { background: %(panel)s; border: 1px solid %(line)s; border-radius: 8px; }
    QMenuBar { background: %(bg)s; color: %(text)s; }
    QMenuBar::item:selected { background: %(panel2)s; }
    QMenu { background: %(panel)s; color: %(text)s; border: 1px solid %(line)s; }
    QMenu::item:selected { background: %(accent)s; color: #0b0b0e; }
    QStatusBar { background: %(bg)s; color: %(muted)s; }
    QSlider::groove:horizontal { height: 6px; background: %(panel2)s; border-radius: 3px; }
    QSlider::handle:horizontal { background: %(accent)s; width: 14px; margin: -5px 0;
        border-radius: 7px; }
    """ % {"bg": BG, "panel": PANEL, "panel2": PANEL2, "text": TEXT,
           "muted": MUTED, "accent": ACCENT, "line": LINE, "warn": WARN}


def centreer(d, ouder=None):
    try:
        s = (ouder.screen() if ouder else None) or QGuiApplication.primaryScreen()
        g = s.availableGeometry()
        d.move(g.center().x() - d.width() // 2, g.center().y() - d.height() // 2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal
# ---------------------------------------------------------------------------
def taal_detecteren():
    try:
        from PyQt6.QtCore import QLocale
        return "nl" if QLocale.system().name().lower().startswith("nl") else "en"
    except Exception:
        return "en"


TEKST = {
    "nl": {
        "ondertitel": "Schermafbeeldingen en schermopnames - met tekst, pijlen en vormen",
        "menu_bestand": "Bestand", "menu_help": "Help",
        "instellingen": "Instellingen", "afsluiten": "Afsluiten",
        "snelgids": "Snelgids", "over": "Over DraveShot", "donatie": "Donatie",
        "sluiten": "Sluiten", "opslaan": "Opslaan", "annuleren": "Annuleren",
        "tab_foto": "Schermafbeelding", "tab_video": "Schermopname",
        # foto
        "vastleggen_gebied": "Gebied vastleggen", "vastleggen_volledig": "Volledig scherm",
        "open_afbeelding": "Afbeelding openen...", "vertraging": "Vertraging (s)",
        "foto_leeg": "Leg een schermafbeelding vast of open een afbeelding om te annoteren.",
        "opslaan_als": "Opslaan als...", "kopieer": "Naar klembord",
        "gekopieerd": "Naar klembord gekopieerd.", "opgeslagen": "Opgeslagen: {pad}",
        # video
        "opname_starten": "Opname starten", "opname_gebied": "Opname (gebied)",
        "opname_stoppen": "Opname stoppen", "open_video": "Video openen...",
        "video_leeg": "Neem je scherm op of open een video om te annoteren.",
        "exporteren": "Exporteren (annotaties inbranden)...",
        "bezig_export": "Bezig met exporteren...", "export_klaar": "Klaar: {pad}",
        "export_fout": "Export mislukt (zie app-fout.txt of het logvenster).",
        "opnemen_bezig": "Opname loopt... klik op Stoppen.",
        "opnemen_bezig_kort": "Opname loopt",
        "ffmpeg_status_niet": "ffmpeg: niet gevonden - klik op een opname-knop om het "
                              "automatisch te downloaden, of wijs het aan bij Instellingen.",
        "tijd_van": "Van (s)", "tijd_tot": "Tot (s)", "tijd_uitleg":
            "Selecteer een annotatie en stel in wanneer die in beeld is (van/tot in seconden).",
        "geen_ffmpeg": "ffmpeg niet gevonden. Wijs het aan bij Instellingen, of zet "
                       "ffmpeg.exe (of de uitgepakte ffmpeg-map) in DraveShot-data.",
        "ffmpeg_vraag": "ffmpeg is nodig voor video en is niet gevonden.\n\nNu "
                        "automatisch downloaden? (eenmalig, ongeveer 100 MB; wordt "
                        "in DraveShot-data gezet)",
        "ffmpeg_downloaden": "ffmpeg downloaden...",
        "ffmpeg_klaar": "ffmpeg is gedownload en klaar voor gebruik.",
        "ffmpeg_mislukt": "Downloaden van ffmpeg is mislukt:\n{fout}\n\nJe kunt "
                          "ffmpeg.exe ook handmatig naast de app zetten of aanwijzen "
                          "bij Instellingen.",
        "inst_ffmpeg_download": "ffmpeg nu downloaden",
        "scrub": "Tijd",
        "zoom_in": "Inzoomen (+)", "zoom_uit": "Uitzoomen (-)",
        "passend": "Passend", "honderd": "100%",
        "zoom_tip": "Tip: zoom met de knoppen of Ctrl + scrollwiel. In 'Kiezen/"
                    "verplaatsen' kun je tekst en vormen verslepen.",
        # gereedschap
        "g_kies": "Kiezen/verplaatsen", "g_tekst": "Tekst", "g_pijl": "Pijl",
        "g_lijn": "Lijn", "g_rechthoek": "Rechthoek", "g_ovaal": "Ovaal",
        "g_pen": "Pen", "g_stift": "Markeerstift", "g_vervaag": "Vervagen",
        "g_bijsnijden": "Bijsnijden", "g_kleur": "Kleur", "g_dikte": "Dikte",
        "g_tekstgrootte": "Tekstgrootte",
        "g_ongedaan": "Ongedaan", "g_wis": "Alles wissen",
        "tekst_vraag": "Tekst (Enter = nieuwe regel):",
        # instellingen
        "inst_taal": "Taal", "inst_taal_auto": "Automatisch (computertaal)",
        "inst_ffmpeg": "ffmpeg (map of ffmpeg.exe; leeg = automatisch)",
        "inst_fps": "Opname-beelden per seconde (fps)", "bladeren": "Bladeren...",
        "herstart_taal": "Herstart de app om de taal volledig toe te passen.",
        "over_tekst": "DraveShot v{versie}\n\nSchermafbeeldingen en schermopnames met "
                      "annotaties. Lokaal en offline. Video gebruikt ffmpeg.\n\n"
                      "Contact: {contact}\nDonatie: {donatie}",
        "alleen_windows": "Schermvastlegging werkt op Windows. Open hier anders een "
                          "bestaande afbeelding/video om te annoteren.",
    },
    "en": {
        "ondertitel": "Screenshots and screen recordings - with text, arrows and shapes",
        "menu_bestand": "File", "menu_help": "Help",
        "instellingen": "Settings", "afsluiten": "Quit",
        "snelgids": "Quick guide", "over": "About DraveShot", "donatie": "Donate",
        "sluiten": "Close", "opslaan": "Save", "annuleren": "Cancel",
        "tab_foto": "Screenshot", "tab_video": "Screen recording",
        "vastleggen_gebied": "Capture region", "vastleggen_volledig": "Full screen",
        "open_afbeelding": "Open image...", "vertraging": "Delay (s)",
        "foto_leeg": "Capture a screenshot or open an image to annotate.",
        "opslaan_als": "Save as...", "kopieer": "To clipboard",
        "gekopieerd": "Copied to clipboard.", "opgeslagen": "Saved: {pad}",
        "opname_starten": "Start recording", "opname_gebied": "Record (region)",
        "opname_stoppen": "Stop recording", "open_video": "Open video...",
        "video_leeg": "Record your screen or open a video to annotate.",
        "exporteren": "Export (burn in annotations)...",
        "bezig_export": "Exporting...", "export_klaar": "Done: {pad}",
        "export_fout": "Export failed (see app-fout.txt or the log).",
        "opnemen_bezig": "Recording... click Stop.",
        "opnemen_bezig_kort": "Recording",
        "ffmpeg_status_niet": "ffmpeg: not found - click a recording button to download "
                              "it automatically, or point to it in Settings.",
        "tijd_van": "From (s)", "tijd_tot": "To (s)", "tijd_uitleg":
            "Select an annotation and set when it shows (from/to in seconds).",
        "geen_ffmpeg": "ffmpeg not found. Point to it in Settings, or put ffmpeg.exe "
                       "(or the extracted ffmpeg folder) in DraveShot-data.",
        "ffmpeg_vraag": "ffmpeg is needed for video and was not found.\n\nDownload it "
                        "automatically now? (one-time, about 100 MB; placed in "
                        "DraveShot-data)",
        "ffmpeg_downloaden": "Downloading ffmpeg...",
        "ffmpeg_klaar": "ffmpeg has been downloaded and is ready to use.",
        "ffmpeg_mislukt": "Downloading ffmpeg failed:\n{fout}\n\nYou can also put "
                          "ffmpeg.exe next to the app manually or point to it in "
                          "Settings.",
        "inst_ffmpeg_download": "Download ffmpeg now",
        "scrub": "Time",
        "zoom_in": "Zoom in (+)", "zoom_uit": "Zoom out (-)",
        "passend": "Fit", "honderd": "100%",
        "zoom_tip": "Tip: zoom with the buttons or Ctrl + mouse wheel. In "
                    "'Select/move' you can drag text and shapes.",
        "g_kies": "Select/move", "g_tekst": "Text", "g_pijl": "Arrow",
        "g_lijn": "Line", "g_rechthoek": "Rectangle", "g_ovaal": "Ellipse",
        "g_pen": "Pen", "g_stift": "Highlighter", "g_vervaag": "Blur",
        "g_bijsnijden": "Crop", "g_kleur": "Color", "g_dikte": "Width",
        "g_tekstgrootte": "Text size",
        "g_ongedaan": "Undo", "g_wis": "Clear all",
        "tekst_vraag": "Text (Enter = new line):",
        "inst_taal": "Language", "inst_taal_auto": "Automatic (system language)",
        "inst_ffmpeg": "ffmpeg (folder or ffmpeg.exe; empty = automatic)",
        "inst_fps": "Recording frames per second (fps)", "bladeren": "Browse...",
        "herstart_taal": "Restart the app to fully apply the language.",
        "over_tekst": "DraveShot v{versie}\n\nScreenshots and screen recordings with "
                      "annotations. Local and offline. Video uses ffmpeg.\n\n"
                      "Contact: {contact}\nDonate: {donatie}",
        "alleen_windows": "Screen capture works on Windows. Otherwise open an existing "
                          "image/video here to annotate.",
    },
}
_TAAL = "nl"


def T(s):
    return TEKST.get(_TAAL, TEKST["nl"]).get(s, s)


# ---------------------------------------------------------------------------
# Annotatie-items
# ---------------------------------------------------------------------------
class PijlItem(QGraphicsItem):
    def __init__(self, p1, p2, kleur, dikte):
        super().__init__()
        self.p1 = p1; self.p2 = p2; self.kleur = kleur; self.dikte = dikte
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

    def stel_eind(self, p2):
        self.prepareGeometryChange(); self.p2 = p2; self.update()

    def boundingRect(self):
        m = self.dikte + max(16, int(self.dikte * 3.5))
        return QRectF(self.p1, self.p2).normalized().adjusted(-m, -m, m, m)

    def paint(self, p, *_):
        import math
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.kleur, self.dikte, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawLine(self.p1, self.p2)
        hoek = math.atan2(self.p2.y() - self.p1.y(), self.p2.x() - self.p1.x())
        l = max(12, self.dikte * 3.2)
        for d in (-0.5, 0.5):
            x = self.p2.x() - l * math.cos(hoek + d)
            y = self.p2.y() - l * math.sin(hoek + d)
            p.drawLine(self.p2, QPointF(x, y))


class TekstItem(QGraphicsTextItem):
    """Tekst met een donker, half-doorzichtig plaatje erachter, zodat de tekst
    altijd goed leesbaar is - ook op een drukke ondergrond."""

    def __init__(self, tekst):
        super().__init__(tekst)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

    def boundingRect(self):
        return super().boundingRect().adjusted(-12, -8, 12, 8)

    def paint(self, p, opt, w=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = super().boundingRect().adjusted(-10, -6, 10, 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(r, 10, 10)
        super().paint(p, opt, w)


class TekenScene(QGraphicsScene):
    """Canvas met achtergrond (foto/videoframe) + annotaties; herbruikt voor
    foto-export (plat) en video-export (transparante overlay per tijdsbereik)."""

    def __init__(self):
        super().__init__()
        self.bg = None
        self.gereedschap = "kies"
        self.kleur = QColor(ACCENT)
        self.dikte = 4
        self.tekst_grootte = 40       # pixelhoogte van nieuwe tekst (instelbaar)
        self.annotaties = []          # toegevoegde items (volgorde)
        self.tijden = {}              # item -> (van, tot) voor video
        self._bezig = None
        self._start = None
        self._video_duur = 0.0

    def zet_achtergrond(self, pixmap):
        if self.bg is not None:
            self.removeItem(self.bg); self.bg = None
        pixmap.setDevicePixelRatio(1.0)
        self.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.bg = QGraphicsPixmapItem(pixmap)
        self.bg.setZValue(-1000)
        self.addItem(self.bg)

    def _registreer(self, item, van=None, tot=None):
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.annotaties.append(item)
        self.tijden[item] = (0.0 if van is None else van,
                             self._video_duur if tot is None else tot)

    def voeg_tekst_toe(self, tekst, pos):
        it = TekstItem(tekst)
        it.setDefaultTextColor(self.kleur)
        f = QFont("Arial"); f.setPixelSize(max(8, int(self.tekst_grootte)))
        f.setBold(True)
        it.setFont(f)
        it.setPos(pos)
        self.addItem(it); self._registreer(it)
        return it

    def ongedaan(self):
        if self.annotaties:
            it = self.annotaties.pop()
            self.tijden.pop(it, None)
            self.removeItem(it)

    def wis_alles(self):
        for it in list(self.annotaties):
            self.removeItem(it)
        self.annotaties.clear(); self.tijden.clear()

    # ---- muis ----
    def mousePressEvent(self, ev):
        if self.gereedschap == "kies":
            return super().mousePressEvent(ev)
        pos = ev.scenePos()
        g = self.gereedschap
        if g == "tekst":
            tekst, ok = QInputDialog.getMultiLineText(None, APP_NAAM, T("tekst_vraag"))
            if ok and tekst:
                self.voeg_tekst_toe(tekst, pos)
            ev.accept(); return
        self._start = pos
        if g in ("pen", "stift"):
            path = QPainterPath(pos)
            it = QGraphicsPathItem(path)
            kl = QColor(self.kleur)
            if g == "stift":
                kl.setAlpha(110)
                pen = QPen(kl, self.dikte * 4, Qt.PenStyle.SolidLine,
                           Qt.PenCapStyle.RoundCap)
            else:
                pen = QPen(kl, self.dikte, Qt.PenStyle.SolidLine,
                           Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            it.setPen(pen)
            self.addItem(it); self._bezig = ("pad", it, path)
        elif g == "rechthoek":
            it = QGraphicsRectItem(QRectF(pos, pos))
            it.setPen(QPen(self.kleur, self.dikte)); self.addItem(it)
            self._bezig = ("rect", it)
        elif g == "ovaal":
            it = QGraphicsEllipseItem(QRectF(pos, pos))
            it.setPen(QPen(self.kleur, self.dikte)); self.addItem(it)
            self._bezig = ("ovaal", it)
        elif g == "lijn":
            it = QGraphicsLineItem(pos.x(), pos.y(), pos.x(), pos.y())
            it.setPen(QPen(self.kleur, self.dikte, Qt.PenStyle.SolidLine,
                           Qt.PenCapStyle.RoundCap)); self.addItem(it)
            self._bezig = ("lijn", it)
        elif g == "pijl":
            it = PijlItem(pos, pos, self.kleur, self.dikte); self.addItem(it)
            self._bezig = ("pijl", it)
        elif g in ("vervaag", "bijsnijden"):
            it = QGraphicsRectItem(QRectF(pos, pos))
            stip = QColor(WARN) if g == "bijsnijden" else QColor(MUTED)
            it.setPen(QPen(stip, 2, Qt.PenStyle.DashLine)); self.addItem(it)
            self._bezig = (g, it)
        ev.accept()

    def mouseMoveEvent(self, ev):
        if self.gereedschap == "kies":
            return super().mouseMoveEvent(ev)
        if not self._bezig:
            return
        soort = self._bezig[0]; pos = ev.scenePos()
        if soort == "pad":
            _, it, path = self._bezig
            path.lineTo(pos); it.setPath(path)
        elif soort in ("rect", "ovaal", "vervaag", "bijsnijden"):
            self._bezig[1].setRect(QRectF(self._start, pos).normalized())
        elif soort == "lijn":
            self._bezig[1].setLine(self._start.x(), self._start.y(), pos.x(), pos.y())
        elif soort == "pijl":
            self._bezig[1].stel_eind(pos)
        ev.accept()

    def mouseReleaseEvent(self, ev):
        if self.gereedschap == "kies":
            return super().mouseReleaseEvent(ev)
        if not self._bezig:
            return
        soort = self._bezig[0]; it = self._bezig[1]
        if soort == "vervaag":
            self.removeItem(it)
            self._maak_vervaag(it.rect())
        elif soort == "bijsnijden":
            r = it.rect(); self.removeItem(it)
            self.bijsnijden(r)
        else:
            self._registreer(it)
        self._bezig = None
        ev.accept()

    def mouseDoubleClickEvent(self, ev):
        # dubbelklik op een tekst-annotatie -> bewerken (meerregelig)
        it = self.itemAt(ev.scenePos(), QTransform())
        if isinstance(it, TekstItem):
            tekst, ok = QInputDialog.getMultiLineText(
                None, APP_NAAM, T("tekst_vraag"), it.toPlainText())
            if ok:
                if tekst:
                    it.setPlainText(tekst)
                ev.accept(); return
        super().mouseDoubleClickEvent(ev)

    def _maak_vervaag(self, rect):
        if self.bg is None or rect.width() < 4 or rect.height() < 4:
            return
        bron = self.bg.pixmap()
        deel = bron.copy(rect.toRect())
        if deel.isNull():
            return
        klein = deel.scaled(max(1, deel.width() // 12), max(1, deel.height() // 12),
                            Qt.AspectRatioMode.IgnoreAspectRatio,
                            Qt.TransformationMode.FastTransformation)
        mozaiek = klein.scaled(deel.width(), deel.height(),
                               Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformationMode.FastTransformation)
        it = QGraphicsPixmapItem(mozaiek)
        it.setPos(rect.topLeft())
        it.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.addItem(it); self._registreer(it)

    def bijsnijden(self, rect):
        if self.bg is None:
            return
        rect = rect.intersected(self.sceneRect())
        if rect.width() < 4 or rect.height() < 4:
            return
        plat = self.render_plat()
        deel = plat.copy(rect.toRect())
        self.wis_alles()
        self.zet_achtergrond(QPixmap.fromImage(deel))

    # ---- render ----
    def render_plat(self):
        """Achtergrond + alle annotaties als platte afbeelding (foto-export)."""
        self.clearSelection()
        b = self.sceneRect()
        img = QImage(int(b.width()), int(b.height()), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        p = QPainter(img)
        self.render(p, QRectF(0, 0, b.width(), b.height()), b)
        p.end()
        return img

    def render_overlay(self, items):
        """Alleen de gegeven annotaties op een transparant vlak (video-overlay)."""
        self.clearSelection()
        zichtbaar = {}
        if self.bg:
            zichtbaar[self.bg] = self.bg.isVisible(); self.bg.setVisible(False)
        for it in self.annotaties:
            zichtbaar[it] = it.isVisible()
            it.setVisible(it in items)
        b = self.sceneRect()
        img = QImage(int(b.width()), int(b.height()), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        self.render(p, QRectF(0, 0, b.width(), b.height()), b)
        p.end()
        for it, v in zichtbaar.items():
            it.setVisible(v)
        return img


# ---------------------------------------------------------------------------
# Gebied-overlay (selecteer een schermgebied)
# ---------------------------------------------------------------------------
class GebiedOverlay(QDialog):
    """Modale, schermvullende overlay om een gebied te slepen. exec() geeft
    Accepted met self.gekozen gevuld, of Rejected bij Escape/geen selectie."""

    def __init__(self, schermpix):
        super().__init__(None)
        self.schermpix = schermpix
        self.start = None; self.eind = None; self.gekozen = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        scr = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(scr)

    def _factor(self):
        return (self.schermpix.width() / max(1, self.width()),
                self.schermpix.height() / max(1, self.height()))

    def paintEvent(self, _):
        p = QPainter(self)
        p.drawPixmap(QRectF(self.rect()), self.schermpix, QRectF(self.schermpix.rect()))
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))
        if self.start and self.eind:
            r = QRectF(self.start, self.eind).normalized()
            fx, fy = self._factor()
            bron = QRectF(r.x() * fx, r.y() * fy, r.width() * fx, r.height() * fy)
            p.drawPixmap(r, self.schermpix, bron)
            p.setPen(QPen(QColor(ACCENT), 2)); p.drawRect(r)

    def mousePressEvent(self, ev):
        self.start = ev.position(); self.eind = ev.position(); self.update()

    def mouseMoveEvent(self, ev):
        self.eind = ev.position(); self.update()

    def mouseReleaseEvent(self, ev):
        self.eind = ev.position()
        r = QRectF(self.start, self.eind).normalized()
        fx, fy = self._factor()
        gr = QRect(int(r.x() * fx), int(r.y() * fy),
                   int(r.width() * fx), int(r.height() * fy))
        if gr.width() > 4 and gr.height() > 4:
            self.gekozen = gr; self.accept()
        else:
            self.reject()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape:
            self.gekozen = None; self.reject()


class StopBalk(QWidget):
    """Klein, altijd-bovenop balkje om een lopende opname te stoppen."""

    def __init__(self, stop_cb):
        super().__init__(None, Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        lay = QHBoxLayout(self); lay.setContentsMargins(12, 8, 12, 8)
        lbl = QLabel("\u25CF " + T("opnemen_bezig_kort"))
        lbl.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        lay.addWidget(lbl)
        b = QPushButton(T("opname_stoppen")); b.setObjectName("gevaar")
        b.clicked.connect(stop_cb); lay.addWidget(b)
        self.setStyleSheet(
            "background: %s; border: 1px solid %s; border-radius: 10px;" % (PANEL, LINE))

    def plaats(self):
        self.adjustSize()
        scr = QGuiApplication.primaryScreen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2, scr.top() + 12)


def leg_scherm_vast(rect=None):
    scr = QGuiApplication.primaryScreen()
    pix = scr.grabWindow(0)
    pix.setDevicePixelRatio(1.0)
    if rect is not None:
        pix = pix.copy(rect)
        pix.setDevicePixelRatio(1.0)
    return pix


# ---------------------------------------------------------------------------
# Opname-thread (ffmpeg gdigrab)
# ---------------------------------------------------------------------------
class OpnameProces:
    def __init__(self, cfg, doel, rect=None):
        self.cfg = cfg; self.doel = doel; self.rect = rect; self.proc = None

    def start(self):
        ffmpeg = vind_ffmpeg(self.cfg)
        if not ffmpeg:
            return False, T("geen_ffmpeg")
        fps = str(int(self.cfg.get("fps", 25)))
        cmd = [ffmpeg, "-y", "-f", "gdigrab", "-framerate", fps]
        if self.rect is not None:
            cmd += ["-offset_x", str(self.rect.x()), "-offset_y", str(self.rect.y()),
                    "-video_size", "%dx%d" % (self.rect.width(), self.rect.height())]
        cmd += ["-i", "desktop", "-pix_fmt", "yuv420p", self.doel]
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, **_zonder_venster())
            return True, ""
        except Exception as e:
            return False, str(e)

    def stop(self):
        if not self.proc:
            return
        try:
            self.proc.stdin.write(b"q"); self.proc.stdin.flush()
            self.proc.wait(timeout=8)
        except Exception:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = None


class ExportThread(QThread):
    klaar = pyqtSignal(bool, str)

    def __init__(self, cfg, scene, bron_video, doel):
        super().__init__()
        self.cfg = cfg; self.scene = scene
        self.bron = bron_video; self.doel = doel
        self.overlays = []  # vooraf gerenderde (pad, van, tot)

    def run(self):
        ffmpeg = vind_ffmpeg(self.cfg)
        if not ffmpeg:
            self.klaar.emit(False, T("geen_ffmpeg")); return
        try:
            inputs = ["-i", self.bron]
            for pad, _, _ in self.overlays:
                inputs += ["-i", pad]
            filters = []
            vorig = "[0:v]"
            for i, (pad, van, tot) in enumerate(self.overlays, start=1):
                uit = "[v%d]" % i
                filters.append("%s[%d:v]overlay=0:0:enable='between(t,%.3f,%.3f)'%s"
                               % (vorig, i, van, tot, uit))
                vorig = uit
            cmd = [ffmpeg, "-y"] + inputs
            if filters:
                cmd += ["-filter_complex", ";".join(filters), "-map", vorig]
            else:
                cmd += ["-map", "0:v"]
            cmd += ["-map", "0:a?", "-c:a", "copy", "-pix_fmt", "yuv420p", self.doel]
            r = subprocess.run(cmd, capture_output=True, **_zonder_venster())
            ok = (r.returncode == 0 and os.path.isfile(self.doel))
            self.klaar.emit(ok, self.doel if ok else "")
        except Exception as e:
            self.klaar.emit(False, str(e))


class FfmpegDownloadThread(QThread):
    """Haalt een Windows-build van ffmpeg op en zet ffmpeg.exe + ffprobe.exe in
    de doelmap (DraveShot-data). Meldt voortgang (0-100, of -1 = onbekend)."""
    voortgang = pyqtSignal(int)
    klaar = pyqtSignal(bool, str)

    def __init__(self, doelmap, urls=None):
        super().__init__()
        self.doelmap = doelmap
        self.urls = list(urls) if urls else list(FFMPEG_DOWNLOAD_URLS)
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        laatste = ""
        for url in self.urls:
            if self._stop:
                self.klaar.emit(False, "geannuleerd"); return
            ok, info = self._probeer(url)
            if ok:
                self.klaar.emit(True, info); return
            if info == "geannuleerd":
                self.klaar.emit(False, info); return
            laatste = info
        self.klaar.emit(False, laatste or "download mislukt")

    def _probeer(self, url):
        import urllib.request
        import zipfile
        tmp = os.path.join(self.doelmap, "_ffmpeg_download.zip")
        try:
            os.makedirs(self.doelmap, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "DraveShot"})
            with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as f:
                totaal = int(r.headers.get("Content-Length", 0) or 0)
                gelezen = 0
                while True:
                    if self._stop:
                        f.close()
                        try:
                            os.remove(tmp)
                        except OSError:
                            pass
                        return False, "geannuleerd"
                    blok = r.read(262144)
                    if not blok:
                        break
                    f.write(blok); gelezen += len(blok)
                    self.voortgang.emit(int(gelezen * 100 / totaal) if totaal else -1)
            gevonden = {}
            with zipfile.ZipFile(tmp) as z:
                for naam in z.namelist():
                    basis = os.path.basename(naam).lower()
                    if basis in ("ffmpeg.exe", "ffprobe.exe") and basis not in gevonden:
                        doel = os.path.join(self.doelmap, basis)
                        with z.open(naam) as bron, open(doel, "wb") as uit:
                            shutil.copyfileobj(bron, uit)
                        gevonden[basis] = doel
            try:
                os.remove(tmp)
            except OSError:
                pass
            if "ffmpeg.exe" in gevonden:
                return True, gevonden["ffmpeg.exe"]
            return False, "ffmpeg.exe niet in het archief gevonden"
        except Exception as e:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            return False, str(e)


# ---------------------------------------------------------------------------
# Weergave en gereedschap
# ---------------------------------------------------------------------------
class ZoomView(QGraphicsView):
    """Voorbeeld met in-/uitzoomen (knoppen + Ctrl+scrollwiel) en scrollbalken."""

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def wheelEvent(self, ev):
        if ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            f = 1.2 if ev.angleDelta().y() > 0 else 1 / 1.2
            self.scale(f, f); ev.accept()
        else:
            super().wheelEvent(ev)

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_uit(self):
        self.scale(1 / 1.25, 1 / 1.25)

    def passend(self):
        sc = self.scene()
        if sc and sc.sceneRect().width() > 1:
            self.resetTransform()
            self.fitInView(sc.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def honderd(self):
        self.resetTransform()


class Gereedschapsbalk(QWidget):
    def __init__(self, scene, met_bijsnijden=True):
        super().__init__()
        self.scene = scene
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)
        self.groep = QButtonGroup(self); self.groep.setExclusive(True)
        gereedschappen = [
            ("kies", "g_kies"), ("tekst", "g_tekst"), ("pijl", "g_pijl"),
            ("lijn", "g_lijn"), ("rechthoek", "g_rechthoek"), ("ovaal", "g_ovaal"),
            ("pen", "g_pen"), ("stift", "g_stift"), ("vervaag", "g_vervaag"),
        ]
        if met_bijsnijden:
            gereedschappen.append(("bijsnijden", "g_bijsnijden"))
        for sleutel, lbl in gereedschappen:
            b = QToolButton(); b.setText(T(lbl)); b.setCheckable(True)
            b.clicked.connect(lambda _=False, s=sleutel: self._kies(s))
            self.groep.addButton(b); lay.addWidget(b)
            if sleutel == "kies":
                b.setChecked(True)
        self.kleurknop = QPushButton(T("g_kleur"))
        self.kleurknop.clicked.connect(self._kleur)
        self._zet_kleurknop()
        lay.addWidget(self.kleurknop)
        lay.addWidget(QLabel(T("g_dikte")))
        self.dikte = QSpinBox(); self.dikte.setRange(1, 40); self.dikte.setValue(4)
        self.dikte.valueChanged.connect(lambda v: setattr(self.scene, "dikte", v))
        lay.addWidget(self.dikte)
        lay.addWidget(QLabel(T("g_tekstgrootte")))
        self.tgrootte = QSpinBox(); self.tgrootte.setRange(8, 400)
        self.tgrootte.setValue(self.scene.tekst_grootte)
        self.tgrootte.valueChanged.connect(self._tekstgrootte)
        lay.addWidget(self.tgrootte)
        self.scene.selectionChanged.connect(self._sync_tekstgrootte)
        bo = QPushButton(T("g_ongedaan")); bo.clicked.connect(self.scene.ongedaan)
        lay.addWidget(bo)
        bw = QPushButton(T("g_wis")); bw.setObjectName("gevaar")
        bw.clicked.connect(self.scene.wis_alles); lay.addWidget(bw)
        lay.addStretch(1)

    def _tekstgrootte(self, v):
        self.scene.tekst_grootte = v
        for it in self.scene.selectedItems():
            if isinstance(it, TekstItem):
                f = it.font(); f.setPixelSize(v); it.setFont(f)

    def _sync_tekstgrootte(self):
        for it in self.scene.selectedItems():
            if isinstance(it, TekstItem):
                px = it.font().pixelSize()
                if px > 0:
                    self.tgrootte.blockSignals(True)
                    self.tgrootte.setValue(px)
                    self.tgrootte.blockSignals(False)
                break

    def _kies(self, sleutel):
        self.scene.gereedschap = sleutel
        from PyQt6.QtWidgets import QGraphicsView
        for v in self.scene.views():
            v.setDragMode(QGraphicsView.DragMode.NoDrag)

    def _kleur(self):
        c = QColorDialog.getColor(self.scene.kleur)
        if c.isValid():
            self.scene.kleur = c; self._zet_kleurknop()

    def _zet_kleurknop(self):
        c = self.scene.kleur
        self.kleurknop.setStyleSheet(
            "background:%s; color:#0b0b0e; border:none; border-radius:9px; padding:8px 12px;"
            % c.name())


# ---------------------------------------------------------------------------
# Instellingen / Snelgids
# ---------------------------------------------------------------------------
class InstellingenDialoog(QDialog):
    def __init__(self, ouder, cfg):
        super().__init__(ouder)
        self.cfg = cfg
        self.setWindowTitle(T("instellingen")); self.setWindowIcon(app_icoon())
        self.resize(560, 240); self.setStyleSheet(STIJL())
        lay = QVBoxLayout(self); form = QFormLayout()
        self.taal = QComboBox()
        self.taal.addItem(T("inst_taal_auto"), "auto")
        self.taal.addItem("Nederlands", "nl"); self.taal.addItem("English", "en")
        self.taal.setCurrentIndex(max(0, self.taal.findData(cfg.get("taal", "auto"))))
        form.addRow(T("inst_taal"), self.taal)
        frij = QHBoxLayout()
        self.ff = QLineEdit(cfg.get("ffmpeg", "")); frij.addWidget(self.ff, 1)
        bb = QPushButton(T("bladeren")); bb.clicked.connect(self._kies_ff)
        frij.addWidget(bb)
        bd = QPushButton(T("inst_ffmpeg_download")); bd.clicked.connect(self._download_ff)
        frij.addWidget(bd)
        fw = QWidget(); fw.setLayout(frij)
        form.addRow(T("inst_ffmpeg"), fw)
        self.fps = QSpinBox(); self.fps.setRange(5, 60); self.fps.setValue(int(cfg.get("fps", 25)))
        form.addRow(T("inst_fps"), self.fps)
        lay.addLayout(form); lay.addStretch(1)
        knr = QHBoxLayout(); knr.addStretch(1)
        ann = QPushButton(T("annuleren")); ann.clicked.connect(self.reject); knr.addWidget(ann)
        ok = QPushButton(T("opslaan")); ok.setObjectName("primair")
        ok.clicked.connect(self._ok); knr.addWidget(ok)
        lay.addLayout(knr)
        QTimer.singleShot(0, lambda: centreer(self, ouder))

    def _kies_ff(self):
        p, _ = QFileDialog.getOpenFileName(self, "ffmpeg", BASIS)
        if p:
            self.ff.setText(p)

    def _download_ff(self):
        ouder = self.parent()
        if ouder is not None and hasattr(ouder, "_download_ffmpeg_auto"):
            # leeg het pad-veld; na download wijst de app naar de nieuwe versie
            if ouder._download_ffmpeg_auto():
                self.ff.setText(ouder.cfg.get("ffmpeg", ""))

    def _ok(self):
        self.cfg["taal"] = self.taal.currentData()
        self.cfg["ffmpeg"] = self.ff.text().strip()
        self.cfg["fps"] = self.fps.value()
        self.accept()


SNELGIDS_NL = """
<h2>DraveShot - Snelgids</h2>
<p>Maak <b>schermafbeeldingen</b> en <b>schermopnames</b> en zet er tekst, pijlen
en vormen op. Volledig lokaal.</p>
<h3>Schermafbeelding</h3>
<p><b>Gebied vastleggen</b> (sleep een kader) of <b>Volledig scherm</b>. Annoteer
met de knoppenbalk: tekst, pijl, lijn, rechthoek, ovaal, pen, markeerstift,
<b>vervagen</b> (privacy) en <b>bijsnijden</b>. Daarna <b>Opslaan als</b> of
<b>naar klembord</b>.</p>
<h3>Schermopname (video)</h3>
<p><b>Opname starten</b> (volledig) of <b>Opname (gebied)</b>, dan <b>Stoppen</b>.
Hiervoor is <b>ffmpeg</b> nodig (wijs het aan bij Instellingen, of zet ffmpeg.exe
naast de app). Open daarna de opname en teken annotaties; per annotatie stel je
met <b>Van/Tot</b> in wanneer die in beeld is. <b>Exporteren</b> brandt de
annotaties in een nieuwe videofile.</p>
<p><b>Groter zien / verplaatsen:</b> zoom met de knoppen onder het voorbeeld of met Ctrl + scrollwiel; zet de knop op <b>Kiezen/verplaatsen</b> om tekst, pijlen en vormen te verslepen.</p>
<p><b>Tekst:</b> kies <b>Tekst</b> en klik op de plek; je kunt meerdere regels typen (Enter = nieuwe regel). <b>Dubbelklik</b> op bestaande tekst om die te wijzigen. Met <b>Tekstgrootte</b> stel je de grootte in; selecteer eerst een tekst om die achteraf groter/kleiner te maken.</p>
<p>Tip: de schermvastlegging werkt op Windows. Donatie (vrijwillig):
<b>paypal.me/roger076</b> &middot; service@dravenlock.nl</p>
"""
SNELGIDS_EN = """
<h2>DraveShot - Quick guide</h2>
<p>Take <b>screenshots</b> and <b>screen recordings</b> and add text, arrows and
shapes. Fully local.</p>
<h3>Screenshot</h3>
<p><b>Capture region</b> (drag a box) or <b>Full screen</b>. Annotate with the
toolbar: text, arrow, line, rectangle, ellipse, pen, highlighter, <b>blur</b>
(privacy) and <b>crop</b>. Then <b>Save as</b> or <b>to clipboard</b>.</p>
<h3>Screen recording (video)</h3>
<p><b>Start recording</b> (full) or <b>Record (region)</b>, then <b>Stop</b>. This
needs <b>ffmpeg</b> (point to it in Settings, or put ffmpeg.exe next to the app).
Then open the recording and draw annotations; per annotation set <b>From/To</b>
for when it shows. <b>Export</b> burns the annotations into a new video file.</p>
<p><b>See bigger / move:</b> zoom with the buttons below the preview or Ctrl + mouse wheel; switch to <b>Select/move</b> to drag text, arrows and shapes.</p>
<p><b>Text:</b> pick <b>Text</b> and click; you can type multiple lines (Enter = new line). <b>Double-click</b> existing text to change it. Use <b>Text size</b> to set the size; select a text first to resize it afterwards.</p>
<p>Tip: screen capture works on Windows. Donate (voluntary):
<b>paypal.me/roger076</b> &middot; service@dravenlock.nl</p>
"""


class SnelgidsDialoog(QDialog):
    def __init__(self, ouder):
        super().__init__(ouder)
        self.setWindowTitle(T("snelgids")); self.setWindowIcon(app_icoon())
        self.resize(680, 600); self.setStyleSheet(STIJL())
        from PyQt6.QtWidgets import QTextBrowser
        lay = QVBoxLayout(self)
        b = QTextBrowser(); b.setOpenExternalLinks(True)
        b.setHtml(SNELGIDS_NL if _TAAL == "nl" else SNELGIDS_EN)
        lay.addWidget(b)
        k = QPushButton(T("sluiten")); k.clicked.connect(self.accept); lay.addWidget(k)
        QTimer.singleShot(0, lambda: centreer(self, ouder))


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class Hoofdvenster(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.opname = None
        self.stopbalk = None
        self._export = None
        self._video_pad = None
        self.setWindowTitle("%s  v%s" % (APP_NAAM, APP_VERSIE))
        self.setWindowIcon(app_icoon())
        self.resize(1180, 760); self.setStyleSheet(STIJL())
        self._menu()
        self._bouw()

        sb = QStatusBar(); self.setStatusBar(sb)
        self.btn_donatie = QPushButton(" \u2665 " + T("donatie"))
        self.btn_donatie.setObjectName("primair")
        self.btn_donatie.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DONATIE_URL)))
        sb.addPermanentWidget(self.btn_donatie)
        # ffmpeg bij opstarten controleren en zo nodig automatisch ophalen
        QTimer.singleShot(400, self._startup_ffmpeg)

    def _menu(self):
        balk = self.menuBar()
        m = balk.addMenu(T("menu_bestand"))
        a = QAction(T("instellingen"), self); a.triggered.connect(self._instellingen)
        m.addAction(a)
        m.addSeparator()
        a = QAction(T("afsluiten"), self); a.setShortcut("Ctrl+Q")
        a.triggered.connect(self.close); m.addAction(a)
        h = balk.addMenu(T("menu_help"))
        a = QAction(T("snelgids"), self); a.setShortcut("F1")
        a.triggered.connect(lambda: SnelgidsDialoog(self).exec()); h.addAction(a)
        a = QAction(T("over"), self); a.triggered.connect(self._over); h.addAction(a)
        a = QAction(T("donatie"), self)
        a.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(DONATIE_URL)))
        h.addAction(a)

    def _bouw(self):
        from PyQt6.QtWidgets import QTabWidget
        centraal = QWidget(); self.setCentralWidget(centraal)
        lay = QVBoxLayout(centraal)
        kop = QLabel(APP_NAAM); kop.setObjectName("titel"); lay.addWidget(kop)
        sub = QLabel(T("ondertitel")); sub.setObjectName("sub"); lay.addWidget(sub)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_foto(), T("tab_foto"))
        self.tabs.addTab(self._tab_video(), T("tab_video"))
        lay.addWidget(self.tabs, 1)

    def _zoombalk(self, view):
        rij = QHBoxLayout(); rij.setContentsMargins(0, 0, 0, 0)
        for lbl, fn in ((T("zoom_uit"), view.zoom_uit),
                        (T("passend"), view.passend),
                        (T("zoom_in"), view.zoom_in),
                        (T("honderd"), view.honderd)):
            b = QPushButton(lbl); b.clicked.connect(fn); rij.addWidget(b)
        tip = QLabel(T("zoom_tip")); tip.setObjectName("sub")
        rij.addWidget(tip, 1)
        w = QWidget(); w.setLayout(rij)
        return w

    # ---- foto-tab ----
    def _tab_foto(self):
        w = QWidget(); lay = QVBoxLayout(w)
        rij = QHBoxLayout()
        b1 = QPushButton(T("vastleggen_gebied")); b1.setObjectName("primair")
        b1.clicked.connect(lambda: self._foto_vastleggen(True)); rij.addWidget(b1)
        b2 = QPushButton(T("vastleggen_volledig"))
        b2.clicked.connect(lambda: self._foto_vastleggen(False)); rij.addWidget(b2)
        b3 = QPushButton(T("open_afbeelding")); b3.clicked.connect(self._open_afbeelding)
        rij.addWidget(b3)
        rij.addWidget(QLabel(T("vertraging")))
        self.vertraging = QSpinBox(); self.vertraging.setRange(0, 10)
        self.vertraging.setValue(int(self.cfg.get("vertraging", 0)))
        rij.addWidget(self.vertraging)
        rij.addStretch(1)
        bs = QPushButton(T("opslaan_als")); bs.clicked.connect(self._foto_opslaan)
        rij.addWidget(bs)
        bk = QPushButton(T("kopieer")); bk.clicked.connect(self._foto_kopieer)
        rij.addWidget(bk)
        lay.addLayout(rij)

        self.foto_scene = TekenScene()
        self.foto_balk = Gereedschapsbalk(self.foto_scene, met_bijsnijden=True)
        lay.addWidget(self.foto_balk)
        self.foto_view = ZoomView(self.foto_scene)
        lay.addWidget(self._zoombalk(self.foto_view))
        lay.addWidget(self.foto_view, 1)
        self.foto_info = QLabel(T("foto_leeg")); self.foto_info.setObjectName("sub")
        lay.addWidget(self.foto_info)
        return w

    def _foto_vastleggen(self, gebied):
        if not WINDOWS:
            QMessageBox.information(self, APP_NAAM, T("alleen_windows")); return
        self.showMinimized()
        QApplication.processEvents()
        time.sleep(0.3 + int(self.vertraging.value()))
        rect = None
        if gebied:
            schermpix = leg_scherm_vast()
            ov = GebiedOverlay(schermpix)
            ov.exec()
            rect = ov.gekozen
            self.showNormal()
            if rect is None:
                return
            pix = schermpix.copy(rect)
        else:
            pix = leg_scherm_vast(); self.showNormal()
        self._zet_foto(pix)

    def _open_afbeelding(self):
        p, _ = QFileDialog.getOpenFileName(self, T("open_afbeelding"), BASIS,
                                           "Afbeeldingen (*.png *.jpg *.jpeg *.bmp)")
        if p:
            pix = QPixmap(p)
            if not pix.isNull():
                self._zet_foto(pix)

    def _zet_foto(self, pix):
        self.foto_scene.wis_alles()
        self.foto_scene.zet_achtergrond(pix)
        self.foto_view.passend()
        self.foto_info.setText("%d x %d" % (pix.width(), pix.height()))

    def _foto_opslaan(self):
        if self.foto_scene.bg is None:
            return
        p, _ = QFileDialog.getSaveFileName(self, T("opslaan_als"),
                                           os.path.join(OPNAME_MAP,
                                           time.strftime("schermafbeelding_%Y%m%d_%H%M%S.png")),
                                           "PNG (*.png);;JPEG (*.jpg)")
        if not p:
            return
        img = self.foto_scene.render_plat()
        img.save(p)
        self.statusBar().showMessage(T("opgeslagen").format(pad=p), 6000)

    def _foto_kopieer(self):
        if self.foto_scene.bg is None:
            return
        img = self.foto_scene.render_plat()
        QApplication.clipboard().setPixmap(QPixmap.fromImage(img))
        self.statusBar().showMessage(T("gekopieerd"), 4000)

    # ---- video-tab ----
    def _tab_video(self):
        w = QWidget(); lay = QVBoxLayout(w)
        rij = QHBoxLayout()
        self.b_op = QPushButton(T("opname_starten")); self.b_op.setObjectName("primair")
        self.b_op.clicked.connect(lambda: self._opname_start(False)); rij.addWidget(self.b_op)
        self.b_opg = QPushButton(T("opname_gebied"))
        self.b_opg.clicked.connect(lambda: self._opname_start(True)); rij.addWidget(self.b_opg)
        self.b_stop = QPushButton(T("opname_stoppen")); self.b_stop.setObjectName("gevaar")
        self.b_stop.clicked.connect(self._opname_stop); self.b_stop.setEnabled(False)
        rij.addWidget(self.b_stop)
        bo = QPushButton(T("open_video")); bo.clicked.connect(self._open_video)
        rij.addWidget(bo)
        rij.addStretch(1)
        self.b_export = QPushButton(T("exporteren")); self.b_export.setObjectName("primair")
        self.b_export.clicked.connect(self._video_export); rij.addWidget(self.b_export)
        lay.addLayout(rij)

        self.video_scene = TekenScene()
        self.video_balk = Gereedschapsbalk(self.video_scene, met_bijsnijden=False)
        lay.addWidget(self.video_balk)
        self.video_view = ZoomView(self.video_scene)
        lay.addWidget(self._zoombalk(self.video_view))
        lay.addWidget(self.video_view, 1)

        srij = QHBoxLayout()
        srij.addWidget(QLabel(T("scrub")))
        self.scrub = QSlider(Qt.Orientation.Horizontal); self.scrub.setEnabled(False)
        self.scrub.sliderReleased.connect(self._scrub)
        srij.addWidget(self.scrub, 1)
        self.tijd_lbl = QLabel("0.0 s"); srij.addWidget(self.tijd_lbl)
        lay.addLayout(srij)

        trij = QHBoxLayout()
        trij.addWidget(QLabel(T("tijd_van")))
        self.van = QDoubleSpinBox(); self.van.setRange(0, 99999); self.van.setDecimals(1)
        self.van.valueChanged.connect(self._tijd_gewijzigd); trij.addWidget(self.van)
        trij.addWidget(QLabel(T("tijd_tot")))
        self.tot = QDoubleSpinBox(); self.tot.setRange(0, 99999); self.tot.setDecimals(1)
        self.tot.valueChanged.connect(self._tijd_gewijzigd); trij.addWidget(self.tot)
        self.tijd_info = QLabel(T("tijd_uitleg")); self.tijd_info.setObjectName("sub")
        trij.addWidget(self.tijd_info, 1)
        lay.addLayout(trij)
        self.video_scene.selectionChanged.connect(self._toon_tijd)
        self.video_info = QLabel(T("video_leeg")); self.video_info.setObjectName("sub")
        lay.addWidget(self.video_info)
        self.ffmpeg_status = QLabel(""); self.ffmpeg_status.setWordWrap(True)
        lay.addWidget(self.ffmpeg_status)
        self._werk_ffmpeg_status_bij()
        return w

    def _werk_ffmpeg_status_bij(self):
        if not hasattr(self, "ffmpeg_status"):
            return
        pad = vind_ffmpeg(self.cfg)
        if pad:
            self.ffmpeg_status.setText("ffmpeg: " + pad)
            self.ffmpeg_status.setStyleSheet("color: %s;" % GOED)
        else:
            self.ffmpeg_status.setText(T("ffmpeg_status_niet"))
            self.ffmpeg_status.setStyleSheet("color: %s;" % WARN)

    def _download_ffmpeg_auto(self):
        """Downloadt ffmpeg automatisch (zonder ja/nee-vraag) met voortgangsbalk,
        legt het pad vast en controleert of ffmpeg echt start."""
        dlg = QProgressDialog(T("ffmpeg_downloaden"), T("annuleren"), 0, 100, self)
        dlg.setWindowTitle(APP_NAAM); dlg.setWindowIcon(app_icoon())
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setMinimumDuration(0); dlg.setAutoClose(False); dlg.setAutoReset(False)
        dlg.setValue(0)
        resultaat = {}
        th = FfmpegDownloadThread(DATA_MAP)

        def vooruit(p):
            if p < 0:
                dlg.setRange(0, 0)
            else:
                dlg.setRange(0, 100); dlg.setValue(p)

        from PyQt6.QtCore import QEventLoop
        lus = QEventLoop()

        def gereed(ok, info):
            resultaat["ok"] = ok; resultaat["info"] = info
            dlg.reset(); lus.quit()

        th.voortgang.connect(vooruit); th.klaar.connect(gereed)
        dlg.canceled.connect(th.stop)
        th.start(); dlg.show(); lus.exec(); th.wait(5000)

        if resultaat.get("ok"):
            pad = resultaat["info"]
            self.cfg["ffmpeg"] = pad
            bewaar_config(self.cfg)
            if self._ffmpeg_werkt(pad):
                QMessageBox.information(self, APP_NAAM, T("ffmpeg_klaar"))
                return True
            QMessageBox.warning(self, APP_NAAM,
                                T("ffmpeg_mislukt").format(fout="ffmpeg start niet"))
            return False
        if resultaat.get("info") and resultaat["info"] != "geannuleerd":
            QMessageBox.warning(self, APP_NAAM,
                                T("ffmpeg_mislukt").format(fout=resultaat["info"]))
        return False

    @staticmethod
    def _ffmpeg_werkt(pad):
        try:
            r = subprocess.run([pad, "-version"], capture_output=True,
                               **_zonder_venster())
            return r.returncode == 0
        except Exception:
            return False

    def _zorg_ffmpeg(self):
        """True als ffmpeg beschikbaar is; downloadt het anders automatisch."""
        if vind_ffmpeg(self.cfg):
            return True
        if not WINDOWS:
            QMessageBox.warning(self, APP_NAAM, T("geen_ffmpeg")); return False
        ok = self._download_ffmpeg_auto()
        self._werk_ffmpeg_status_bij()
        return ok

    def _startup_ffmpeg(self):
        """Bij opstarten: ontbreekt ffmpeg, haal het meteen automatisch op."""
        if WINDOWS and not vind_ffmpeg(self.cfg):
            self._download_ffmpeg_auto()
        self._werk_ffmpeg_status_bij()

    def _opname_start(self, gebied):
        if not WINDOWS:
            QMessageBox.information(self, APP_NAAM, T("alleen_windows")); return
        if not self._zorg_ffmpeg():
            return
        rect = None
        if gebied:
            ov = GebiedOverlay(leg_scherm_vast())
            ov.exec()
            rect = ov.gekozen
            if rect is None:
                return
        doel = os.path.join(OPNAME_MAP, time.strftime("opname_%Y%m%d_%H%M%S.mp4"))
        self.opname = OpnameProces(self.cfg, doel, rect)
        ok, fout = self.opname.start()
        if not ok:
            QMessageBox.warning(self, APP_NAAM, fout); self.opname = None; return
        self._video_pad = doel
        self.b_op.setEnabled(False); self.b_opg.setEnabled(False); self.b_stop.setEnabled(True)
        self.video_info.setText(T("opnemen_bezig"))
        self.stopbalk = StopBalk(self._opname_stop)
        self.stopbalk.plaats(); self.stopbalk.show()
        self.showMinimized()

    def _opname_stop(self):
        if not self.opname:
            return
        self.opname.stop(); self.opname = None
        if self.stopbalk is not None:
            self.stopbalk.close(); self.stopbalk = None
        self.b_op.setEnabled(True); self.b_opg.setEnabled(True); self.b_stop.setEnabled(False)
        self.showNormal(); self.raise_(); self.activateWindow()
        if self._video_pad and os.path.isfile(self._video_pad):
            self._laad_video(self._video_pad)

    def _open_video(self):
        p, _ = QFileDialog.getOpenFileName(self, T("open_video"), BASIS,
                                           "Video (*.mp4 *.mkv *.mov *.avi)")
        if p:
            self._laad_video(p)

    def _laad_video(self, pad):
        self._video_pad = pad
        duur = video_duur(self.cfg, pad)
        self.video_scene._video_duur = duur
        frame = os.path.join(DATA_MAP, "_frame.png")
        if not haal_frame(self.cfg, pad, 0.0, frame):
            QMessageBox.warning(self, APP_NAAM, T("geen_ffmpeg")); return
        pix = QPixmap(frame)
        self.video_scene.wis_alles()
        self.video_scene.zet_achtergrond(pix)
        self.video_view.passend()
        self.scrub.setEnabled(True); self.scrub.setRange(0, int(max(1, duur) * 10))
        self.scrub.setValue(0)
        self.van.setValue(0.0); self.tot.setValue(round(duur, 1))
        self.video_info.setText("%d x %d  -  %.1f s" % (pix.width(), pix.height(), duur))

    def _scrub(self):
        if not self._video_pad:
            return
        t = self.scrub.value() / 10.0
        self.tijd_lbl.setText("%.1f s" % t)
        frame = os.path.join(DATA_MAP, "_frame.png")
        if haal_frame(self.cfg, self._video_pad, t, frame):
            self.video_scene.bg.setPixmap(QPixmap(frame))

    def _toon_tijd(self):
        items = [it for it in self.video_scene.selectedItems()
                 if it in self.video_scene.tijden]
        if items:
            van, tot = self.video_scene.tijden[items[0]]
            self.van.blockSignals(True); self.tot.blockSignals(True)
            self.van.setValue(van); self.tot.setValue(tot)
            self.van.blockSignals(False); self.tot.blockSignals(False)

    def _tijd_gewijzigd(self):
        for it in self.video_scene.selectedItems():
            if it in self.video_scene.tijden:
                self.video_scene.tijden[it] = (self.van.value(), self.tot.value())

    def _video_export(self):
        if not self._video_pad or not self.video_scene.annotaties:
            return
        if not self._zorg_ffmpeg():
            return
        doel, _ = QFileDialog.getSaveFileName(
            self, T("exporteren"),
            os.path.join(OPNAME_MAP, time.strftime("video_geannoteerd_%Y%m%d_%H%M%S.mp4")),
            "MP4 (*.mp4)")
        if not doel:
            return
        # groepeer annotaties per (van,tot) en render overlays
        groepen = {}
        for it in self.video_scene.annotaties:
            groepen.setdefault(self.video_scene.tijden[it], []).append(it)
        overlays = []
        for i, ((van, tot), items) in enumerate(groepen.items()):
            img = self.video_scene.render_overlay(items)
            pad = os.path.join(DATA_MAP, "_overlay_%d.png" % i)
            img.save(pad)
            overlays.append((pad, van, tot))
        self.statusBar().showMessage(T("bezig_export"))
        self.b_export.setEnabled(False)
        self._export = ExportThread(self.cfg, self.video_scene, self._video_pad, doel)
        self._export.overlays = overlays
        self._export.klaar.connect(self._export_klaar)
        self._export.start()

    def _export_klaar(self, ok, pad):
        self.b_export.setEnabled(True)
        if ok:
            self.statusBar().showMessage(T("export_klaar").format(pad=pad), 8000)
            QMessageBox.information(self, APP_NAAM, T("export_klaar").format(pad=pad))
        else:
            self.statusBar().showMessage(T("export_fout"), 8000)
            QMessageBox.warning(self, APP_NAAM, T("export_fout"))

    # ---- menu-acties ----
    def _instellingen(self):
        global _TAAL
        d = InstellingenDialoog(self, self.cfg)
        if d.exec():
            bewaar_config(self.cfg)
            nieuw = self.cfg.get("taal", "auto")
            _TAAL = taal_detecteren() if nieuw == "auto" else nieuw
            self._werk_ffmpeg_status_bij()
            QMessageBox.information(self, APP_NAAM, T("herstart_taal"))

    def _over(self):
        QMessageBox.information(self, T("over"), T("over_tekst").format(
            versie=APP_VERSIE, contact=CONTACT, donatie=DONATIE_URL))

    def closeEvent(self, ev):
        try:
            if self.opname:
                self.opname.stop()
        except Exception:
            pass
        ev.accept()


def main():
    global _TAAL
    zorg_voor_mappen()
    cfg = laad_config()
    taal = cfg.get("taal", "auto")
    _TAAL = taal_detecteren() if taal == "auto" else (taal if taal in ("nl", "en")
                                                      else taal_detecteren())
    if WINDOWS:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Dravenlock.DraveShot")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAAM)
    app.setWindowIcon(app_icoon())
    app.setStyleSheet(STIJL())
    venster = Hoofdvenster(cfg)
    venster.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
