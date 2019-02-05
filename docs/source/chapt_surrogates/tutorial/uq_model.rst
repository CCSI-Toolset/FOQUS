.. _tutorial.surrogate.uq:

Surrogates with UQ Tools
========================

For the purpose of this tutorial, we will use ACOSSO to demonstrate the
use of a surrogate within the UQ module. The steps are the same
regardless of the surrogate tool chosen.

To perform the UQ analysis, Python is required for use the “User
Regression” response surface that will be used. Before starting this
tutorial, you will need to install Python 2.7.x (not Python 3). (See
https://www.python.org/downloads/). In addition, if \*.py files have
been re-associated with other executables (e.g. editors), please change
the association back to python.exe.

#. Load a fresh session by clicking the Session button from the Home
   window. Select Open Session and then navigate to the “examples/UQ”
   directory. Select “Rosenbrock_no_vectors.foqus.” This will load a
   session with a simple flowsheet containing a single node.

#. Click Settings and ensure that (1) FOQUS Flowsheet Run Method is set
   to “Local”, and that (2) proper paths are set for PSUADE and RScript.

#. Train an ACOSSO surrogate of this node by clicking the **Surrogates**
   button from the Home window.

   #. Click Add Samples and select “Use Flowsheet”. This will display
      the Simulation Ensemble Setup dialog.

   #. Within this dialog, ensure all variables are set to “Variable”
      type in the Distributions tab. In the Sampling scheme tab, select
      “Monte Carlo” as your sampling scheme, set the number of samples
      to 100, and then click Generate Samples to generate the set of
      input values. Click Done to return to the Surrogates screen.

   #. Once sample generation completes, click the Uncertainty button
      from the Home window.

   #. Click the Launch button to generate the samples.

   #. Click the Surrogates button from the Home window. The Data tab of
      the Surrogates screen should now displays a Flowsheet Results
      table that is populated with the values of the new input samples.

   #. From the Variables tab, select all of the checkboxes. (There
      should be six checkboxes for input variables and one checkbox for
      output variable.) Here, you are defining the inputs and outputs
      for your surrogate function.

   #. From the Method Settings tab, note the name of the file next to
      “FOQUS Model (for UQ)”. This will be the name of the UQ driver
      file that contains the Python code that implements the surrogate
      function.

   #. On top of this screen, select “ACOSSO” as your surrogate tool from
      the Tool drop-down list and then click on the green arrow to start
      training the surrogate.

   #. Once complete, a popup window will display, reminding you of the
      location of the drive file. Note the location as you will need
      this information later inside the UQ module.

#. Perform a response-surface-based uncertainty analysis by clicking the
   **Uncertainty** button from the Home window.

   #. In the Uncertainty Quantification Simulation Ensembles table. A
      row corresponding to the ensemble that was just generated for
      surrogate training should be displayed. This same ensemble can be
      used or a new one can be created to be used as the test data set
      for analysis. In the row corresponding to the ensemble to be
      analyzed, click the Analyze button to proceed. This action will
      bring up an analysis dialog.

   #. Within this analysis dialog, navigate to “Analysis” section. For
      Step 1, select “Response Surface”. For Step 3, select “User
      Regression” in the first drop-down list. Lastly, for “User
      Regression File”, browse to the same location as the UQ driver
      file that was generated within the Surrogates module. (This is the
      same location that was previously noted from the popup message.)
      At this point, your surrogate function is now set up as a
      user-defined response surface and all response-surface-based UQ
      analyses are accessible.

   #. Click Validate (Step 4) to perform response surface validation.
      Once complete, a figure with cross-validation results will be
      displayed: a histogram of errors to the left and a plot of
      predicted values versus actual values to the right. For more
      information, refer to the UQ Tutorial in
      Section\ `[tutorial.uq.rs] <#tutorial.uq.rs>`__\ .

   #. Once a “Response Surface” has been validated, other UQ analysis
      options are available. Choose “Uncertainty Analysis” in Step 5 and
      click Analyze to perform uncertainty analysis using your ACOSSO
      surrogate.

During validation, if the error, “RSAnalyzer: RSTest_hs.m does not
exist.” displays, this is likely caused by incompatibility with the
surrogate and the test data. An example scenario might be your test data
has six inputs, but your surrogate assumes five inputs. This is easily
fixed by returning to the Surrogates screen, clicking on the
**Variables** tab, and making sure the appropriate selections are made
(i.e., check off six inputs instead of just five).
