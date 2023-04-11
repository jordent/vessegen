# **Vessegen Software**

Vessegen Software is a Python Package to control a custom-made bioreactor. It was designed to run off of a Raspberry Pi. Thus, this software will likely not be useful anywhere else or to anyone except for the lab it was designed for.

## **Requirements**

This tutorial assumes you are using a Raspberry Pi with the most up to date Raspbian OS. At the time of writing, we were using a Raspberry Pi 3B running Raspian GNU/Linux 11 (Bullseye).

## **Installation**

To complete installation, an external mouse or keyboard will be needed. Alternatively, you could just ahead to **Additional Touch Screen Optimization** to set up the keyboard and right-click functionality if you are using a touch screen and then come back to these steps. To start installation, first clone the git repo.

```bash
sudo apt-get install git
git clone https://github.com/jordent/vessegen.git
cd ./vessegen
```

Our package comes with some scripts to make installation easier. To use these scripts, give the scripts executable permissions by typing the following command into the terminal. Note: you must be in your vessegen directory.

```bash
chmod +x ./bin/*
```

Now you can simply run the installation script.

```bash
./bin/install-vessegen.sh
```
The software should now be installed. You can run Vessegen software from the command line by typing the following.
```bash
./bin/run-vessegen.sh
```

## **Create a Desktop Executable**

The easiest way to use this software is to set up the Raspberry Pi to have an executable shortcut on the desktop. To do that, first start with the installation above and ensure that dependencies have been installed. Then, run the install desktop script.

```bash
./bin/install-desktop.sh
```

After reboot, there should now be an executable on the desktop that can be run.

## Getting an Update

You can always check for an update by using git.

```bash
cd ./vessegen # Navigate to your vessegen folder
git fetch
git status
git pull
```

If an update pulls, reinstall.

```bash
./bin/install-vesegen.sh
```

## **Notable Raspberry Pi Preferences**
If using a 7 inch LCD touch screen like we did, the first thing you should do is comfirm that the OS is set to a medium screen size. To do that, do the following:

> Top Left Menu &rarr; Preferences &rarr; Appearance Settings &rarr; Defaults &rarr; For medium screens &rarr; Set Defaults

This is a good base to start, but we found some additional customization was helpful. First, you can change the background image.

> Top Left Menu &rarr; Preferences &rarr; Appearance Settings &rarr; Desktop &rarr; Picture &rarr; RPiSystem.png

With the new image, it may be helpful to change desktop text color to black.

> Top Left Menu &rarr; Preferences &rarr; Appearance Settings &rarr; Desktop &rarr; Text Colour &rarr; Black.png

We found that we didn't need the wastebasket icon on the desktop.

> Top Left Menu &rarr; Preferences &rarr; Appearance Settings &rarr; Desktop &rarr; Uncheck Wastebasket

It is also useful to verify that the tasbar menu will be large enough to use.

> Top Left Menu &rarr; Preferences &rarr; Appearance Settings &rarr; Menu Bar &rarr; Size &rarr; Very Large

Our software was designed to fit on a 7-inch 1024x600 LCD touch screen. To get the GUI to fit on that sized screen, you should minimize the task bar when not in use. To do that, you can change the following setting.

> Right Click Taskbar &rarr; Panel Settings &rarr; Advanced &rarr; Automatic hiding &rarr; Check *Minimize panel when not in use* and Set *Size when minimized* to 5 pixels

You also may have want to increase the size of the Desktop Executable. To do so, simply go to the following:

> File Manager &rarr; Edit &rarr; Preferences &rarr; Display &rarr; Size of big icons: 256x256

In order to make the touch screen fit correctly and have correct calibration, we need to disable *Overscan*.

> Top Left Menu &rarr; Raspberry Pi Configuration &rarr; Display &rarr; Overscan (disable)

You may have noticed that when running the executable on the desktop, you are prompted about what you want to do with it. This is changeable by doing checking the following setting:

> File Manager &rarr; Edit &rarr; Preferences &rarr; General &rarr; Don't ask options on launch executable file

For a touch screen display, it is recommended to set the executable to run on a single click. To do this, simply do the following:

> File Manager &rarr; Edit &rarr; Preferences &rarr; General &rarr; Open files with single click

## **Additional Touch Screen Optimization**
Our setup involved using a 7 inch LCD touch screen. If going this route, some nice things to set up are an onscreen keyboard, right-click touch screen functionality, and other optimizations. This step may be dependent on your specific touch screen, but for us the optimizations we ran can be found [here](https://docs.sunfounder.com/projects/ts-7/en/latest/quick_user_guide.html).
