# FOQUS Install

## Install Python

Python 3.6 or higher is required to run FOQUS. [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download/) are convenient Python distributions, but the choice of interpreter is up to the user. One advantage of using Miniconda or Anaconda is that it is easy to create self-contained environments, which can help with managing package version dependencies. This guide will walk through the installation process with a few optional steps for installing Miniconda and setting up an environment.

If you have a working version of Python 3.6 or greater, which you prefer over Anaconda,
you can skip steps 1 to 4.

1. Get the correct version of [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for your environment, preferably a Python 3 version, but Python and 3.x environments can be installed with either.  
2. Install Miniconda by running the installer, and following a few simple prompts.
3. Set up a foqus environment.
  > conda create -n foqus python=3 pip
4. Activate the environment
  - Linux: > source activate foqus
  - Windows: > conda activate foqus

If you create an environment in which to install FOQUS, you will need to ensure that environment is active before running FOQUS.

## Install git

Git can be used for developers who want to contribute to FOQUS, but it is also used to install some FOQUS requirements. There are a few ways to install git. If you are using Anaconda, it can be installed with conda. Otherwise, git clients can be found here https://git-scm.com/download/.ref

5. Install git
  - Option 1:
  > conda install git
  - Option 2: Download and install the git client of your choice

## Get FOQUS

There are 2 ways to get FOQUS either download it from the [github page](https://github.com/CCSI-Toolset/FOQUS) or if you are a developer and would like to contribute, you can fork the repository and clone your fork.

5. Download FOQUS
  - Get a tagged release [here](https://github.com/CCSI-Toolset/FOQUS/releases),
  - Click the clone or download button [here](https://github.com/CCSI-Toolset/FOQUS) to get the latest development version. or
  - Use the git client to clone your fork of FOQUS (if you want to contribute)
6. If you downloaded a zip file extract the FOQUS source to a convenient location.

## Install FOQUS

7. Open the Anaconda prompt (or appropriate terminal or shell depending on operating system and choice of Python), and change to the directory containing the FOQUS files.
8. If you set up a "foqus" conda environment activate it
  - On Windows:
  > conda activate foqus
  - On Linux and OSX:
  > source activate foqus
9. Install requirements:
  > pip install –r requirements.txt
10. Install FOQUS.  The in-place install will allow you to easily edit source code while the regular install will install FOQUS in the central Python library location, and not allow editing of the source code.
  - Install in-place:
  > python setup.py develop
  - Regular install:
  > python setup.py install

## Test FOQUS Installation

11. Run foqus:
  - On Windows a batch file (foqus.bat) is created in the source directory.  This can be moved to any convenient location, and linked by a Windows shortcut if desired.  Start FOQUS by running the batch file.  The batch file should run FOQUS in the appropriate conda environment, if an Anaconda environment was used.
  - On Linux or OSX launch foqus in a terminal.  Activate the appropriate conda environment if necessary.
  > foqus.py
12. The first time FOQUS is run it will as for a working directory location.  This is the location FOQUS will put any working files.  This setting can be changed later.

## Install Optional Software

There are several optional pieces of software which are not written in Python and not easily installed automatically. There are a couple packages which most users would want to install.  The first is PSUADE, which provides FOQUS UQ functionality. The second is Turbine which is requires Windows, and is used to interface with Excel, Aspen, and gPROMS software.

Other software listed below will enable additional features of FOQUS if available.

### Install PSUADE (current version: 1.7.12)

PSUADE is short for *Problem Solving environment for Uncertainty Analysis and Design Exploration*. It is a software toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the [psuade github](https://github.com/LLNL/psuade). For Windows users, there is an [executable](https://github.com/LLNL/psuade/releases) for your convenience.

### Install Turbine and SimSinter (Windows Only)
* This requires [Microsoft SQL Server Compact 4.0](https://www.microsoft.com/en-us/download/details.aspx?id=17876).
* Download and install the [SimSinter](https://github.com/CCSI-Toolset/SimSinter/releases/) and [TurbineLite](https://github.com/CCSI-Toolset/turb_sci_gate/releases/) installers.
* Install SimSinter first, then TurbineLite.
* After the install the Turbine Web API Service Will start automatically when Windows starts, but it will not start directly after the install. Do one of these two things (only after install).
    * Restart computer, or
    * Start the "Turbine Web API service": (1) open Task Manager, (2) go to the "Services" tab, (3) click the "Services" button (in the lower right corner), (4) right-click "Turbine Web API Service" from the list, and (5) click "Start"

### Install ALAMO

ALAMO is short for *Automated Learning of Algebraic Models for Optimization*. It is a software toolkit that generates algebraic models of simulations, experiments, or other black-box systems. For more information, click [here](http://archimedes.cheme.cmu.edu/?q=alamo).

Download and request a license from the [ALAMO download page](https://minlp.com/alamo-downloads).

### Install NLopt

NLopt is an optional optimization library, which can be used by FOQUS. Unfortunately,
the Python module is not available to be installed with pip. For installation
instructions, click [here](https://nlopt.readthedocs.io/en/latest/), or NLopt can be installed with conda as follows:

``conda install -c conda-forge nlopt``

### Install R

R is a software toolbox for statistical computing and graphics. R version 3.1+ are required for the ACOSSO and BSS-ANOVA surrogate models and the Basic Data's SolventFit model.

* Follow instructions from the [R website](http://cran.r-project.org/) to download and install R.
* Open R and type the following to install and load the prerequisite packages:
   * install.packages(‘quadprog’)
   * library(quadprog)
   * install.packages(‘abind’)
   * library(abind)
   * install.packages(‘MCMCpack’)
   * library(MCMCpack)
   * install.packages(‘MASS’)
   * library(MASS)
   * q()
* The last command exits R. When asked to save workspace image, type "y".
* Open FOQUS, go to the “Settings” tab, and set the “RScript Path” to the proper location of the R executable.

## Optional FOQUS Settings
* Go to the FOQUS settings tab.
  - Set ALAMO and PSUADE locations.
  - Test TurbineLite config.

## Automated tests (from top level of foqus repo)
``python foqus.py -s test/system_test/ui_test_01.py``

## Troubleshooting

* Error "Cannot import adodbapi.base." This error may occur if pywin32 installs an older version of adodbapi.  Uninstalling and reinstalling the latest version should fix the problem. ```pip uninstall adodbapi``` then ```pip install adodbapi``` has been found to resolve it.
