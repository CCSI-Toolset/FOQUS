# FOQUS Install

## Install Python

Install Python and PyQt5.  For Windows, the Anaconda Python distribution is 
convenient. It comes with most required packages and the latest versions 
have PyQt5 by default. PyQt5 is easily installed with Anaconda, but the 
packaging seems to vary of other versions of Python and operating conditions, 
so including it as a requirement in the installer is not very easy. 

If possible, it is convenient to set the Anaconda Python application to open
*.py files on Windows. The foqus.py script is installed later in Anaconda's 
scripts directory and can be executed by just typing ``foqus.py``, but it will be 
executed by the interpreter that Windows associates with Python files.

## Install a Git Client

If you do not have a git client install one.

## Install FOQUS

There are 2 ways to install FOQUS the first is preferred if you are a developer 
or want to modify FOQUS. The second way is probably easiest for other users.

1. Developers
  * Clone the FOQUS repository
  * ``python setup.py develop``
2. Other Users
  * ``pip install git+https://github.com/CCSI-toolset/foqus@master``
  
Additional components not currently include with FOQUS or the FOQUS bundle are:
* PSUADE for uncertainty quantification and optimization under uncertainty analyses
* DRM-Builder for building dynamic reduced models
* iREVEAL building surrogate models for CFD with kriging
* Data management framework
* Turbine Hydro, used by the Turbine Gateway to move simulation files from
  the main Turbine database to TurbineLite instances on worker nodes

## [Optional] Install PSUADE 1.7.10

PSUADE is short for *Problem Solving environment for Uncertainty Analysis and Design Exploration*. It is a software toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the [psuade github](https://github.com/LLNL/psuade). For Windows users, there is an [executable](https://github.com/LLNL/psuade/releases) for your convenience.

## [Optional] Install NLopt

NLopt is an optional optimization library, which can be used by FOQUS. Unfortunately
the Python module is not available to be installed with pip. For installation 
instructions see https://nlopt.readthedocs.io/en/latest/, or NLopt can be installed with conda.

```conda install -c conda-forge nlopt```







