.. _file-formats:

File Formats
============

Most UQ capabilities within FOQUS rely on PSUADE. As such, different UQ components require input files in PSUADE
formats. CSV (comma-separated values) files are also compatible. The specific requirements are explained in the
UQ section  :ref:`uq-tutorials` and section :ref:`ouu`.

PSUADE Full File Format
-----------------------

The following is an example of the full PSUADE file format. Comments in red do not appear in the file and are only for
instructional purposes.

:ref:`full-format`

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

:ref:`sample-format`

This file format is accepted when:

- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Load all samples from a single file** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_loadsample`).
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Choose sampling scheme** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_dist`); in the **Distributions** tab, if the user designates an input variable’s PDF to be of type “Sample”, the “Param 1” field will generate a **Select File** button that prompts for the sample file representing the input’s PDF.
- Similar to above, when the user enters Expert Mode within the Analysis dialog; within Expert Mode (:ref:`fig:uqt_rsaeua`), the user can change the input distribution before performing response surface based analysis.
- The user performs optimization under uncertainty from the main :ref:`fig:ouu_screen`; if any of the variables are designated as random variables, the **UQ Setup** tab will be displayed and any prompt for loading existing sample (e.g., “Load existing sample for Z3” or “Load existing sample for Z4”) will require this file format. (Currently, the **UQ Setup** tab is missing from the Figure because no variables have been designated as random).

This file format is written when:

- The user wants to save the results of inference by clicking **Save Posterior Input Samples to File** within Bayesian Inference (:ref:`fig:uq_inf`), which is accessible from the Analysis screen of UQ (:ref:`fig:uq_analysisW`).


Comma Separated Values (CSV) File Format
----------------------------------------
The following is an example of the CSV file format. Comments in red do not appear in the file and are only for
instructional purposes. CSV files can be easily generated using Excel and exporting in the .csv format.

:ref:`csv-format`

Variable names are specified in the first line, with input names and then output names. Output names can be specified,
even if there is no data available for them yet. Data is only required for inputs. In addition, the variable names line
is not required in those places where a PSUADE sample file is acceptable.

This file format is accepted when:

- The user loads an existing ensemble by clicking the **Load from File** button from the :ref:`fig:uq_screen`. Variable names are required.
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Load all samples from a single file** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_loadsample`).
- The user creates a new ensemble by clicking the **Add New** button from the :ref:`fig:uq_screen` and selecting the **Choose sampling scheme** radio button in the user’s selection of sample generation (:ref:`fig:uq_sim_dist`); in the **Distributions** tab, if the user designates an input variable’s PDF to be of type “Sample”, the “Param 1” field will generate a **Select File** button that prompts for the sample file representing the input’s PDF.
- Similar to above, when the user enters Expert Mode within the Analysis dialog; within Expert Mode(:ref:`fig:uqt_rsaeua`), the user can change the input distribution before performing response surface based analysis.
- The user performs optimization under uncertainty from the main :ref:`fig:ouu_screen`; if any of the variables are designated as random variables, the **UQ Setup** tab will be displayed and any prompt for loading existing sample (e.g., “Load existing sample for Z3” or “Load existing sample for Z4”) will require this file format. (Currently, the **UQ Setup** tab is missing from the Figure because no variables have been designated as random).