# -*- mode: python ; coding: utf-8 -*-
import os

# Frontend dist folder — same directory structure assume karo
FRONTEND_DIST = os.path.join('..', 'frontend', 'dist')

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        (FRONTEND_DIST, 'dist'),           # frontend build files
    ],
    hiddenimports=[
        'email_sender',
        'tracker',
        'psycopg2',
        'psycopg2.extras',
        'psycopg2._psycopg',
        'dotenv',
        'imaplib',
        'email',
        'email.mime.text',
        'email.mime.multipart',
        'smtplib',
        'urllib.parse',
        'threading',
        'flask',
        'flask_cors',
        'webview',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='OutreachOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # Window app — no black terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Icon add karna ho to: icon='icon.ico'
)
