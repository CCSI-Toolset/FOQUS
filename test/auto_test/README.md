# Bash Scripts for Automated Testing of FOQUS

Tests include: Flowsheet, Optimization, Optimization Under Uncertainty, and Uncertainty Quantification

## Using The Scripts
The scripts are designed to be run in series on a testing machine, but can be run locally if desired. Windows requires a bash shell to run these scripts which can be provided by the Git client.
The order for using the scripts is listed here:
* Create
* Activate
* Setup
* Test Scripts
* Deactivate
* Destroy

## Viewing Results
* The smoke tests are designed to report errors
	* Successful runs will not generate error log files
* Error logs are located in the FOQUS working directory labeled AutoErrLog_testName.txt
	* Log files include the full error message including headings and supplementary content