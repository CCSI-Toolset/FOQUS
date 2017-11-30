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

If you do not have a git client install one. If you have Anaconda the easiest
way is 

``conda install git``

## Install Turbine Client

This step can be done automatically once the CCSI repositories are open by 
including Turbine Client as a requirment.

``pip install git+https://github.com/CCSI-toolset/turb_client@master``

## Install FOQUS

There are 2 ways to install FOQUS the first is preferred if you are a developer 
or want to modify FOQUS. The second way is probably easiest for other users.

1. Developers
  * Clone the FOQUS repository
  * ``python setup.py develop``
2. Other Users
  * ``pip install git+https://github.com/CCSI-toolset/foqus@master``
  
 
## Install FOQUS Bundle

(This will be renamed and the content modified before release)

Install the FOQUS Bundle installer for Windows from the CCSI website.  This will install 
TurbineLite, SimSinter, PSUADE, and an obsolete Windows application version of FOQUS. 
TurbineLite and SimSinter are Windows only programs which allow running simulations in Aspen,
gPROMS, and Excel. PSUADE supplies the UQ functionality of FOQUS.

On platforms other than Windows. PSUADE can be installed separately.

Additional components not currently include with FOQUS or the FOQUS bundle are
* DRM-Builder for building dynamic reduced models.
* iREVEAL building surrogate models for CFD with Kriging.
* Data management framework
* Turbine Hydro, used by the Turbine Gateway to move simulation files from
  the main Turbine database to TurbineLite instances on worker nodes.

## Optional, Install NLopt

NLopt is an optional optimization library, which can be used by FOQUS.  Unfortunately
the Python module is not available to be installed with pip. For installation 
instructions see https://nlopt.readthedocs.io/en/latest/. The Python module is required. 






