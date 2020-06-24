#!/usr/bin/env python

import os
import pathlib as pl

import winshell

# Define all the file paths needed for the shortcut
desktop = pl.Path(winshell.desktop())
conda_base = pl.Path(os.environ['CONDA_PREFIX_1'])
conda_env = pl.Path(os.environ['CONDA_PREFIX'])
win32_cmd = str(pl.Path(winshell.folder('CSIDL_SYSTEM')) / 'cmd.exe')
icon = str(conda_base / "Menu" / "Iconleak-Atrous-Console.ico")

# This will point to My Documents/py_work. Adjust to your preferences
my_working = str(pl.Path(winshell.folder('PERSONAL')) / "ccsi-foqus")
link_filepath = str(desktop / "ccsi-foqus.lnk")

# Build up all the arguments to cmd.exe
# Use /K so that the command prompt will stay open
arg_str = "/K " + str(conda_base / "Scripts" / "activate.bat") + " " + str(conda_env)

# Create the shortcut on the desktop
with winshell.shortcut(link_filepath) as link:
    link.path = win32_cmd
    link.description = "CCSI FOQUS"
    link.arguments = arg_str
    link.icon_location = (icon, 0)
    link.working_directory = my_working
