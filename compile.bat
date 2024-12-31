pyinstaller --onefile --windowed --clean --upx-dir "upx" --icon=akashi.ico --distpath=./ --add-data "akashi.ico;." --add-data "file_hashes.bin;." --add-data "img;img" main.py
pause
