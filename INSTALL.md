# FOQUS Install

## Install Python

Install Python 2.7 with PyQt5.  The Anaconda Python distribution is the recommended way to install Python (https://www.anaconda.com/download/#windows). Anaconda comes with most required packages and the latest versions 
have PyQt5 by default. These instructions will assume you are using Anaconda.

## Install a Git Client

If you do not have a git client install one.  For Windows, a client can be found here: https://git-scm.com/downloads.

It is possible to install git through Anaconda (```conda install git```).

## Install FOQUS

There are 2 ways to install FOQUS the first is preferred if you are a developer 
or want to modify FOQUS. The second way is probably easiest for other users.

1. Developers and users interested in the FOQUS code:
  * Clone the FOQUS repository
  * ``python setup.py develop``
2. Other Users:
  * ``pip install git+https://github.com/CCSI-toolset/foqus@master``
  
## Install Optional Software

### Install Turbine and SimSinter (Windows Only)
* This requires Microsoft SQL Server Compact 4.0
    * https://www.microsoft.com/en-us/download/details.aspx?id=17876
* At https://www.acceleratecarboncapture.org/, Log in and go to products page
* Download and install FOQUS Bundle
* **Unintall outdated FOQUS and PSUADE that are installed (windows control pannel)**
* Do one of these two things (only after install)
    * restart computer
    * or start the "Turbine Web API service"

### Install PSUADE (current version: 1.7.10)

PSUADE is short for *Problem Solving environment for Uncertainty Analysis and Design Exploration*. It is a software toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the [psuade github](https://github.com/LLNL/psuade). For Windows users, there is an [executable](https://github.com/LLNL/psuade/releases) for your convenience.

### Install ALAMO
- http://www.minlp.com/home
- Request a license
- Download Windows installer

### Install NLopt

NLopt is an optional optimization library, which can be used by FOQUS. Unfortunately
the Python module is not available to be installed with pip. For installation 
instructions see https://nlopt.readthedocs.io/en/latest/, or NLopt can be installed with conda.

```conda install -c conda-forge nlopt```

### Install online documentation


## Optional FOQUS Settings
* Go to the FOQUS settings tab
  - Set ALAMO and PSUADE locations
  - Test TurbineLite config

## Automated tests (from top level of foqus repo)
	- ```python fouqs.py -s python foqus.py -s test/system_test/ui_test_01.py```
	- ...




