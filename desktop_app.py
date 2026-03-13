"""
desktop_app.py - Desktop launcher for Health Informatics Drill.

Starts the Flask server in a background thread and opens the UI in a
native window (via pywebview) or in the default browser as a fallback.

Usage
-----
    python desktop_app.py              # native window (requires pywebview)
    python desktop_app.py --browser    # force browser mode
"""

import os
import sys
import socket
import threading
import time
import webbrowser

# ---------------------------------------------------------------------------
# Resolve paths — works both when running from source and from a PyInstaller
# one-file bundle (where sys._MEIPASS points to the temp extraction folder).
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)


def _find_free_port():
    """Pick a random available port so multiple instances don't collide."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_flask(port):
    """Import and run the Flask app (blocking)."""
    from app import app, DB_PATH
    from database import init_db

    if not os.path.exists(DB_PATH):
        print("Initializing database …")
        init_db(DB_PATH)

    # Disable reloader — it doesn't play well with PyInstaller or threads
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def _wait_for_server(port, timeout=15):
    """Block until the Flask server is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def main():
    use_browser = "--browser" in sys.argv
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Start Flask in a daemon thread so it dies when the window closes
    server_thread = threading.Thread(target=_start_flask, args=(port,), daemon=True)
    server_thread.start()

    print(f"Starting Health Informatics Drill on {url} …")
    if not _wait_for_server(port):
        print("ERROR: Flask server did not start in time.")
        sys.exit(1)

    if use_browser:
        webbrowser.open(url)
        print("Opened in browser. Press Ctrl+C to stop.")
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down.")
        return

    # Try native window via pywebview
    try:
        import webview

        window = webview.create_window(
            "Health Informatics Drill",
            url,
            width=1400,
            height=900,
            min_size=(1024, 700),
        )
        webview.start()
    except ImportError:
        print("pywebview not installed — falling back to browser.")
        webbrowser.open(url)
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down.")


if __name__ == "__main__":
    main()
