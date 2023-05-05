#!/bin/bash
echo Installing missing packages...
pip install -r requirements.txt
python -m swarmai.__main__
read -p "Press any key to continue..."
