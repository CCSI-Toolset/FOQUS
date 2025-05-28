.. _install_psuade:

Install PSUADE-Lite (current version: 1.9.0)
--------------------------------------------

PSUADE (Problem Solving environment for Uncertainty Analysis and Design Exploration) is a software
toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity
analysis, design optimization, model calibration, and more.

`PSUADE-Lite <https://github.com/LLNL/psuade-lite>`_ is now available as a Conda package. To install just follow the steps below::

  conda activate ccsi-foqus
  conda install --yes -c conda-forge -c CCSI-Toolset psuade-lite=1.9
  psuade --help  # quickly test that the psuade executable has been installed correctly

The ``psuade`` executable should now be available within the Conda environment's folders, i.e. at the path ``$CONDA_PREFIX/bin/psuade`` (Linux, macOS) or ``%CONDA_PREFIX%\bin\psuade.exe`` (Windows).
Once you set the full path in the corresponding field in the FOQUS GUI "Settings" tab, you should be able to use it normally within FOQUS.