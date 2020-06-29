#!/usr/bin/env python

""" Create a windows shortcut on the desktop to start FOQUS """
import os
import pathlib as pl
import sys
import winshell

# Define all the file paths needed for the shortcut
desktop = pl.Path(winshell.desktop())
link_filepath = desktop / "ccsi-foqus.lnk"
conda_base = pl.Path(os.environ['CONDA_PREFIX_1'])
activate_bat = conda_base / 'Scripts' / 'activate.bat'
conda_env = pl.Path(os.environ['CONDA_PREFIX'])
foqus_exe = conda_env / 'Scripts' /'foqus.exe'
win32_cmd = pl.Path(winshell.folder('CSIDL_SYSTEM')) / 'cmd.exe'
this_dir = pl.Path(__file__).resolve().parent
icon = this_dir / "foqus.ico"
working_dir = pl.Path(winshell.folder('PERSONAL'))  # "Documents"

# Build up all the arguments to cmd.exe
cmd_args = f"/K {activate_bat} {conda_env} & {foqus_exe} && exit"

if link_filepath.exists():
    print(f'Overwriting shortcut: {link_filepath}')

# Create the shortcut on the desktop
with winshell.shortcut(str(link_filepath)) as link:
    link.path = str(win32_cmd)
    link.description = "CCSI FOQUS"
    link.arguments = cmd_args
    link.icon_location = (str(icon), 0)
    link.working_directory = str(working_dir)
