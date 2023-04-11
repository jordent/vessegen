#!/bin/bash

source env/bin/activate
pyinstaller --onefile --windowed --name=vessegen --distpath=./executable --clean vessegen/__main__.py
deactivate
sudo cp ./executable/vessegen /usr/bin/vessegen
sudo cp ./executable/vessegen.png /usr/bin/vessegen.png
sudo cp ./executable/vessegen.desktop /home/pi/Desktop/
sudo reboot