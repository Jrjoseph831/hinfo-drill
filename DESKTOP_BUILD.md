# Building the Desktop App

Health Informatics Drill can run as a **web app** (Flask) or as a **standalone desktop application** for Windows and macOS.

## Quick Build

```bash
# One command does it all — installs deps and builds the executable
python build_desktop.py
```

The finished executable lands in the `dist/` folder:

| Platform | Output |
|----------|--------|
| Windows  | `dist/HealthInformaticsDrill.exe` |
| macOS    | `dist/HealthInformaticsDrill.app` |
| Linux    | `dist/HealthInformaticsDrill` |

## Manual Build

### 1. Install dependencies

```bash
pip install -r requirements-desktop.txt
```

### 2. Run PyInstaller

```bash
pyinstaller --clean --noconfirm hinfo_drill.spec
```

### 3. Run the app

Double-click the executable, or from a terminal:

```bash
# Windows
dist\HealthInformaticsDrill.exe

# macOS
open dist/HealthInformaticsDrill.app

# Linux
./dist/HealthInformaticsDrill
```

## Browser-Only Mode

If you don't want the native window (skips pywebview), build or run with `--browser`:

```bash
# Run from source in browser mode
python desktop_app.py --browser

# Build without pywebview
python build_desktop.py --browser
```

## How It Works

- `desktop_app.py` — Starts the Flask server on a random free port, then opens the UI in a native window (pywebview) or browser.
- `hinfo_drill.spec` — PyInstaller spec that bundles everything (templates, static files, scenarios, database module) into a single executable.
- `build_desktop.py` — Convenience script that installs deps and runs PyInstaller.

The database (`hinfo_drill.db`) is created automatically on first launch in the working directory.

## Requirements

- Python 3.9+
- ~150–250 MB disk space for the built executable (varies by platform)

## Troubleshooting

**"pywebview not installed" warning**: The app will fall back to opening in your default browser. Install pywebview (`pip install pywebview`) for the native window experience.

**Antivirus flags on Windows**: Some antivirus software flags PyInstaller executables. This is a known false positive. You can whitelist the executable or build with `--browser` mode to skip pywebview (which reduces the binary surface area).

**macOS Gatekeeper**: On first launch, macOS may block the app. Right-click → Open, or go to System Settings → Privacy & Security → Open Anyway.
