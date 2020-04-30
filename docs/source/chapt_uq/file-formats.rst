File Formats
============

Most UQ capabilities within FOQUS rely on PSUADE. As such, different UQ components require input files in PSUADE
formats. CSV (comma-separated values) files are also compatible. The specific requirements are explained in the
UQ section  :ref:`sec:_uq_tutorials` and section :ref:`sec:_ouu`.


PSUADE Full File Format
-----------------------

The following is an example of the full PSUADE file format. Comments in red do not appear in the file and are only for
instructional purposes.

PSUADE_IO (Note : inputs not true inputs if pdf  ̃=U)  :red: Start data block

5 2 6  :red: 5 inputs, 2 outputs, and 6 samples

1 1  :red: Sample index, run value (0 if sample point has not been calculated.)
  -9.5979899497487442e-01  :red: Value to the first input of sample 1

  1.0552763819095490e-01  :red: Value to the second input of sample 1

  2.1608040201005019e-01  :red: Value to the third input of sample 1

  -2.1608040201005019e-10  :red: Value to the fourth input of sample 1

  -2.5628140703517588e-01  :red: Value to the fifth input of sample 1

  -1.6979984061153328e+00  :red: Value to the first output of sample 1 (9.99e+34 if undefined)

  -7.8296928608517824e-01  :red: Value to the second output of sample 1 (9.99e+34 if undefined)

2 1  :red: Sample point 2. Run value is true (outputs calculated).
  -9.5477386934673336e-02

  8.5427135678391997e-02

  -9.7989949748743721e-01

  -4.8743718592964824e-01

  3.5175879396984966e-02

  9.7708275149071300e-01

  8.6655187317087226e-02

3 1  :red: Sample point 3. Run value is true (outputs calculated).
  -6.9849246231155782e-01

  -5.9798994974874375e-01

  -9.6984924623115576e-01

  2.5125628140703515e-02

  8.1909547738693478e-01

  -6.4229247835711212e-02

  2.8546752874255432e-01

4 1  :red: Sample point 4. Run value is true (outputs calculated).
  2.1608040201005019e-01

  7.2864321608040195e-01

  4.9748743718592969e-01

  5.6783919597989962e-01

  6.7839195979899491e-01

  -4.7115433927748318e-01

  -3.5869634004753126e-01

5 1  :red: Sample point 5. Run value is true (outputs calculated).
  5.6783919597989962e-01

  5.4773869346733672e-01

  -2.2613065326633164e-01

  3.8693467336683418e-01

  -1.7587939698492461e-01

  6.8926859881410230e-03

  -2.7551395275787588e-01

6 0  :red: Sample point 6. Run value is false (outputs not calculated).
  -7.2864321608040195e-01

  2.1608040201005019e-01

  8.3919597989949746e-01

  3.5175879396984966e-02

  2.3618090452261309e-01

  9.9999999999999997e+34  :red: Output not calculated.

  9.9999999999999997e+34  :red: Output not calculated.

PSUADE_IO  :red: End data block

PSUADE  :red: Start informational block

INPUT  :red: Start input information block

dimension = 5  :red: Number of inputs

variable 1 A0 = -1.00000e+00 1.00000e+00  :red: Input name & range

variable 2 A1 = -1.00000e+00 1.00000e+00

variable 3 A2 = -1.00000e+00 1.00000e+00

variable 4 A3 = -1.00000e+00 1.00000e+00

variable 5 A4  =  -1.00000e+00   1.00000e+00

END  :red: End input information block

OUTPUT  :red: Start output information block

dimension = 2  :red: Number of outputs

variable 1 Y1  :red: Output name

variable 2 Y2

END  :red: End output information block

METHOD  :red: Start sampling method information block

sampling = LH  :red: Latin Hypercube sampling

num_samples = 6  :red: Number of samples

END  :red: End sampling method block

APPLICATION  :red: Start application block

driver = NONE  :red: Name of driver program for calculating outputs (NONE for no driver)

END  :red: End application block

ANALYSIS  :red: Start analysis method information block

analyzer output_id = 1

analyzer rstype = MARS  :red: Default response surface type

diagnostics 1
END  :red: End analysis method information block
END  :red: End information block


This file format is accepted when:

