# Vessegen Software

Vessegen Software is a Python Package to control a custom made bioreactor. It was designed to run off of a Raspberry Pi. Thus, this software will likely not be useful anywhere else or to anyone except for the lab it was designed for.

## Create a Desktop Executable

The easiest way to use this software is to setup the Raspberry Pi to use the executables and .desktop files that come with the distribution. To do that, execute the following code.

```bash
chmod +x ./bin/install
./bin/install
```

There should now be an executable on the desktop that can be ran.

## Manual Installation

If you would like to install the Python package and call from the command line, use the package manager [pip](https://pip.pypa.io/en/stable/) to install the dependencies.

```bash
pip install -r requirements.txt
```
Then you can install the Vessegen Software.

```bash
pip install vessegen
```
And then run Vessegen.

```bash
vessegen
```
It is recommended that these installations occur inside of a Python virtual environment. The recommended sequence of commands is the following.

```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install vessegen
vessegen
...
deactivate
```
Note that if installed inside of a virtual environment

```bash
source env/bin/activate
```
will need to get called in the correct directory any time you want

```bash
vessegen
```
to work. Thus, in this instance, it may not be necessary to use the virtual environment.

## Updating the Code

It is not recommended to update the code unless care is taken to not do something that will burn out the Raspberry Pi. Any incorrect code or bugs that result in something happening to the GPIO pins could result in the burning of your Raspberry Pi. Thus, proceed with caution.

If you would like to edit the code, you will need to repackage the software. Ensure all dependencies have been installed, including any packages you may be adding.

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
Now, you can install the Vessegen package in editable mode so that the package will automatically update any time you save the code. Make sure you are in the directory with the **pyproject.toml**.

```bash
pip install -e .
```

In order to update the executable, you need to use **PyInstaller**
```bash
pyinstaller --onefile --windowed --name=vessegen --distpath=./executable --clean vessegen/__main__.py
```
and then rerun the install script.

```bash
./bin/install
```