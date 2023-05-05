@echo off
echo Installing missing packages...
pip install -r requirements.txt
python -m swarmai.__main__
pause
