# Smoke Tests for Automated Testing of FOQUS

Tests include: Flowsheet, Optimization, Optimization Under Uncertainty, and Uncertainty Quantification

## Using The Tests
* Navigate to the main directory containing the ``foqus.py`` file
* Launch FOQUS with the ``-s`` option: ``python foqus.py -s "examples\Smoke Tests\generic_smoke_test.py"``

## Viewing Results
* These smoke tests are designed to report errors
	* Successful runs will not generate error log files
* Error logs are located in the FOQUS working directory labeled AutoErrLog_testName.txt
	* Log files include the full error message including headings and supplementary content