These are install note that may be of some use for developers and testers.  We can either improve or delete these later.

## Windows

1. Download and install Anaconda (Python 2.7) 
      - https://www.anaconda.com/download/#windows
2. Download and install git client 
      - https://git-scm.com/downloads
3. Download ALAMO 
      - http://www.minlp.com/home
      - Request a license
      - Download Windows installer
      - Place license file in the same directory with alamo.exe
4. Create your own fork of the FOQUS repository 
      - https://github.com/CCSI-Toolset/foqus
      - fork button near upper right
5. Clone the FOQUS repository
      - Open "Anaconda Prompt" from Anaconda in start menu (assuming git is in path)
      - This command will create a foqus directory in th directory you run it in with a local foqus repo
      - ```git clone https://github.com/YOUR_USER_NAME/foqus foqus```
6. Getting updates
      - The command below pulls from master branch, but could pull from other branches too
      - ```git pull https://github.com/CCSI-Toolset/foqus master```
7. Create a virtual environment to keep FOQUS install septerate (optional)
      - There are a few minor issues with the env that may cause very slightly more effort.  If you only use Anaconda for fouqs this is most likely not work the trouble
      - ```conda create -n foqus python=2.7 anaconda```
      - ```conda activate foqus``` (need to do everytime you open the Anaconda console)
8. Install TurbineLite 
      * This requires Microsoft SQL Server Compact 4.0
          * https://www.microsoft.com/en-us/download/details.aspx?id=17876
          * I selected the 64-bit one and installed
      * https://www.acceleratecarboncapture.org/
      * Log in and go to products page
      * Select FOQUS Bundle
      * Download and install
      * **Unintall FOQUS and PSUADE that are installed (windows control pannel)**
      * Do one of these two things (only after install)
          * restart computer
          * or start the "Turbine Web API service"
9. Install PSUADE 
      - https://github.com/LLNL/psuade/releases
10. Install nlopt (optional)
      - ```conda install -c conda-forge nlopt```
11. Install FOQUS
      * Go to the directory where you cloned the FOQUS repository
      * ```python setup.py develop```
      * with the develp option foqus remains it its original location and code can be edited
      * to uninstall FOQUS for whatever reason 
            * ```pip unsintall foqus```
            * delete the cloned repo if you want to
            * could also delete the env if you made one 
                  * conda env remove foqus
12. Running FOQUS.
      * Go to Anaconda command prompt
      * ```conda activate foqus```
      * there is a problem with the env and python interperter so can't just run script or will use wrong env
            * This will get you correct version of python, but unfortunatley need to enter full path to script
                * ```python C:\Users\jeslick\AppData\Local\Continuum\anaconda2\envs\foqus\Scripts\foqus.py```
	          * Or going to where you your foqus repo is and running foqus.py there should be fine too
      * If you see Pandas warnings about not adding a column via new attribute, that is ok.  I'm not tryin to add a column there. May want to redesign to contain dataframe instead of inherit dataframe
13. FOQUS Settings
	- Go to the FOQUS settings tab
        - Set ALAMO and PSUADE locations
        - Test TurbineLite config
14. Automated tests (from top level of foqus repo)
	- ```python fouqs.py -s python foqus.py -s test/system_test/ui_test_01.py```
	- ...
