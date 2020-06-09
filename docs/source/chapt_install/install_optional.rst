.. _install_optional:

Install Optional Software
-------------------------

There are several optional pieces of software which are not written in Python and not easily
installed automatically. There are a couple packages which most users would want to install.  The
first is PSUADE, which provides FOQUS UQ functionality. The second is TurbineLite which requires
Windows and is used to interface with Excel, Aspen, and gPROMS software.

Other software listed below will enable additional features of FOQUS if available.

Install PSUADE (current version: 1.7.12)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PSUADE (Problem Solving environment for Uncertainty Analysis and Design Exploration) is a software
toolkit containing a rich set of tools for performing uncertainty analysis, global sensitivity
analysis, design optimization, model calibration, and more.

PSUADE install instructions are on the `PSUADE github site <https://github.com/LLNL/psuade>`_. For
Windows users, there is an installer at the `PSUADE releases page
<https://github.com/LLNL/psuade/releases>`_ for your convenience.

Install Turbine and SimSinter (Windows Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Install `Microsoft SQL Server Compact 4.0 <https://www.microsoft.com/en-us/download/details.aspx?id=17876>`_.

* Download and install the latest releases of `SimSinter
  <https://github.com/CCSI-Toolset/SimSinter/releases/>`_ and `TurbineLite
  <https://github.com/CCSI-Toolset/turb_sci_gate/releases/>`_.

* Install SimSinter first, then TurbineLite.

* After the install the Turbine Web API Service Will start automatically when Windows starts, but it
  will not start directly after the install. Do one of these two things (only after install):
  
  * Restart computer, or
  * Start the "Turbine Web API service":

    1. open Task Manager
    2. go to the "Services" tab
    3. click the "Services" button (in the lower right corner)
    4. right-click "Turbine Web API Service" from the list, and
    5. click "Start"


Install ALAMO
^^^^^^^^^^^^^

ALAMO (Automated Learning of Algebraic Models for Optimization) is a software toolkit that generates
algebraic models of simulations, experiments, or other black-box systems. For more information, go
to the `ALAMO Home Page <http://archimedes.cheme.cmu.edu/?q=alamo>`_.

Download ALAMO and request a license from the `ALAMO download page
<https://minlp.com/alamo-downloads>`_.


Install NLopt
^^^^^^^^^^^^^

NLopt is an optional optimization library, which can be used by FOQUS. Unfortunately, the Python
module is not available to be installed with pip. See the `NLopt Installation Instructions
<https://nlopt.readthedocs.io/en/latest/>`_ or NLopt can be installed with conda as follows::

    conda activate ccsi-foqus
    conda install -c conda-forge nlopt


Install SnobFit
^^^^^^^^^^^^^^^

SnobFit is an optional optimization library, which can be used by FOQUS for unconstrained
optimization. The python package can be installed with pip with::

    conda activate ccsi-foqus
    pip install SQSnobFit
    
The plugin has been developed for FOQUS versions 2.1 and greater. For further details on the
available versions and installation, see the `SQSnobFit PyPI package page
<https://pypi.org/project/SQSnobFit/>`_.

Once the python package is downloaded, navigate the path to "SQSnobFit" folder (likely
`$CONDA_PREFIX/lib/python3.7/site-packages/SQSnobFit/`) and modify the ``_snobfit.py`` file making
the following changes:

Comment out or remove the following code lines just below ``def minimize(...)`` function definition::

    if budget <= 0:
      budget = 100000
    
Then replace::

    return Result(fbest, xbest), objfunc.get_history()

with::

    return (request,xbest,fbest)

in the ``def minimize()`` function.


Install R
^^^^^^^^^

R is a software toolbox for statistical computing and graphics. R version 3.1+ is required for the
ACOSSO and BSS-ANOVA surrogate models and the Basic Data's SolventFit model.

* Follow instructions from the `R website <http://cran.r-project.org/>`_ to download and install R.
  
* Open R and type the following to install and load the prerequisite packages::

    install.packages('quadprog')
    library(quadprog)
    install.packages('abind')
    library(abind)
    install.packages('MCMCpack')
    library(MCMCpack)
    install.packages('MASS')
    library(MASS)
    q()

* The last command exits R. When asked to save workspace image, type "y".

* Open FOQUS, go to the “Settings” tab, and set the “RScript Path” to the proper location of the R
  executable.


Optional FOQUS Settings
-----------------------

Go to the FOQUS settings tab:

  - Set ALAMO and PSUADE locations.
  - Test TurbineLite config.
