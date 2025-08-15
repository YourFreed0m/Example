import sys
import time
import threading
import hashlib
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

from PySide6 import QtWidgets, QtCore, QtGui
import pytesseract
from PIL import Image
import numpy as np
import mss
import win32gui
import win32con
import win32api
import win32process
from dotenv import load_dotenv
import os

# Translation (Argos)
try:
	from argostranslate import package, translate
	except_import = None
except Exception as e:
	except_import = e
	package = None
	translate = None

load_dotenv()

@dataclass
class OcrBox:
	text: str
	left: int
	top: int
	width: int
	height: int
	conf: float


def list_windows() -> List[Tuple[int, str]]:
	res = []
	def enum_handler(hwnd, _):
		if win32gui.IsWindowVisible(hwnd):
			title = win32gui.GetWindowText(hwnd)
			if title.strip():
				res.append((hwnd, title))
	win32gui.EnumWindows(enum_handler, None)
	return res


def get_window_rect(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
	try:
		rect = win32gui.GetWindowRect(hwnd)
		# account for DPI scaling (use logical coords for capture)
		return rect  # left, top, right, bottom
	except Exception:
		return None


class OverlayWindow(QtWidgets.QWidget):
	def __init__(self):
		super().__init__(flags=QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
		self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
		self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
		self.boxes: List[Tuple[QtCore.QRect, str]] = []
		self.font_cache: Dict[Tuple[int, int, str], QtGui.QFont] = {}

	def set_boxes(self, boxes: List[OcrBox]):
		self.boxes = []
		for b in boxes:
			rect = QtCore.QRect(b.left, b.top, b.width, b.height)
			self.boxes.append((rect, b.text))
		self.update()

	def paintEvent(self, event):
		p = QtGui.QPainter(self)
		p.setRenderHint(QtGui.QPainter.Antialiasing)
		for rect, text in self.boxes:
			if not text:
				continue
			# Autosize font to fit rect width/height, cache by (w,h,text hash)
			key = (rect.width(), rect.height(), hashlib.md5(text.encode('utf-8')).hexdigest())
			font = self.font_cache.get(key)
			if font is None:
				font = QtGui.QFont('Segoe UI')
				# binary search to fit
				lo, hi = 6, max(10, rect.height())
				fm = QtGui.QFontMetrics(font)
				while lo <= hi:
					mid = (lo + hi) // 2
					font.setPointSize(mid)
					fm = QtGui.QFontMetrics(font)
					br = fm.boundingRect(rect, QtCore.Qt.TextWordWrap, text)
					if br.width() <= rect.width() and br.height() <= rect.height():
						lo = mid + 1
					else:
						hi = mid - 1
				font.setPointSize(max(6, hi))
				self.font_cache[key] = font
			p.setFont(font)
			# draw semi-transparent backdrop for readability
			bg = QtGui.QColor(10, 10, 10, 120)
			p.fillRect(rect, bg)
			p.setPen(QtGui.QColor(230, 240, 255))
			p.drawText(rect.adjusted(4, 2, -4, -2), QtCore.Qt.TextWordWrap, text)
		p.end()


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle('Overlay OCR Translator')
		self.resize(520, 420)

		self.combo = QtWidgets.QComboBox()
		self.refresh_btn = QtWidgets.QPushButton('Обновить окна')
		self.start_btn = QtWidgets.QPushButton('Старт')
		self.stop_btn = QtWidgets.QPushButton('Стоп')
		self.interval = QtWidgets.QDoubleSpinBox()
		self.interval.setRange(0.2, 5.0)
		self.interval.setSingleStep(0.1)
		self.interval.setValue(1.0)
		self.status = QtWidgets.QLabel('Готово')

		central = QtWidgets.QWidget()
		self.setCentralWidget(central)
		layout = QtWidgets.QVBoxLayout(central)
		row = QtWidgets.QHBoxLayout()
		row.addWidget(QtWidgets.QLabel('Окно:'))
		row.addWidget(self.combo, 1)
		row.addWidget(self.refresh_btn)
		layout.addLayout(row)
		row2 = QtWidgets.QHBoxLayout()
		row2.addWidget(QtWidgets.QLabel('Интервал OCR (сек):'))
		row2.addWidget(self.interval)
		row2.addStretch(1)
		row2.addWidget(self.start_btn)
		row2.addWidget(self.stop_btn)
		layout.addLayout(row2)
		layout.addWidget(self.status)

		self.overlay = OverlayWindow()
		self.overlay.hide()

		self.refresh_btn.clicked.connect(self.populate_windows)
		self.start_btn.clicked.connect(self.start)
		self.stop_btn.clicked.connect(self.stop)

		self.populate_windows()

		self.ocr_thread: Optional[threading.Thread] = None
		self.stop_flag = threading.Event()
		self.last_frame_hash: Optional[str] = None

		self.translator = None
		self.ensure_translator()

	def ensure_translator(self):
		global except_import
		try:
			if except_import is not None:
				self.status.setText('Argos not available, translation disabled')
				return
			installed = package.get_installed_packages()
			if not any(p.from_code == 'en' and p.to_code == 'ru' for p in installed):
				# try install
				package.update_package_index()
				pkg = next((p for p in package.get_available_packages() if p.from_code=='en' and p.to_code=='ru'), None)
				if pkg:
					package.install_from_path(pkg.download())
			langs = translate.get_installed_languages()
			en = next((l for l in langs if l.code=='en'), None)
			ru = next((l for l in langs if l.code=='ru'), None)
			if en and ru:
				self.translator = en.get_translation(ru)
		except Exception as e:
			self.status.setText(f'Translation unavailable: {e}')

	def populate_windows(self):
		self.combo.clear()
		for hwnd, title in list_windows():
			self.combo.addItem(f'{title} (HWND {hwnd})', userData=hwnd)

	def start(self):
		idx = self.combo.currentIndex()
		if idx < 0:
			return
		hwnd = self.combo.itemData(idx)
		self.stop_flag.clear()
		self.ocr_thread = threading.Thread(target=self.run_loop, args=(hwnd,), daemon=True)
		self.ocr_thread.start()
		self.status.setText('Работает...')

	def stop(self):
		self.stop_flag.set()
		self.overlay.hide()
		self.status.setText('Остановлено')

	def run_loop(self, hwnd: int):
		with mss.mss() as sct:
			while not self.stop_flag.is_set():
				rect = get_window_rect(hwnd)
				if not rect:
					self.status.setText('Окно недоступно')
					break
				left, top, right, bottom = rect
				w = max(1, right - left)
				h = max(1, bottom - top)
				mon = { 'left': left, 'top': top, 'width': w, 'height': h }
				sct_img = sct.grab(mon)
				img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
				# Frame dedup
				frame_hash = hashlib.md5(img.tobytes()).hexdigest()
				if frame_hash == self.last_frame_hash:
					time.sleep(self.interval.value())
					continue
				self.last_frame_hash = frame_hash

				boxes = self.ocr_image(img)
				if self.translator:
					for b in boxes:
						if looks_english(b.text):
							try:
								b.text = self.translator.translate(b.text)
							except Exception:
								pass
				# move/resize overlay
				QtCore.QMetaObject.invokeMethod(self.overlay, 'setGeometry', QtCore.Qt.QueuedConnection,
					QtCore.Q_ARG(QtCore.QRect, QtCore.QRect(left, top, w, h)))
				QtCore.QMetaObject.invokeMethod(self.overlay, 'show', QtCore.Qt.QueuedConnection)
				QtCore.QMetaObject.invokeMethod(self.overlay, 'set_boxes', QtCore.Qt.QueuedConnection,
					QtCore.Q_ARG(list, boxes))

				time.sleep(self.interval.value())

	def ocr_image(self, img: Image.Image) -> List[OcrBox]:
		# Use tesseract data with word-level boxes, then group to lines
		try:
			custom_oem_psm = r'--oem 1 --psm 6 -l eng'
			data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_oem_psm)
			boxes: List[OcrBox] = []
			for i in range(len(data['text'])):
				text = data['text'][i].strip()
				if not text:
					continue
				conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0.0
				if conf < 60:
					continue
				x = int(data['left'][i])
				y = int(data['top'][i])
				w = int(data['width'][i])
				h = int(data['height'][i])
				boxes.append(OcrBox(text=text, left=x, top=y, width=w, height=h, conf=conf))
			# simple line grouping by y overlap
			lines: List[OcrBox] = []
			boxes.sort(key=lambda b: (b.top, b.left))
			for b in boxes:
				placed = False
				for ln in lines:
					if abs((b.top + b.height/2) - (ln.top + ln.height/2)) < max(ln.height, b.height):
						# merge
						ln.text = (ln.text + ' ' + b.text).strip()
						ln.width = max(ln.width, (b.left + b.width) - ln.left)
						ln.height = max(ln.height, b.height)
						placed = True
						break
				if not placed:
					lines.append(OcrBox(text=b.text, left=b.left, top=b.top, width=b.width, height=b.height, conf=b.conf))
			return lines
		except Exception as e:
			self.status.setText(f'OCR error: {e}')
			return []


def looks_english(s: str) -> bool:
	s = s.strip()
	if not s:
		return False
	# Heuristics: contains A-Z letters, not mostly digits/symbols
	letters = sum(c.isalpha() for c in s)
	latin = sum(('A' <= c <= 'Z') or ('a' <= c <= 'z') for c in s)
	return latin >= max(1, letters // 2)


if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	w = MainWindow()
	w.show()
	sys.exit(app.exec())