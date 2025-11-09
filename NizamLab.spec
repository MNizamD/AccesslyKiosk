# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['Accessly.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

b = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure + b.pure, a.zipped_data + b.zipped_data, cipher=block_cipher)

exe1 = EXE(a.scripts, pyz, a.binaries, a.zipfiles, a.datas,
           name='Launcher',
           console=False)

exe2 = EXE(b.scripts, pyz, b.binaries, b.zipfiles, b.datas,
           name='Start',
           console=False)

coll = COLLECT(exe1, exe2,
               a.binaries + b.binaries,
               a.zipfiles + b.zipfiles,
               a.datas + b.datas,
               strip=False,
               upx=True,
               name='NizamLab')
