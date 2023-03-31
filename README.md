# Vessegen Software

Vessegen Software is a Python Package to control a custom made bioreactor. It was designed to run off of a Raspberry Pi. Thus, this software will likely not be useful anywhere else or to anyone except for the lab it was designed for.

## Installation

To start installation, first clone the git repo.

```bash
sudo apt-get install git
git clone https://github.com/jordent/vessegen.git
cd ./vessegen
```

Now, create a virtual environment to install the dependencies, making sure we have Python.

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv python3-wheel python3-setuptools
python3 -m venv env
source env/bin/activate
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the dependencies.

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
Then you can install the Vessegen Software.

```bash
pip install .
```
And then run Vessegen.

```bash
vessegen
```
When you are done, be sure to deactive the virtual environment
```bash
deactivate
```
## Create a Desktop Executable

The easiest way to use this software is to setup the Raspberry Pi to have an executable shorcut on the desktop. To do that, first start with the installation above and ensure that dependencies have been installed. Then, create the executable using PyInstaller.

```bash
source env/bin/activate
pyinstaller --onefile --windowed --name=vessegen --distpath=./executable --clean vessegen/__main__.py
deactivate
```

Now run the install script to put the executable into the correct place and create the shortcut on the desktop.

```bash
chmod +x ./bin/install
./bin/install
```

There should now be an executable on the desktop that can be ran. Before running, it is reccomended to reboot the system.

## Noteable Raspberry Pi Preferences

You may have noticed that when running the executable on the desktop, you are prompted about what you want to do with it. This is changeable by doing checking the following setting:

*File Manager -> Edit -> Preferences -> General -> Don't ask options on launch executable file*

You also may have want to increase the size of the Desktop Executable. To do so, simply go to the following:

*File Manager -> Edit -> Preferences -> Display -> Size of big icons:*