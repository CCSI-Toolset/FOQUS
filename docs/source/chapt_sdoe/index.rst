Sequential Design of Experiments (SDOE)
=======================================

A sequential design of experiments strategy allows for adaptive learning based on incoming results as the experiment is being run. The SDoE module in FOQUS allows the experimenter to flexibly incorporate this strategy into their designed experimental planning to allow for maximal relevant information to be collected. Statistical design of experiments is an important strategy to improve the amount of information that can be gleaned from the overall experiment. It leverages principles of putting experimental runs where they are of maximum value, the interdependence of the runs to estimate model parameters, and robustness to the variability of results that can be obtained when the same experimental conditions are repeated. There are two major categories of designed experiments: those for which a physical experiment is being run, and designs for a computer experiment where the output from a theoretical model is explored. While the methods available were initially focused on experiments for physical experiments, opportunities also exist for accelerated learning through strategic selection and updating of experimental runs for computer experiments. 

The overall process for Sequential Design of Experiments (SDoE) is detailed below:

#.	Identify one or more criteria over which to optimize. Common choices are (a) refining the region of interest, (b) improving the precision (or reducing the uncertainty) in the estimation of model parameters, (c) improving the precision of prediction for new observations in the design region, (d) quantifying the discrepancy between the model and data, or (e) optimizing the value of responses of interest. If more than one criterion is going to be used, then identify how they will be combined into a utility function.

#.	Develop a working model of the process that can be used to calculate the criteria values based on currently available knowledge and data.

#.	Define the inputs that will be manipulated during the experiment, and the ranges of interest for these factors. 

#.	Identify candidate input factor locations that are being considered for new experiments. This can be a grid of input combinations or continuous regions in the design space. If there are combinations of the factors that will not yield results or that are not of interest, these regions of the design space should be excluded from consideration.

#.	Develop a working model of the process that is able to receive new data and incorporate them to update the calculated criteria values.

#.	Develop a plan for the size of the sequential design batches, based on the time required to set-up and run the experiments as well as the computational time required to process new data and update the working model. 

#.	Identify the initial batch of experiments to be run at the beginning of the experiments based on the model developed in step 2. This involves examining the utility of new data at each candidate location, and comparing which locations have the highest anticipated utility.

#.	Run the first batch of experimental runs, update the model developed in step 5 with the new results, and generate the next batch of experimental runs.

#.	For the duration of the experiment, repeat steps 7 and 8 for subsequent batches based on the updated model after incorporating the newly obtained data.

The first version of the SDoE module allows some functionality that can produce flexible space-filling designs to be created.
Later versions will allow for additinoal design criteria to be utilized, but the first version already had considerable flexibility to construct helpful design based on several different strategies. Key features of the approach that we use in this module are: a) designs will be constructed by selecting from a user-provided candidate set of input combinations, and b) historical data, which has already been collected can be integrated into the design construction to ensure that new data are collected with a view to disperse from where data are already available.

We begin with some basic terminology that will help provide structure to the process described in the remainder of the section.

*	Input factors – these are the controllable experimental settings that are manipulated during the experiment. It is important to carefully define the ranges of interest for the inputs (eg. Temperature in [200°C,400°C]) as well as any logistical or operational constraints on these input factors (eg. Flue Gas Rate < 1000 kg/hr when Temperature > 350°C)

*	Input combinations (or design runs) – these are the choices of settings for each of the input factors for a particular run of the experiment. It is assumed that the implementers of the experiment are able to set the input factors to the desired operating conditions to match the prescribed choice of settings.

* Input space (or design space) – the region of interest for the input factors in which the experiment will be run. This is typically constructed by combining the individual input factor ranges, and then adapting the region to take into account any constraints. Any suggested runs of the experiment will be located in this region.

*	Responses (or outputs) – these are the measured results obtained from each experimental run. These are most desirably quantitative summaries of a characteristic of interest from running the process at the prescribed set of operating conditions (eg. CO2 capture efficiency is a typical response of interest for CCSI).

