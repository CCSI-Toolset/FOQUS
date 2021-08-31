Example 1: ODoE with Existing Candidate Set
--------------------------------------------

In this example, the user will provide an existing candidate set.

#. Start FOQUS and click the ‘SDoE’ icon.

   .. figure:: figs/1_SDoE_main.png
      :alt: SDoE Main Window
      :name: fig.SDoE_main

      SDoE Main Window


#. Select the radio button **Robust omptimality-based DoE (ODoE)**

   .. figure:: figs/2_ODoE_main.png
      :alt: ODoE Main Window
      :name: fig.ODoE_main

      ODoE Main Window

#. Click the **Browse** button to **Load RS Train Data**, browse and load the ODoE_example.csv
   from the examples folder.

   First you will be prompted to specify the number of inputs in your
   training data.

   .. figure:: figs/3a_ODoE_numInputs.png
      :alt: ODoE Specify Number of Inputs
      :name: fig.ODoE_numInputs

      ODoE Specify Number of Inputs

   After clicking **OK** the file loads and the screen will look like this:

   .. figure:: figs/3b_ODoE_LoadRSTrainData.png
      :alt: ODoE Load RS Train Data
      :name: fig.ODoE_loadRSTrainData

      ODoE Load RS Train Data

#. Under **Input Setup** we need to select the type for each input. Leave **X1** and **X2** as **Variable**
   inputs and change **X3** and **X4** to be **Design** inputs.

   .. figure:: figs/4_ODoE_inputSetup.png
      :alt: ODoE Input Setup
      :name: fig.ODoE_inputSetup

      ODoE Input Setup

#. Click **Confirm Inputs** and the **Simulation Ensemble Setup** window will pop up to generate
   our **Prior Sample**.

   .. figure:: figs/5_ODoE_PriorGeneration1.png
      :alt: ODoE Simulation Ensemble Setup for Prior Sample Generation
      :name: fig.ODoE_priorGen1

      ODoE Simulation Ensemble Setup for Prior Sample Generation

#. Switch to the **Sampling Scheme** tab and select **Monte Carlo** and leave the **# of Samples**
   at **1000**. Click **Generate Samples**. When the samples are generated, **Done!** will show up
   right next to the button. You can visualize the samples clicking on the **Preview Samples** button.
   Once the user is done, click the **Done** button so the generated samples get saved.

   .. figure:: figs/6_ODoE_PriorGeneration2.png
      :alt: ODoE Simulation Ensemble Setup for Prior Sample Generation - Sample Scheme
      :name: fig.ODoE_priorGen2

      ODoE Simulation Ensemble Setup for Prior Sample Generation - Sample Scheme

#. Under **Design Setup** click on the **Load Existing Candidate Set** button.

   .. figure:: figs/7a_ODoE_LoadCand1.png
      :alt: ODoE Load Existing Candidate Set
      :name: fig.ODoE_loadCand1

      ODoE Load Existing Candidate Set

   Browse and load the CandidateSet.csv from the examples folder. The user can select the candidate
   and click on the **Delete Selection** button in case they want to delete the candidate set. To
   visualize the data, just click the **View** button under the **Visualize** column.

   .. figure:: figs/8a_ODoE_LoadCand2.png
      :alt: ODoE Load Existing Candidate Set
      :name: fig.ODoE_loadCand2

      ODoE Load Existing Candidate Set

#. On the right hand side of the **Design Setup** section, click on the **Load Evaluation Set**
   button.

   .. figure:: figs/9a-1_ODoE_LoadEval.png
      :alt: ODoE Load Evaluation Set
      :name: fig.ODoE_loadEval

      ODoE Load Evaluation Set

   Browse and load the EvaluationSet.csv file from the examples folder. Similar to the candidate set
   section, the user can select the evaluation set and click on the **Delete Selection** button in
   case they want to delete the evaulation set. To visualize the data, just click the **View**
   button under the **Visualize** column.

   .. figure:: figs/9a-2_ODoE_Cand&EvalSets.png
      :alt: ODoE Candidate and Evaluation Sets
      :name: fig.ODoE_candEValSet

      ODoE Candidate and Evaluation Sets

#. Click on the **Confirm Design Setup** button and under the **Output Setup** section, select
   **MARS** in the **Response Surface** dropdown menu.

   .. figure:: figs/10_ODoE_outputSetup.png
      :alt: ODoE Output Setup - MARS
      :name: fig.ODoE_outputSetup

      ODoE Output Setup - MARS

#. Click **Validate RS** button and the user will get a informative message window and the response
   surface validation plot.

   .. figure:: figs/11_ODoE_RSValidation_message.png
      :alt: ODoE Response Surface Validation Message
      :name: fig.ODoE_RSValMessage

      ODoE Response Surface Validation Message

   .. figure:: figs/12a_ODoE_RSValidation_plot.png
      :alt: ODoE Response Surface Validation Plot
      :name: fig.ODoE_RSValPlot

      ODoE Response Surface Validation Plot

   If the RS selected looks good, you can click the **Confirm RS** button. The response surface
   predictions on candidates will get populated in the table on the bottom right corner under
   **RS Predictions on Candidates**. The user can edit the **mean** and **standard deviation**
   columns in this table as needed.

   .. figure:: figs/13_ODoE_RSConfirmed.png
      :alt: ODoE Response Surface Confirmed and Predictions Generated
      :name: fig.ODoE_RSConfirmed

      ODoE Response Surface Confirmed and Predictions Generated

#. Under ODoE Setup select the **Optimality Criterion** (in this case G-Opt), **Design Size**
   (in this case 2) and **Number of Restarts** (in this case 3). Once those three parameters are
   decided, click the **Run ODoE** button. A window with PSUADE running will show up.

   .. figure:: figs/14_ODoE_PSUADErunning.png
      :alt: ODoE PSUADE Running Window
      :name: fig.ODoE_PSUADE

      ODoE PSUADE Running Window

#. Once PSUADE finishes generating the optimality-based design, another window will pop up with
   results information. A more thorough summary will also be saved in the **ODOE_files** directory
   as **odoe_results.txt**.

   .. figure:: figs/15_ODoE_resultsWindow.png
      :alt: ODoE Results Window
      :name: fig.ODoE_resultsWindow

      ODoE Results Window

   .. figure:: figs/16_ODoE_ResultsFile.png
      :alt: ODoE Results File
      :name: fig.ODoE_resultsFile

      ODoE Results File
