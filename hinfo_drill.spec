# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Health Informatics Drill.

Build commands:
    Windows:  pyinstaller hinfo_drill.spec
    macOS:    pyinstaller hinfo_drill.spec
"""

import sys
from pathlib import Path

block_cipher = None
base_dir = Path(SPECPATH)

# Collect all data files the app needs at runtime
datas = [
    (str(base_dir / "templates"), "templates"),
    (str(base_dir / "static"), "static"),
    (str(base_dir / "scenarios.py"), "."),
    (str(base_dir / "scenarios_part1.py"), "."),
    (str(base_dir / "scenarios_part2.py"), "."),
    (str(base_dir / "scenarios_part3.py"), "."),
    (str(base_dir / "database.py"), "."),
    (str(base_dir / "synthea_integration.py"), "."),
    (str(base_dir / "tools_audit.py"), "."),
    (str(base_dir / "tools_coding.py"), "."),
    (str(base_dir / "tools_hl7.py"), "."),
    (str(base_dir / "tools_report.py"), "."),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    "flask",
    "jinja2",
    "markupsafe",
    "werkzeug",
    "faker",
    "faker.providers",
    "sqlite3",
    "scenarios",
    "scenarios_part1",
    "scenarios_part2",
    "scenarios_part3",
    "database",
    "synthea_integration",
    "tools_audit",
    "tools_coding",
    "tools_hl7",
    "tools_report",
]

a = Analysis(
    [str(base_dir / "desktop_app.py")],
    pathex=[str(base_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HealthInformaticsDrill",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                    # No terminal window on launch
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                        # Add icon path here if desired
)

# macOS .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="HealthInformaticsDrill.app",
        icon=None,
        bundle_identifier="com.hinfodrill.app",
        info_plist={
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleName": "Health Informatics Drill",
            "NSHighResolutionCapable": True,
        },
    )