*	Design criterion / Utility function – this is a mathematical expression of the goal (or goals) of the experiment that is used to guide the selection of new input combinations, based on the prior information before the start of the experiment and during the running of the experiment. The design criterion can be based on a single goal or multiple competing goals, and can be either static throughout the experiment or evolving as different goals change in importance over the course of the experiment. Common choices of goals for the experiment are:

#.	exploring the region of interest, 

#. improving the precision (or reducing the uncertainty) in the estimation of model parameters, 

#.	improving the precision of prediction for new observations in the design region, 

#. quantifying the discrepancy between the model and data, or 

#.	optimizing the value of responses of interest. 

An optimal design of experiment strategy uses the utility function to evaluate potential choices of input combinations to maximize the improvement in the utility function over the available candidates. If the optimal design strategy is sequential, then the goal is to use early results from the beginning of the experiment to guide the choice of new input combinations based on what has been learned about the responses.

Using SDoE Module - The Basics
------------------------------

In this section, we descibe the basic steps in for creating a design in this module. When you first click on the  **SDOE** button from the main FOQUS homepage, a first window appears. To create a design, the progression of steps takes you through the **Ensemble Selection** box (top left), then a transition triggered by the **Confirm** button to the **Ensemble Aggregation** box, and finally there are optional changes that can be made in the box at the bottom of the window. The final step in this wondow is to click on **Create Design**. 

.. figure:: figs/1_home.png
   :alt: Home Screen
   
   SDOE Home Screen
   
   [fig:sdoe_home]
   
We now consider some details for each of these steps:

1. In the **Ensemble Selection** box, click on the **Load from File..** button to select the file(s) for the construction of the design. Several files can be selected and added to the box listing the chosen files.

2. For each of the files selected using the pull-down menu, identify them as either a **Candidate** file or a **History** file. **Candidate** .csv files are comprised of possible input combinations from which the design can be constructed. The columns of the file should contain the different input factors that define the dimension of the input space. The rows of the file each identify one set of input values that could be selected as a run in the final design. Typically, a good candidate file will have many different candidate runs listed, and they should fill the available ranges of the inputs that could be considered. Leaving gaps or holes in the input space is possible, but generally should correspond to a region where it is not possible (or desirable) to collect data.
**History** .csv files should have the same number of columns for the input space as the candidate file, and represent data that have already been collected. The algorithm for creating the design will aim to place points in different locations from where data have already been obtained, while filling the input space around those locations.

3. Click on the **View** button to open the **Preview Inputs** pop-up widow, to see the list of columns contained in each file. The left hand side displays the first set of values from the file. Select the columns that you wish to see graphically in the right hand box , and then click on **Plot SDOE** to see a scatterplot matrix of the data. 

.. figure:: figs/2_preview_inputs.png
   :alt: SDOE preview of inputs
   
   SDOE preview of inputs
   
   [fig:2_preview_inputs]

Select the columns that you wish to see graphically in the right hand box , and then click on **Plot SDOE** to see a scatterplot matrix of the data. 

.. figure:: figs/3_scatterplot_inputs.png
   :alt: SDOE plot of inputs
   SDOE plot of inputs
   
   [fig:3_scatterplot_inputs]
   
The plot shows histograms of each of the inputs on the diagonals to provide a view of the distribution of values as well as the range of each input. The off-diagonals show pairwise scatterplots of each pair of inputs. This should provide the experimenter with the ability to assess if the ranges specified and any constraints for the inputs have been appropriately captured with the specified candidate set. In addition, repeating this process for any historical data will provide verification that the already observed data have been suitably characterized.

4. Once the data have been verified for both the **Candidate** and **History** files, click on the **Confirm** button to make the **Ensemble Aggregation** window active.

5. If more than one **Candidate** file was specified, then the **aggregate_candidates.csv** file that was created will have combined these files into a single file. Similarly if more than one **Histoy** file was specified, then the **aggregate_history.csv** file has been created with all runs from these files. If only a single file was selected for either the  **Candidate** and **History** files, then their aggregated matching files will be the same as the original.

There are options to view the aggregated files for both the candidate and history files, with a similar interface as was shown in step 3. In addition, a single plot of the combined candidate and history files can be viewed, by (ADD DETAILS WHEN AVAILABLE). In this plot the (BLACK) points represent the candidate locations, while the (RED) points represent already collected data from the history file.