- The user load an existing ensemble by clicking the **Load From File** button from the :ref:`fig:uq_screen`.
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Load all samples from a single file** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_loadsample`).
- The user performs optimization under uncertainty from the main :ref:`fig:ouu_screen` and selects the **Load Model From File** radio button for the user’s model; for this file, the user does not need to specify the first block (i.e., the PSUADE_IO block).

This file format is written when:

- The user saves an existing ensemble by clicking the **Save Selected** button from the :ref:`fig:uq_screen`.


PSUADE Sample File Format
-------------------------
The following is an example of the sample file format. Comments in red do NOT appear in the file and are only for
instructional purposes.

PSUADE_BEGIN  :red: Start data block

5 2  :red: 5 samples, 2 inputs

1 4.0 -1.0  :red: Sample index, input values for sample point 1

2 3.0 2.0  :red: Sample index, input values for sample point 2

3 5.0 1.0  :red: Sample index, input values for sample point 3

4 2.0 1.5  :red: Sample index, input values for sample point 4

5 3.0 3.0  :red: Sample index, input values for sample point 5

PSUADE_END  :red: End data block


This file format is accepted when:

- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Load all samples from a single file** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_loadsample`).
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Choose sampling scheme** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_dist`)); in the **Distributions** tab, if the user designates an input variable’s PDF to be of type “Sample”, the “Param 1” field will generate a **Select File** button that prompts for the sample file representing the input’s PDF.
- Similar to above, when the user enters Expert Mode within the Analysis dialog; within Expert Mode (:ref:`fig:uqt_rsaeua`), the user can change the input distribution before performing response surface based analysis.
• The user performs optimization under uncertainty from the main :ref:`fig:ouu_screen`; if any of the variables are designated as random variables, the **UQ Setup** tab will be displayed and any prompt for loading existing sample (e.g., “Load existing sample for Z3” or “Load existing sample for Z4”) will require this file format. (Currently, the **UQ Setup** tab is missing from the Figure because no variables have been designated as random).

This file format is written when:

- The user wants to save the results of inference by clicking **Save Posterior Input Samples to File** within Bayesian Inference (:ref:`fig:uq_inf`), which is accessible from the Analysis screen of UQ (:ref:`fig:uq_analysisW`).


Comma Separated Values (CSV) File Format
----------------------------------------
The following is an example of the CSV file format. Comments in red do not appear in the file and are only for
instructional purposes. CSV files can be easily generated using Excel and exporting in the .csv format.

A0,A1,A2,A3,A4,Y1,Y2  :red: Input variable names, then output variable names (if any)

-0.959,0.105,0.216,-2.16e-10,-0.256,-1.698,-0.783  :red: Values for the first sample (Output values are not required if
not calculated)

-0.095,0.085,-0.980,-0.487,0.035,0.978,0.087  :red: Values for the second sample

-0.698,-0.598,-0.970,0.025,0.819,-0.064,0.285

0.216,0.729,0.497,0.568,0.678,-0.471,-0.359

0.568,0.548,-0.226,0.387,-0.176,6.89e-03,-0.276


Variable names are specified in the first line, with input names and then output names. Output names can be specified,
even if there is no data available for them yet. Data is only required for inputs. In addition, the variable names line
is not required in those places where a PSUADE sample file is acceptable.

This file format is accepted when:

- The user loads an existing ensemble by clicking the **Load from File** button from the :ref:`fig:uq_screen`. Variable names are required.
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Load all samples from a single file** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_loadsample`).
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Choose sampling scheme** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_dist`); in the **Distributions** tab, if the user designates an input variable’s PDF to be of type “Sample”, the “Param 1” field will generate a **Select File** button that prompts for the sample file representing the input’s PDF.
- Similar to above, when the user enters Expert Mode within the Analysis dialog; within Expert Mode(:ref:`fig:uqt_rsaeua`), the user can change the input distribution before performing response surface based analysis.
- The user performs optimization under uncertainty from the main :ref:`fig:ouu_screen`; if any of the variables are designated as random variables, the **UQ Setup** tab will be displayed and any prompt for loading existing sample (e.g., “Load existing sample for Z3” or “Load existing sample for Z4”) will require this file format. (Currently, the **UQ Setup** tab is missing from the Figure because no variables have been designated as random).