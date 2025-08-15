# Overlay OCR Translator (Windows)

Translates English text inside any app window on the fly using OCR and overlays the translated Russian text in-place.
- Window tracking: follows movement/resizing, multi-monitor, DPI-aware
- OCR: Tesseract (word/line bounding boxes)
- Translation: Argos Translate (offline en→ru model)
- Overlay: click-through, always-on-top, per-box font autosizing to avoid overlap

## Requirements
- Windows 10/11
- Python 3.10+
- Tesseract OCR (Windows installer) from UB Mannheim: https://github.com/UB-Mannheim/tesseract/wiki
  - After install, ensure `tesseract.exe` is in PATH or set TESSERACT_PATH in `.env` (optional)

## Install
```bash
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements.txt
python -m argostranslate.package install translate-en_ru
```
If `argos` model install fails, the app will try to fetch it on first run.

## Run
```bash
python main.py
```
- Select a target window by title
- Press Start. The overlay will appear sized to the window and update automatically.
- Tray: Right-click to exit.

## Controls
- F9: Toggle overlay on/off
- F10: Force re-OCR

## Notes
- Performance: OCR is throttled (~1/sec) and skipped if frame not changed
- Privacy: Runs locally; no cloud calls by default
- Fallback: If Argos model not found and download blocked, app shows original text (no translation)

## Known limitations
- Complex UIs with dynamic effects may require lower OCR interval or per-app tuning
- Accuracy depends on font rendering and Tesseract language data