.. figure:: figs/4_scatterplot_aggregated.png
   :alt: SDOE plot of aggregated inputs
   SDOE plot of aggregated inputs
   
   [fig:4_scatterplot_aggregated]
   
6. Once the data have been verified as the desired set to be used for the design construction, then click on the **Create Design** button at the bottom right corner of the **Ensemble Aggregation** window. This opens the second SDOE window, which allows for specific design choices to be made.

.. figure:: figs/5_SDOE_page2.png
   :alt: SDOE second window
   SDOE second window
   
   [fig:5_SDOE_page2]

7. The first choice to be made for the design is whether to optimize using **minimax** or **maximin**. The first choice, **minimax** looks to choose design points that minimize the maximum distance that any point in the input space (as characterized by the candidate set and historical data, if it is available) is away from a design point. Hence, the idea here is that if we want to use data to help predict new outcomes throughout the inputt space, then we don't want to be too far away from an observed location. The second choice, **maximin** looks to choose a design where the design points are as far away from each other as possible. In this case, the design criterion is looking to maximize how close any two points are away from their nearest neighbor. In practice the two design criterion often give similar designs, with the maximin criterion tending to push the chosen design points closer to the edges of the specified regions. 

Hint: If there is uncertainty about some of the edge points in the candidate set being viable options, then **minimax** might be preferred. If the goal is to place points throughoht the input space with them going right to the edges, than **maximin** might be preferred. Note, that creating the designs is relatively easy, so it may be helpful to try both approaches to see which is preferred.

8. The next choice to be made falls under **Design Specification**, when the experimenter can select the sizes of designs to be created. The **Min Design Size** specifies the smallest design size to be created. Not that the default value is set at **2**, which would lead to choosing the best two design runs from the candidate set to fill the space (after taking into account any historical data that has already been gathered).
The **Max Design Size** specifies the largest design size to be created. The default value is set at **8**, which means that if this combination were used, designs would be created of size 2, 3, 4, 5, 6, 7 and 8. Hence, it may be prudent to select a relatively small range of values to expedite the creation of the designs, as each of these choices triggers a separate optimization search.

9. Next, there are options for the columns of the candidate set to be used for the construction of the design. Under **Include?** in the box on the right hand side, the experimenter has the option of whether particular columns should be included in the space-filling design search. Unclick a box, if a particular column should not be included in the search.

Next select the **Type** for each column. Typically most of the columns will be designated as **Inputs**, which means that they will be used to find the best design. In addition, we recommend including one **Index** column which contains a unique identifier for each run of the candidate set. This makes tracking which runs are included in the constructed designs. If no **Index** column is specified, a warning will appear later in the process, but it is not strictly required.

Finally, the **Min** and **Max** columns in the box allow the range of values for each input column to be changed. The default is to extract the smallest and largest values from the candidate and history data files, and use these. This approach generally works well, as it scales the inputs to be in a uniform hypercube for comparing distances between the design points. 

Hint: the default values for **Min** and **Max** can generally be left at their defaults unless: (1) the range of some inputs represent very different amounts of change in the process. For example, if temperature is held nearly constant, while a flow rate changes substantially, then it may be desirable to extend the range of the temperature beyond its nominal values to make the amount of change in temperature more commensurate with the amount of change in the flow rate. (2) if changes are made in the candidate or history data files. For example, if one set of designs are created from one candidate set, and then another set of designs are created from a different candidate set.



Example 1: 8-run 2-D design
---------------------------

For this first example, the goal is to construct a simple space-filling design with 8 runs in a 2-dimensional space using the example files provided with FOQUS. 

1. From the FOQUS main screen, click the **SDOE** button. On the top left side, select **Load from File**, and select the candidate.csv file from examples folder. This identifies the possible input combinations from which the design will be constructed. The more possible candidates that can be provided to the search algorithm used to construct the design, the better the design might be for the specified criterion. `[fig:sdoe_home] <#fig:sdoe_home>`__.

.. figure:: figs/1_home.png
   :alt: Home Screen
   
   Home Screen
   
   [fig:sdoe_home]
   
   
