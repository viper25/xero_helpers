del /s /q .\dist\*
rd /s /q build
rd /s /q __pycache__
pyinstaller --icon stosc_ico.ico --version-file winver.rc --onefile --distpath .\dist ui_main.py