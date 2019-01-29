# FOQUS Install

## Install Python

Python 3.6 or higher is required to run FOQUS. [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download/) are convenient Python distributions, but the choice of interpreter is up to the user. One advantage of using Miniconda or Anaconda is that it is easy to create self-contained environments, which can help with managing package version dependencies. This guide will walk through the installation process with a few optional steps for installing Miniconda and setting up an environment.

If you have a working version of Python 3.x, which you prefer,
you can skip steps 1 to 4.

1. Get the correct version of [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for your environment, preferably a Python 3 version, but Python and 3.x environments can be installed with either.  
2. Install Miniconda by running the installer, and following a few simple prompts.
3. Set up a foqus environment.
  > conda create -n foqus -python=3
4. Activate the environment
  > source activate foqus

If you create an environment in which to install FOQUS, you will need to ensure that environment is active before running FOQUS.

## Get FOQUS

There are 2 ways to get FOQUS either download it from the [github page](https://github.com/CCSI-Toolset/FOQUS) or if you are a developer and would like to contribute, you can fork the repository and clone your fork.

5. Download FOQUS
  - Get a tagged release [here](https://github.com/CCSI-Toolset/FOQUS/releases), or
  - Click the clone or download button [here](https://github.com/CCSI-Toolset/FOQUS) to get the latest development version.
6. Extract the FOQUS source to a convenient location.
7. Get the documentation.  PDF and HTML versions of the documentation available from the [release page.](https://github.com/CCSI-Toolset/FOQUS/releases)
  - (Optional) to make HTML help available through the FOQUS help menu, put the files from
    the HTML manual zip file in /foqus_lib/help/html before installing.

## Install FOQUS

8. There are two ways to install FOQUS.  The first one is in-place with will leave the FOQUS source where it is and any changes made to these files will result in changes to FOQUS.  This mode is often used by developers but it can be convenient for other users. The other option is to do a regular install which copies compiled FOQUS files to a central Python package location.
  - install in-place
    - > ``python setup.py develop``
    - or if you need to download dependencies over ssh
    - > ``python setup.py develop ssh``
  - regular install
    - > ``python setup.py install``
    - or if you need to download dependencies over ssh
    - > ``python setup.py develop ssh``


## Install Optional Software

There are several optional pieces of software which are not written in Python and not easily installed automatically. There are a couple packages which most users would want to install.  The first is PSUADE, which provides all of FOQUS's UQ features. The second is Turbine which is requires Windows, and is used to interface with Excel, Aspen, and gPROMS software.

Other software listed below will enable additional features of FOQUS if available.

### Install PSUADE (current version: 1.7.12)

PSUADE is short for *Problem Solving environment for Uncertainty Analysis and Design Exploration*. It is a software toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the [psuade github](https://github.com/LLNL/psuade). For Windows users, there is an [executable](https://github.com/LLNL/psuade/releases) for your convenience.

### Install Turbine and SimSinter (Windows Only)
* This requires [Microsoft SQL Server Compact 4.0](https://www.microsoft.com/en-us/download/details.aspx?id=17876).
* Download and install the [SimSinter](https://github.com/CCSI-Toolset/SimSinter/releases/) and [TurbineLite](https://github.com/CCSI-Toolset/turb_sci_gate/releases/) installers.
* Install SimSinter first, then TurbineLite.
* Do one of these two things (only after install).
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

* Error "Cannot import adodbapi.base." The source of this error is unclear, but
```pip uninstall adodbapi``` then ```pip install adodbapi``` has been found to
resolve it.

* If you are using an outdated version of Pandas, there might be issues with
saving the FOQUS file. See [instructions](https://pandas.pydata.org/pandas-docs/stable/install.html) on how to install/update Pandas.
