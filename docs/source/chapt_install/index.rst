.. _install_label:

Installation
============

Install Python
--------------

Python 3.6 or higher is required to run FOQUS. Miniconda (https://docs.conda.io/en/latest/miniconda.html) or Anaconda (https://www.anaconda.com/download/) are convenient Python distributions, but the choice of interpreter is up to the user. One advantage of using Miniconda or Anaconda is that it is easy to create self-contained environments, which can help managing package version dependencies between different projects. This guide will walk through the installation process with a few optional steps for installing Miniconda and setting up an environment.

If you have a working version of Python 3.6 or greater, which you prefer over Anaconda, you can skip steps 1 to 4.

1. Get the correct version of Miniconda (https://docs.conda.io/en/latest/miniconda.html) for your platform, preferably Python >=3.6, but Python 3.x environments can be installed with the Python 2.7 version.
2. Install Miniconda by running the installer, and following a few simple prompts.
3. Set up a foqus environment; this environment will be referred to as "foqus" in the installation documentation, but you can use any name you like.  If you would like to install multiple version of FOQUS (for example a stable version and the latest development version), this can be done with environments.  In a terminal or, on Windows, in the Anaconda Prompt type ``conda create -n foqus python=3 pip``
4. Activate the environment on Linux in a terminal type: ``source activate foqus`` on Windows in the Anaconda Prompt type: ``conda activate foqus``

If you create an environment in which to install FOQUS, you will need to ensure that environment is active before installing FOQUS. On Windows, once FOQUS is installed a batch file is created that will activate the proper environment when running FOQUS. On Linux or Mac, you will need to activate the appropriate environment before running FOQUS.

.. Install git
.. -----------

.. Git can be used for developers who want to contribute to FOQUS, but it is also used to install some FOQUS requirements. There are a few ways to install git. If you are using Anaconda, it can be installed with conda. Otherwise, git clients can be found here https://git-scm.com/download/.ref

.. 5. Install git

..   * Option 1, use conda: ``conda install git``
..   * Option 2: download and install the git client of your choice

Get FOQUS
---------

There are 2 ways to get FOQUS either download it from the github page (https://github.com/CCSI-Toolset/FOQUS) or if you are a developer and would like to contribute, you can fork the repository and clone your fork.

6. Download FOQUS

  - Get a tagged release  here https://github.com/CCSI-Toolset/FOQUS/releases,
  - Click the clone or download button here https://github.com/CCSI-Toolset/FOQUS to get the latest development version. or
  - Use the git client to clone your fork of FOQUS (if you want to contribute).

7. If you downloaded a zip file extract the FOQUS source to a convenient location.

Install FOQUS
-------------

8. Open the Anaconda prompt (or appropriate terminal or shell depending on operating system and choice of Python), and change to the directory containing the FOQUS files.
9. If you set up a "foqus" conda environment activate it

  - On Windows: ``conda activate foqus``
  - On Linux and OSX: ``source activate foqus``

10. Install requirements: ``pip install –r requirements.txt``
11. Install FOQUS.  The in-place install will allow you to easily edit source code while the regular install will install FOQUS in the central Python library location, and not allow editing of the source code.

  - Install in-place: ``python setup.py develop``
  - Regular install: ``python setup.py install``

Run FOQUS Installation
----------------------

12. Run foqus:

  - On Windows a batch file (foqus.bat) is created in the source directory.  This can be moved to any convenient location, and linked by a Windows shortcut if desired.  Start FOQUS by running the batch file.  The batch file should run FOQUS in the appropriate conda environment, if an Anaconda environment was used.  If you encounter any trouble with the batch file, an additional batch file (foqus_debug.bat) is provided which will keep the cmd windows open after FOQUS quits allowing you to see any error messages which may be generated.
  - On Linux or OSX launch foqus in a terminal.  Activate the appropriate conda environment if necessary. since the script is installed you can run if by typing ``foqus.py`` in a terminal in any directory.

13. The first time FOQUS is run, it will ask for a working directory location.  This is the location FOQUS will put any working files. This setting can be changed later. Files passed as command line arguments to FOQUS will be relative to where FOQUS is run. Once FOQUS starts, file paths will be relative to the FOQUS working directory.

Install Optional Software
-------------------------

There are several optional pieces of software which are not written in Python and not easily installed automatically. There are a couple packages which most users would want to install.  The first is PSUADE, which provides FOQUS UQ functionality. The second is TurbineLite which requires Windows, and is used to interface with Excel, Aspen, and gPROMS software.

Other software listed below will enable additional features of FOQUS if available.

Install PSUADE (current version: 1.7.12)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PSUADE (Problem Solving environment for Uncertainty Analysis and Design Exploration) is a software toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the PSUADE github site (https://github.com/LLNL/psuade). For Windows users, there is an installer at https://github.com/LLNL/psuade/releases for your convenience.

Install Turbine and SimSinter (Windows Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Install Microsoft SQL Server Compact 4.0 (https://www.microsoft.com/en-us/download/details.aspx?id=17876).
* Download and install the SimSinter (https://github.com/CCSI-Toolset/SimSinter/releases/) and TurbineLite (https://github.com/CCSI-Toolset/turb_sci_gate/releases/).
* Install SimSinter first, then TurbineLite.
* After the install the Turbine Web API Service Will start automatically when Windows starts, but it will not start directly after the install. Do one of these two things (only after install).
    * Restart computer, or
    * Start the "Turbine Web API service": (1) open Task Manager, (2) go to the "Services" tab, (3) click the "Services" button (in the lower right corner), (4) right-click "Turbine Web API Service" from the list, and (5) click "Start"

Install ALAMO
^^^^^^^^^^^^^

ALAMO (Automated Learning of Algebraic Models for Optimization) is a software toolkit that generates algebraic models of simulations, experiments, or other black-box systems. For more information, go to http://archimedes.cheme.cmu.edu/?q=alamo.

Download ALAMO and request a license from the ALAMO download page (https://minlp.com/alamo-downloads).

Install NLopt
^^^^^^^^^^^^^

NLopt is an optional optimization library, which can be used by FOQUS. Unfortunately, the Python module is not available to be installed with pip. For installation instructions, see https://nlopt.readthedocs.io/en/latest/, or NLopt can be installed with conda as follows: ``conda install -c conda-forge nlopt``

Install R
^^^^^^^^^

R is a software toolbox for statistical computing and graphics. R version 3.1+ are required for the ACOSSO and BSS-ANOVA surrogate models and the Basic Data's SolventFit model.

* Follow instructions from the R website (http://cran.r-project.org/) to download and install R.
* Open R and type the following to install and load the prerequisite packages:
   * ``install.packages('quadprog')``
   * ``library(quadprog)``
   * ``install.packages('abind')``
   * ``library(abind)``
   * ``install.packages('MCMCpack')``
   * ``library(MCMCpack)``
   * ``install.packages('MASS')``
   * ``library(MASS)``
   * ``q()``
* The last command exits R. When asked to save workspace image, type "y".
* Open FOQUS, go to the “Settings” tab, and set the “RScript Path” to the proper location of the R executable.

Optional FOQUS Settings
-----------------------

* Go to the FOQUS settings tab.
  - Set ALAMO and PSUADE locations.
  - Test TurbineLite config.

Automated tests
---------------

From top level of foqus repo type: ``python foqus.py -s test/system_test/ui_test_01.py`` or ``foqus.bat -s test/system_test/ui_test_01.py``

Building a Local Copy of Documentation
--------------------------------------

In the FOQUS source directory go to the docs directory and type ``make html``. This will build the docs which can be opened by opening build\\html\\index.html in a web browser.
