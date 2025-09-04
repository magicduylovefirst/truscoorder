# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

# Collect all playwright data and binaries
playwright_datas, playwright_binaries, playwright_hiddenimports = collect_all('playwright')

# Collect all data files and binaries
datas = []
binaries = []
hiddenimports = []

# Add playwright data and binaries
datas += playwright_datas
binaries += playwright_binaries
hiddenimports += playwright_hiddenimports

# Add local modules and data files (EXCLUDING credentials.json for security)
datas += [
    ('config.py', '.'),
    ('GoQ', 'GoQ'),
    ('Orange', 'Orange'),
    ('Rakuraku', 'Rakuraku'),
    ('utils.py', '.'),
    ('var.py', '.'),
    ('details.json', '.'),
    ('table_data.json', '.'),
    ('credentials_template.json', '.'),  # Include template, not actual credentials
]

# Add hidden imports for local modules
hiddenimports += [
    'GoQ.GoQ',
    'Orange.Orange', 
    'Rakuraku.Rakuraku',
    'config',
    'utils',
    'var',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)