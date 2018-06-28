# FOQUS Install

## Install Python

Install Python 2.7 with PyQt5. The [Anaconda Python distribution](https://www.anaconda.com/download/#windows) is the recommended way to install Python. Anaconda comes with most required packages and the latest versions
have PyQt5 by default. These instructions will assume you are using Anaconda.

## Install a Git Client

If you do not have a git client, you will need to install one.  For Windows, a client can be found [here](https://git-scm.com/downloads).

It is possible to install git through Anaconda: ``conda install git``

## Install FOQUS

* Clone the FOQUS repository.
* Install FOQUS: ``python setup.py develop``

## Install Optional Software

### Install Turbine and SimSinter (Windows Only)
* This requires [Microsoft SQL Server Compact 4.0](https://www.microsoft.com/en-us/download/details.aspx?id=17876).
* Download and install the [SimSinter](https://github.com/CCSI-Toolset/SimSinter/releases/download/2016.06.00/SimSinterInstaller.msi) and [TurbineLite](https://github.com/CCSI-Toolset/turb_sci_gate/releases/download/2016.06.00/TurbineLite.msi) installers.
* Install SimSinter first, then TurbineLite.
* Do one of these two things (only after install).
    * Restart computer, or
    * Start the "Turbine Web API service": (1) open Task Manager, (2) go to the "Services" tab, (3) click the "Services" button (in the lower right corner), (4) right-click "Turbine Web API Service" from the list, and (5) click "Start" 

### Install PSUADE (current version: 1.7.12)

PSUADE is short for *Problem Solving environment for Uncertainty Analysis and Design Exploration*. It is a software toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the [psuade github](https://github.com/LLNL/psuade). For Windows users, there is an [executable](https://github.com/LLNL/psuade/releases) for your convenience.

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
* The last command exits R. When asked to save workspace image, select "Yes".
* Open FOQUS, go to the “Settings” tab, and set the “RScript Path” to the proper location of the R executable.

### Install online documentation

* Download the [HTML documentation](https://github.com/CCSI-Toolset/foqus/releases/download/1.0.0/FOQUS_User_Manual_HTML.zip).
* Extract html documentation and copy the files to foqus_lib/help/html.

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

