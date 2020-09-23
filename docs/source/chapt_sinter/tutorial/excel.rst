.. _sec.tut.simsinter.excel:

Tutorial 3: Microsoft Excel Configuration
=========================================

The files (both the Excel and the JSON files) for this tutorial are
located in: **examples/tutorial_files/SimSinter/Tutorial_3**

.. note:: |examples_reminder_text|

#. The “SinterConfigGUI” can be launched from FOQUS, via the
   **Create/Edit** button found in **File**\ :math:`\rightarrow`
   **Add/Update Model to Turbine** or “SinterConfigGUI” may be run on
   its own by selecting **CCSI Tools** :math:`\rightarrow` **FOQUS**
   :math:`\rightarrow` **SinterConfigGUI** from the Start menu.

#. The splash window displays, as shown in Figure
   :ref:`fig.sinter.acm.splash`. The user may
   click the splash screen to proceed, or wait 10 seconds for it to
   close automatically.

   .. figure:: ../figs/ap/01_Splash_Screen.png
      :alt: SinterConfigGUI Splash Screen
      :name: fig.sinter.excel.splash

      SinterConfigGUI Splash Screen

#. The SinterConfigGUI Open Simulation window displays (Figure
   :ref:`fig.sinter.acm.openpage`). If
   “SinterConfigGUI” was opened from FOQUS, the filename text box
   already contains the correct file. To proceed immediately click
   **Open File and Configure Variables** or click **Browse** to search
   for the file. For this tutorial, a fresh copy of the BMI (body
   mass index) test is opened (exceltest.xlsm). It is located in:

   examples/tutorial_files/SimSinter/Tutorial_3

   .. figure:: ../figs/ap/02_FileOpenScreen.png
      :alt: SinterConfigGUI Open Simulation Screen
      :name: fig.sinter.excel.openpage

      SinterConfigGUI Open Simulation Screen

#. Microsoft Excel starts in the background. This is so the user can
   observe things about the worksheet while working on the configuration
   file.

#. In the “SinterConfigGUI” the SinterConfigGUI Simulation Meta-Data
   page is now displayed (Figure :ref:`fig.sinter.excel.savename`). The
   first and most important piece of metadata is **Save Location** at
   the top of the window. This is where the sinter configuration file is
   saved. The system attempts to locate a reasonable file location and
   file name; however, the user must confirm the correct file location,
   since it automatically overwrites whatever filename currently exists.

   .. figure:: ../figs/Excel/04_MetaDataSave.png
      :alt: SinterConfigGUI Simulation Meta-Data Save Text Box
      :name: fig.sinter.excel.savename

      SinterConfigGUI Simulation Meta-Data Save Text Box

#. Continue to complete in the remaining fields and click **Next**.

#. In the SinterConfigGUI Variable Configuration Page, (Figure
   :ref:`fig.sinter.excel.variableempty`)
   notice that the Excel setting variable **macro** is already included
   in the **Selected Input Variables.** If the Excel spreadsheet has a
   macro that should be run after SimSinter sets the inputs, but before
   SimSinter gets the outputs, enter the macros name in the **Default**
   text box. If the Default box is left blank, no macro is run (unless a
   name is supplied in the input variables when running the simulation).
   If the user needs to run multiple macros (e.g., Macro1 and Macro2),
   we recommend that the user create a "Master" macro in the Excel file
   that automatically runs Macro1 and Macro2 using the Call statement.
   Let's suppose that the "Master" macro is named MasterMacro.
   Then, in SimSinter, the user will need to type in MasterMacro in
   the **Default** text box under the Excel setting variable **macro**.

   .. figure:: ../figs/Excel/06_VariablesEmpty.png
      :alt: SinterConfigGUI Variable Configuration Page before Input
      :name: fig.sinter.excel.variableempty

      SinterConfigGUI Variable Configuration Page before Input

#. The Excel simulation has the same **Variable Tree** structure as
   Aspen Plus, as shown in (Figure
   :ref:`fig.sinter.excel.variableselected`).
   Only the variables in the active section of the Excel spreadsheet
   appear in the **Variable Tree**. If, for some reason, a cell does not
   appear the in tree, the user may manually enter the cell into the
   **Selected Path** text box. In this case, select the “height$C$4”
   variable.

   Note: Row is first in the **Variable Tree**, yet column is first in
   the **Path**.

   .. figure:: ../figs/Excel/07_VariablesSelected.png
      :name: fig.sinter.excel.variableselected

      SinterConfigGUI Variable Configuration Page Selecting a Variable
      from the Excel Variable Tree

#. If the user double-clicks, presses enter, clicks **Preview**, or
   clicks **Lookup**, the variable will be displayed in the **Preview
   Variable** frame. Click the **Make Input** button to make the
   variable an input variable. Now the variable is in the **Selected
   Input Variables** section, and its meta-data may be edited (Figure
   :ref:`fig.sinter.excel.variableinputs`).

   .. figure:: ../figs/Excel/08_VariablesInput.png
      :name: fig.sinter.excel.variableinputs

      SinterConfigGUI Variable Configuration Page Description “Joe’s
      Height”

#. Enter an output variable (such as, “BMI$C$3”), by selecting the
   variables in the **Variable Tree**, clicking **Preview**, and then
   clicking **Make Output** (Figure :ref:`fig.sinter.excel.variableoutput`).

   .. figure:: ../figs/Excel/09_VariablesOutput.png
      :name: fig.sinter.excel.variableoutput

      SinterConfigGUI Variable Configuration Page Selecting Excel Output
      Variables

#. The simulation is now set up. To save the configuration file, click
   **Finish** or press CTRL+S. The file is saved to the location that
   was set on the SinterConfigGUI Simulation Meta-Data window. A user
   can save a copy under a different name, by navigating back to the
   SinterConfigGUI Simulation Meta-Data window using **Back**, and then
   changing the name. This creates a second version of the file.
