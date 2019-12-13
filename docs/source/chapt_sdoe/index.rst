Sequential Design of Experiments (SDOE)
=======================================

A sequential design of experiments strategy allows for adaptive learning based on incoming results as the experiment is being run. The SDoE module in FOQUS allows the experimenter to flexibly incorporate this strategy into their designed experimental planning to allow for maximal relevant information to be collected. Statistical design of experiments is an important strategy to improve the amount of information that can be gleaned from the overall experiment. It leverages principles of putting experimental runs where they are of maximum value, the interdependence of the runs to estimate model parameters, and robustness to the variability of results that can be obtained when the same experimental conditions are repeated. There are two major categories of designed experiments: those for which a physical experiment is being run, and designs for a computer experiment where the output from a theoretical model is explored. While the methods available primarily focus on experiments for physical experiments, opportunities also exist for accelerated learning through strategic selection and updating of experimental runs for computer experiments using the same tools. 

The current version of the SDoE module has functionality that can produce flexible space-filling designs. Currently, two types of space-filling designs are supported:
 
Uniform Space Filling  (USF) Designs space design points evenly, or uniformly, throughout the user-specified input space. These designs are common in physical and computer experiments where the goal is to have data collected throughout the region, and when predicting new results at a new location, some data will be available close by. To use the Uniform Space Filling design capability in the SDoE module, the only requirement for the user is that the candidate set of possible input combinations contains a column for all of the inputs for each row in the file. It is also recommended (but not required) to have an index column to be able to track which rows of the candidate set were selected.

Non-Uniform Space Filling (NUSF) Designs maintain the goal of having design points spread throughout the desired input space, but add a feature of being able to emphasize some regions more than others. This adds flexibility to the experimentation, when the user is able to tune the design to have as close to uniform as desired or as strongly concentrated in one or more regions as desired. This is new capability that has been added to the SDoE module, and should provide the experimenter with ability to tailor the design to what is required. To use the Non-Uniform Space Filling design capability in the SDoE module, the requirements are that the candidate set contains (a) one column for each of the inputs to be used to construct the design, and (b) one column for the weights to be assigned to each candidate point, where larger values are weighted more heavily and will result in a higher density of points close to those locations. The Index column is again recommended, but not required.

.. figure:: figs/0_design_overview.png
   :alt: Home Screen
   :name: fig.design_overview
   
   Comparison of USF and NUSF designs

Key features of the two approaches that we use in this module are: a) designs will be constructed by selecting from a user-provided candidate set of input combinations, and b) historical data, which has already been collected can be integrated into the design construction to ensure that new data are collected with a view to disperse from where data are already available.

Why Space-Filling Designs?
--------------------------

Space-filling designs are a design of experiments strategy that is well suited to both physical experiments with an accompanying model to describe the process and to computer experiments. The idea behind a space-filling design is that the design points are spread throughout the input space of interest. If the goal is to predict values of the response for a new set of input combinations within the ranges of the inputs, then having data spread throughout the space means that there should be an observed data point relatively close to where the new prediction is sought.

In addition, if there is a model for the process, then having data spread throughout the input space means that the consistency of the model to the observed data can be evaluated at multiple locations to look for possible discrepancies and to quantify the magnitude of those differences throughout the input space.

Hence, for a variety of criteria, a space-filling design can serve as good choice for exploration and for understanding the relationship between the inputs and the response without making a large number of assumptions about the nature of that relationship. As we will see in subsequent examples, the sequential approach allows for great flexibility to leverage what has been learned in early stages to influence the later choices of designs. In addition, the candidate-based approach that is supported in this module has the advantage that it can make the space-filling approach easier to adapt to design space constraints and specialized design objectives that may evolve through the stages of the sequential design.


We begin with some basic terminology that will help provide structure to the process and instructions below.

*	Input factors – these are the controllable experimental settings that are manipulated during the experiment. It is important to carefully define the ranges of interest for the inputs (eg. Temperature in [200°C,400°C]) as well as any logistical or operational constraints on these input factors (eg. Flue Gas Rate < 1000 kg/hr when Temperature > 350°C)

*	Input combinations (or design runs) – these are the choices of settings for each of the input factors for a particular run of the experiment. It is assumed that the implementers of the experiment are able to set the input factors to the desired operating conditions to match the prescribed choice of settings.

* Input space (or design space) – the region of interest for the input factors in which the experiment will be run. This is typically constructed by combining the individual input factor ranges, and then adapting the region to take into account any constraints. Any suggested runs of the experiment will be located in this region.

*	Responses (or outputs) – these are the measured results obtained from each experimental run. These are most desirably quantitative summaries of a characteristic of interest from running the process at the prescribed set of operating conditions (eg. CO2 capture efficiency is a typical response of interest for CCSI).

*	Design criterion / Utility function – this is a mathematical expression of the goal (or goals) of the experiment that is used to guide the selection of new input combinations, based on the prior information before the start of the experiment and during the running of the experiment. The design criterion can be based on a single goal or multiple competing goals, and can be either static throughout the experiment or evolve as goals change in importance over the course of the experiment. Common choices of goals for the experiment are:

#.	exploring the region of interest, 

#.        improving the precision (or reducing the uncertainty) in the estimation of model parameters, 

#.	improving the precision of prediction for new observations in the design region, 

#.        quantifying the discrepancy between the model and data, or 

#.	optimizing the value of responses of interest. 

An ideal design of experiment strategy uses the design criterion to evaluate potential choices of input combinations to maximize the improvement in the criterion over the available candidates. If the optimal design strategy is sequential, then the goal is to use early results from the beginning of the experiment to guide the choice of new input combinations based on what has been learned about the responses.


Matching the Design Type to Experiment Goals
--------------------------------------------

At different stages of the sequential design of experiments, different objectives are common. We outline some common progressions of objectives for experiments that we have worked with in the CCSI project. Often in the early stages of experimentation, little is known about the response and its characteristics. Hence, a first experiment often involves **exploration**, where the goal is to gain some preliminary understanding of the characteristics of the response across the input region of interest. Depending on how easy it is to collect and process data, this exploration might be done in a single first experiment, or there may be opportunities to do several smaller stages. It is particularly beneficial to do the exploration step in smaller stages if there is uncertainty about what areas of the input space are feasible. This can help save resources by exploring slowly and eliminating regions where there are problems.

After initial exploration, a common next step in the sequence of experiments is **model refinement**. For many CCSI experiments, the physical experiments are being collected in conjunction with an underlying science-based model. The data collection from a physical experiment is used to calibrate the model, and provide feedback about where model performance needs improvement (both resolving inaccurate characterization of features and high uncertainty). Often after the first set of data, regions of the input space perform well, while others have issues, such as large uncertainty, as measured by the width of a prediction or confidence interval.

.. figure:: figs/0_sdoe_sequence.png
   :alt: Home Screen
   :name: fig.sdoe_steps
   
   SDOE sequence of steps


Using the SDoE Module - The Basics
----------------------------------

In this section, we will describe the basic steps in for creating a design with this module. We first give details for the Uniform Space Filling Design, and then give a second set of details for a Non-Uniform Space Filling design. 


When you first click on the  **SDOE** button from the main FOQUS homepage, a first window appears. To create a design, the progression of steps takes you through the **Ensemble Selection** box (top left), then a transition triggered by the **Confirm** button to the **Ensemble Aggregation** box, and finally there are optional changes that can be made in the box at the bottom of the window. The final step in this window is to click on which type of design do you want to construct **Uniform Space Filling** or **Non Uniform Space Filling**. 

Basic Steps for a Uniform Space Design
======================================
  
We now consider some details for each of these steps:

1. In the **Ensemble Selection** box, click on the **Load from File..** button to select the file(s) for the construction of the design. Several files can be selected and added to the box listing the chosen files.

.. figure:: figs/1U_starting_screen.png
   :alt: Home Screen
   :name: fig.sdoe_home
   
   SDOE Home Screen
   
2. For each of the files selected using the pull-down menu, identify them as either a **Candidate** file or a **History** file. **Candidate** .csv files are comprised of possible input combinations from which the design can be constructed. The columns of the file should contain the different input factors that define the dimensions of the input space. The rows of the file each identify one combination of input values that could be selected as a run in the final design. Typically, a good candidate file will have many different candidate runs listed, and they should fill the available ranges of the inputs to be considered. Leaving gaps or holes in the input space is possible, but generally should correspond to a region where it is not possible (or desirable) to collect data.

**History** .csv files should have the same number of columns for the input space as the candidate file (with matching column names), and represent data that have already been collected. The algorithm for creating the design aims to place points in different locations from where data have already been obtained, while filling the input space around those locations.

Both the **Candidate** and **History** files should be .csv files that has the first row as the Column heading. The Input columns should be numeric. Additional columns are allowed and can be identified as not necessary to the design creation at a later stage.


3. Click on the **View** button to open the **Preview Inputs** pop-up widow, to see the list of columns contained in each file. The left hand side displays the first few rows of input combinations from the file. Select the columns that you wish to see graphically in the right hand box , and then click on **Plot SDOE** to see a scatterplot matrix of the data. 

.. figure:: figs/2_view_candidates.png
   :alt: SDOE preview of inputs
   :name: fig.2_preview_inputs
   
   SDOE view candidate set inputs

.. figure:: figs/3_plot_candidates.png
   :alt: SDOE plot of inputs
   :name: fig.3_scatterplot_inputs

   SDOE plot of candidate set inputs
   
The plot shows histograms of each of the inputs on the diagonals to provide a view of the distribution of values as well as the range of each input. The off-diagonals show pairwise scatterplots of each pair of inputs. This should provide the experimenter with the ability to assess if the ranges specified and any constraints for the inputs have been appropriately captured for the specified candidate set. In addition, repeating this process for any historical data will provide verification that the already observed data have been suitably characterized.

4. Once the data have been verified for both the **Candidate** and **History** files, click on the **Confirm** button to make the **Ensemble Aggregation** window active.

.. figure:: figs/4U_ensemble_aggregate.png
   :alt: Home Screen
   :name: fig.4_ensemble_aggregate
   
   SDOE Ensemble Aggregation
   
5. If more than one **Candidate** file was specified, then the **aggregate_candidates.csv** file that was created will have combined these files into a single file. Similarly if more than one **Histoy** file was specified, then the **aggregate_history.csv** file has been created with all runs from these files. If only a single file was selected for either the  **Candidate** and **History** files, then their aggregated matching files will be the same as the original.

..
   There are options to view the aggregated files for both the candidate and history files, with a similar interface as was shown in step 3. In addition, a single plot of the combined candidate and history files can be viewed. In this plot the  points represent the candidate locations and points of already collected data from the history file are shown in different colors.

6. Once the data have been verified as the desired set to be used for the design construction, then click on the **Uniform Space Filling** button at the bottom right corner of the **Ensemble Aggregation** window. This opens the second SDOE window, which allows for specific design choices to be made.

.. figure:: figs/5U_second_window.png
   :alt: SDOE second window
   :name: fig.5U_second_window

   SDOE second window

7-USF. The first choice to be made for the design is whether to optimize using **minimax** or **maximin**. The first choice, **minimax**, looks to choose design points that minimize the maximum distance that any point in the input space (as characterized by the candidate set and historical data, if it is available) is away from a design point. Hence, the idea here is that if we want to use data to help predict new outcomes throughout the input space, then we never want to be too far away from an observed location. The second choice, **maximin** looks to choose a design where the design points are as far away from each other as possible. In this case, the design criterion is looking to maximize how close any two points are away from their nearest neighbor. In practice the two design criterion often give similar designs, with the **maximin** criterion tending to push the chosen design points closer to the edges of the specified regions. 

Hint: If there is uncertainty about some of the edge points in the candidate set being viable options, then **minimax** would be preferred. If the goal is to place points throughout the input space with them going right to the edges, than **maximin** would be preferred. Note, that creating the designs is relatively easy, so it may be helpful to try both approaches to examine them and then choose which is preferred.

8. The next choice to be made falls under **Design Specification**, where the experimenter can select the sizes of designs to be created. The **Min Design Size** specifies the smallest design size to be created. Note that the default value is set at **2**, which would lead to choosing the best two design runs from the candidate set to fill the space (after taking into account any historical data that have already been gathered).
The **Max Design Size** specifies the largest design size to be created. The default value is set at **8**, which means that if this combination were used, designs would be created of size 2, 3, 4, 5, 6, 7 and 8. Hence, it may be prudent to select a relatively small range of values to expedite the creation of the designs, as each of these choices triggers a separate optimization search. In the figure above, the **Min Design Size** has been changed to 4, so that only the designs of size 4, 5, 6, 7 and 8 will be created.
 
9. Next, there are options for the columns of the candidate set to be used for the construction of the design. Under **Include?** in the box on the right hand side, the experimenter has the option of whether particular columns should be included in the space-filling design search. Unclick a box, if a particular column should not be included in the search.

Next select the **Type** for each column. Typically most of the columns will be designated as **Inputs**, which means that they will be used to find the best design. In addition, we recommend including one **Index** column which contains a unique identifier for each run of the candidate set. This makes tracking which runs are included in the constructed designs easier. If no **Index** column is specified, a warning appears later in the process, but this column is not strictly required.

Finally, the **Min** and **Max** columns in the box allow the range of values for each input column to be specified. The default is to extract the smallest and largest values from the candidate and history data files, and use these. This approach generally works well, as it scales the inputs to be in a uniform hypercube for comparing distances between the design points. 

Hint: the default values for **Min** and **Max** can generally be left at their defaults unless: (1) the range of some inputs represent very different amounts of change in the process. For example, if temperature is held nearly constant, while a flow rate changes substantially, then it may be desirable to extend the range of the temperature beyond its nominal values to make the amount of change in temperature more commensurate with the amount of change in the flow rate. (2) if changes are made in the candidate or history data files. For example, if one set of designs are created from one candidate set, and then another set of designs are created from a different candidate set. These designs and the achieved criterion value will not be comparable unless the range of each input has been fixed at matching values.

10. Once the design choices have been made, click on the **TestSDOE** button. This generates a small number of iterations of the search algorithm to calibrate the timing for constructing and evaluating the designs. The time taken to generate a design is a function of the size of the candidate set, the size of the design, as well as the dimension of the input space. The slider below **TestSDOE** now indicates an estimate of the time to construct the designs across the range of the **Min Design Size** and **Max Design Size** specified. The smallest **Number of Random Starts** is 10^3 = 1000 is generally too small to produce a good design, but this will run very quickly. Powers of 10 can be chosen with an **Estimated Runtime** provided below the slider. 

.. figure:: figs/6U_after_test_SDOE.png
   :alt: SDOE second window
   :name: fig.6U_after_test_SDOE

   SDOE second window after clicking Test SDOE

Hint: The choice of **Number of Random Starts** involves a trade-off between the quality of the design generated and the time to generate the design. The larger the chosen number of random starts, the better the design is likely to be. However, there are diminishing gains for increasingly large numbers of random starts. If running the actual experiment is expensive, it is generally recommended to choose as large a number of random starts as possible for the available time frame, to maximize the  chance of an ideal design being found.

11. Once the slider has been set to the desired **Number of Random Starts**, click on the **Run SDOE** button, and initiate the construction of the designs. The progress bar indicates how design construction is progressing through the chosen range of designs between the **Min Design Size** and **Max Design Size** specified.

12. When the SDOE module has completed the design creation process, the left window **Created Designs** will be populated with files containing the results. The column entries summarize the key features of each of the designs, including **Optimality Method** (whether minimax or maximin was used), **Design Size** (d, the number of runs in the created design),
**# of Random Starts**, **Runtime** (number of seconds needed to create the design), **Criterion Value** (the value obtained for the minimax or maximin criterion for the saved design).

.. figure:: figs/7U_completed_designs.png
   :alt: SDOE second window
   :name: fig.7U_completed_designs

   SDOE Created Designs

13. To see details of the design, the **View** button at the right hand side of each design row can be selected to show a table of the design, as well as a pairwise scatterplot of the inputs for the chosen design. The table and plot of the design are similar in characteristics to their counterparts for the candidate set.

.. figure:: figs/8_view_design.png
   :alt: SDOE second window
   :name: fig.8_view_design

   SDOE table of created design
   
.. figure:: figs/9_plot_design.png
   :alt: SDOE second window
   :name: fig.9_plot_design

   SDOE pairwise plot of created design
   
14. To access the file with the generated design, go to the **SDOE_files** folder, and a separate folder will have been created for each of the designs. In the example shown, 5 folders were created for the designs of size 4, 5, 6, 7 and 8, respectively. In each folder, there is a file containing the design, with a name that summarizes some of the key information about the design. For example, **candidates_d6_n10000_w+G+lldg+L** contains the design created using the candidate set called candidates.csv, with d=6 runs, based on n=10000 random starts, and based on the 4 inputs W, G, lldg and L.

 .. figure:: figs/10_SDOE_directory.png
   :alt: SDOE second window
   :name: fig.10_SDOE_directory

   SDOE directory

When one of the design files is opened it contains the details of each of the runs in the design, with the input factor levels that should be selected for that run.

.. figure:: figs/11_design_file.png
   :alt: SDOE second window
   :name: fig.11_design_file

   SDOE file containing a created design
   

Basic Steps for a Non-Uniform Space Design
==========================================
  
We now consider some details for each of these steps for the second type of design, where we want to have different densities of design points throughout the input region:

1. In the **Ensemble Selection** box, click on the **Load from File..** button to select the file(s) for the construction of the design. Several files can be selected and added to the box listing the chosen files.

.. figure:: figs/1N_starting_screen.png
   :alt: Home Screen
   :name: fig.sdoeN_home
   
   SDOE Home Screen
   
2. For each of the files selected using the pull-down menu, identify them as either a **Candidate** file or a **History** file. **Candidate** .csv files are comprised of possible input combinations from which the design can be constructed. The columns of the file should contain the different input factors that define the dimensions of the input space, as well as a column that will be used to specify the weights associated with each of the design points. 

**History** .csv files should have the same number of columns for the input space as the candidate file (with matching column names), and represent data that have already been collected. Note that a weight column is also needed for the history file, as the calculation of how close each of the points are to each other requires this. The algorithm for creating the design aims to place points in different locations from where data have already been obtained, while filling the input space around those locations.

Both the **Candidate** and **History** files should be .csv files that has the first row as the Column heading. The Input and Weight columns should be numeric. Additional columns are allowed and can be identified as not necessary to the design creation at a later stage.

3. Click on the **View** button to open the **Preview Inputs** pop-up widow, to see the list of columns contained in each file. The left hand side displays the first few rows of input combinations from the file. Select the columns that you wish to see graphically in the right hand box , and then click on **Plot SDOE** to see a scatterplot matrix of the data. 

.. figure:: figs/3N_plot_candidates.png
   :alt: SDOE plot of inputs
   :name: fig.3_scatterplot_inputs

   SDOE plot of candidate set inputs
   
The plot shows histograms of each of the inputs on the diagonals to provide a view of the distribution of values as well as the range of each input. The off-diagonals show pairwise scatterplots of each pair of inputs. This should provide the experimenter with the ability to assess if the ranges specified and any constraints for the inputs have been appropriately captured for the specified candidate set. In addition, repeating this process for any historical data will provide verification that the already observed data have been suitably characterized. 

Note in this file, the “Values” column which contains the numbers that will be used to define the weights. The numerical values contained in this column do not have any restrictions, except (a) there is a value provided for each row in the candidate set, and (b) that larger values correspond to points that the user wishes to emphasize with regions with a higher density of design points.

4. Once the data have been verified for both the **Candidate** and **History** files, click on the **Confirm** button to make the **Ensemble Aggregation** window active.

5. If more than one **Candidate** file was specified, then the **aggregate_candidates.csv** file that was created will have combined these files into a single file. Similarly if more than one **Histoy** file was specified, then the **aggregate_history.csv** file has been created with all runs from these files. If only a single file was selected for either the  **Candidate** and **History** files, then their aggregated matching files will be the same as the original.

There are options to view the aggregated files for both the candidate and history files, with a similar interface as was shown in step 3. In addition, a single plot of the combined candidate and history files can be viewed. In this plot the  points represent the candidate locations and points of already collected data from the history file are shown in different colors.

6. Once the data have been verified as the desired set to be used for the design construction, then click on the **Non-Uniform Space Filling** button at the bottom right corner of the **Ensemble Aggregation** window. This opens the second SDOE window, which allows for specific design choices to be made.

.. figure:: figs/5N_second_window.png
   :alt: SDOE second window
   :name: fig.5_second_window

   SDOE second window

7. Unlike the Uniform Space Filling designs, the choice of the optimality criterion to be used is fixed at **maximin**. Recall that a **maximin** design looks to choose design points that are as far away from each other as possible. In this case, the design criterion is looking to maximize a weighted value of how close any two points are away from their nearest neighbor. 

8. The next choice to be made falls under **Scaling Method**, where the experimenter can select how the column specified in the **Weight** column will be scaled. The scaling translates the values in the column specified with the **Weight** label directly to the new range of [1, MWR], where MWR = Maximum Weight Ratio. The smallest value (MinValue) gets mapped to the value 1, while the largest value (MaxValue) gets mapped to the value MWR (which will be specified in the next step. For the **Direct MWR** option, the shape of the histogram of the values is preserved, through the formula: 

Scaled Weight = 1 + (MWR - 1)*(Value - MinValue)/(MaxValue - MinValue). 

For the **Ranked MWR** option, the values are sorted from smallest to largest (ties allowed) and then assigned a rank. Rank = 1 corresponds to the smallest value, while the largest Rank is the number of rows in the candidate set (NumCand). Then the scaled weights are assigned through the formula:

Scaled Weight = 1 + (MWR - 1)*(Rank - 1)/(NumCand - 1)

Note: The designs created are dependent on the choice of weights selected. The **Ranked MWR** choice creates a uniform order that results in a symmetric flat histogram for the weights, while the **Direct MWR** scaling preserved the shape of the original values. If the user is not sure which of the choices is better suited to their problem, it might be sensible to generate designs for both choices and compare the results to see which are a better match for spacing in the input space that is desired.
 
9. Next, there are options for the values of the Maximum Weight Ratio (**MWR**) to be used. This is an important step in the Non-Uniform Space Filling design process, as it gives the user control about how much difference there is in the density of points. Smaller values of MWR (close to 1), result in a nearly uniform design. Larger values result in a design that has a higher density of design points for the higher weighed regions, and more sparse for the lower weighted regions. Since how this value is also a function of the histogram of the values for the **Weight** column and the choice of the **Scaling Method**, we recommend constructing designs for several MWR values.

The user can specify up to 5 **MWR** values, where for each of the **MWR** boxes, there is a set of choices that range from 2 to 60. This range should provide considerably flexibility about how unequal the spacing is throughout the design space.

.. figure:: figs/9N_MWR_box.png
   :alt: MWR box
   :name: fig.9N_MWR_box

   Choice of MWR Value and Columns

Also in this step, the columns of the candidate set to be used for the construction of the design. Under **Include?** in the box on the right hand side, the experimenter has the option of whether particular columns should be included in the space-filling design search. Unclick a box, if a particular column should not be included in the search.

Next select the **Type** for each column. Typically most of the columns will be designated as **Inputs**, which means that they will be used to find the best design. For the Non-Uniform Space Design, there is a required column for the **Weights**, which designates which rows in the candidate to emphasize (bigger weights) and which to de-emphasize (smaller weights). In addition, we recommend including one **Index** column which contains a unique identifier for each run of the candidate set. This makes tracking which runs are included in the constructed designs easier. If no **Index** column is specified, a warning appears later in the process, but this column, while recommended, is not strictly required.

Finally, the **Min** and **Max** columns in the box allow the range of values for each input column to be specified. The default is to extract the smallest and largest values from the candidate and history data files, and use these. This approach generally works well, as it scales the inputs to be in a uniform hypercube for comparing distances between the design points. 

Hint: the default values for **Min** and **Max** can generally be left at their defaults unless: (1) the range of some inputs represent very different amounts of change in the process. For example, if temperature is held nearly constant, while a flow rate changes substantially, then it may be desirable to extend the range of the temperature beyond its nominal values to make the amount of change in temperature more commensurate with the amount of change in the flow rate. (2) if changes are made in the candidate or history data files. For example, if one set of designs are created from one candidate set, and then another set of designs are created from a different candidate set. These designs and the achieved criterion value will not be comparable unless the range of each input has been fixed at matching values.

10. Once the design choices have been made, click on the **TestSDOE** button. This generates a small number of iterations of the search algorithm to calibrate the timing for constructing and evaluating the designs. The time taken to generate a design is a function of the size of the candidate set, the size of the design, as well as the dimension of the input space. 

.. figure:: figs/10N_Test_SDOE.png
   :alt: Test SDOE
   :name: fig.10N_Test_SDOE

   Test SDOE timing

Note that the number of random starts looks very different from what was done with the Uniform Space Filling Design. In that case, the number of random starts was offered in powers of 10. In this case, since a more sophisticated search algorithm is being used, each random start will take longer to run, but few starts are needed. There is set of choices for the number of random starts, which ranges from 10 to 1000. Producing a sample design for demonstration purposes with a small number of random starts (say 10 to 30) should work adequately, but recall that the choice of **Number of Random Starts** involves a trade-off between the quality of the design generated and the time to generate the design. The larger the chosen number of random starts, the better the design is likely to be. However, there are diminishing gains for increasingly large numbers of random starts. If running the actual experiment is expensive, it is generally recommended to choose as large a number of random starts as possible for the available time frame, to maximize the  chance of an ideal design being found.

.. figure:: figs/10N_Test_SDOE_choices.png
   :alt: Test SDOE
   :name: fig.10N_Test_SDOE_choices

   Number of Random Start choices


11. Once the slider has been set to the desired **Number of Random Starts**, click on the **Run SDOE** button, and initiate the construction of the designs. The progress bar indicates how design construction is progressing through the chosen range of designs for each of the **MWR** values  specified.

12. When the SDOE module has completed the design creation process, the left window **Created Designs** will be populated with files containing the results. The column entries summarize the key features of each of the designs, including **MWR**, **Design Size** (d, the number of runs in the created design),
**# of Random Starts, n**, **Runtime** (number of seconds needed to create the design), **Criterion Value** (the value obtained for the maximin criterion for the saved design). Note that the criterion values are specific to the MWR value chosen, and hence should not be compared across different values.

.. figure:: figs/12N_completed_designs.png
   :alt: SDOE second window
   :name: fig.12N_completed_designs

   SDOE Created Designs

13. As with the Uniform Space Filling designs, to see details of the design, the **View** button at the right hand side of each design row can be selected to show a table of the design, as well as a pairwise scatterplot of the inputs for the chosen design. The table and plot of the design are similar in characteristics to their counterparts for the candidate set. If multiple designs were created with different **MWR** values (or using the different **Scaling Method* choices), it is helpful to examine the plots to compare their properties to those sought by the experimenter. A final choice should be made based on what is needed for the goals of the study.

   
14. As with the Uniform Space Filling designs, to access the file with the generated design, go to the **SDOE_files** folder, and a separate folder will have been created for each of the designs. In the example shown, 5 folders were created for the designs of size 4, 5, 6, 7 and 8, respectively. In each folder, there is a file containing the design, with a name that summarizes some of the key information about the design. For example, **candidates_d6_n10000_w+G+lldg+L** contains the design created using the candidate set called candidates.csv, with d=6 runs, based on n=10000 random starts, and based on the 4 inputs W, G, lldg and L.

When one of the design files is opened it contains the details of each of the runs in the design, with the input factor levels that should be selected for that run.
   
Examples: 
=========

Next, we illustrate the use of the SDOE capability for several different scenarios. Example 1 constructs several uniform space filling designs of size 8 to 10 runs for a 2-dimensional input space based on a regular square region with a candidate set that is a regularly spaced grid. Both minimax and maximin designs are constructed to illustrate the difference in the criteria.
Example 2 takes one of the designs created in Example 1, and considers how it might be used for sequential updating with additional experimentation. In this case the Example 1 design is considered as historical data, and the goal is to augment the design with several additional runs.

Example 3 considers a 5-dimensional input space based on a CCSI example, and demonstrates what the process of Sequential Design of Experiments might look like with several iterations of constructing uniform space filling designs.

The files for these tutorials are located in: **examples/tutorial_files/SDOE**


Example 1: Constructing Uniform Space Filling minimax and maximin designs for a 2-D input space
-----------------------------------------------------------------------------------------------

For this first example, the goal is to construct a simple space-filling design with between 8 and 10 runs in a 2-dimensional space based on a regular unconstrained square region populated with a grid of candidate points. 

1. From the FOQUS main screen, click the **SDOE** button. On the top left side, select **Load from File**, and select the SDOE_Ex1_Candidates.csv file from examples folder. This identifies the possible input combinations from which the design will be constructed. The more possible candidates that can be provided to the search algorithm used to construct the design, the better the design might be for the specified criterion. 

.. figure:: figs/Ex1_1_load_candidate.png
   :alt: Home Screen
   :name: fig.Ex1_1_load_candidate
   
   Ex 1 Ensemble Selection
   
2. Next, by selecting **View** and then **Plot** it is possible to see the grid of points that will be used as the candidate points. In this case, the range for each of the inputs, X1 and X2, has been chosen to be between -1 and 1.

.. figure:: figs/Ex1_2_candidate_grid.png
   :alt: Home Screen
   :name: fig.Ex1_2_candidate_grid
   
   Ex 1 Candidate Grid
   
3. Next, click on **Confirm** to advance to the **Ensemble Aggregation** Window, and the click on **Uniform Space Filling** to advance to the second SDOE screen, where particular choices about the design can be made. On the second screen, select **minimax** for the **Optiimality Method Selection**. Change the **Min Design Size** and **Max Design Size** to 8 and 10, respectively. This will construct 3 minimax designs of size 8, 9 and 10. Next, change the column called **Label** to be **Index**. This will mean that the design is not constructed using this as an input, but rather that the identifiers in this column will help identify which runs from the candidate set were chosen for the final designs. Since the ranges of each of X1 and X2 are the bounds that we want to use for creating this design, we do not need to change the entries in **Min** and **Max**.

.. figure:: figs/Ex1U_3_mM_choices.png
   :alt: Home Screen
   :name: fig.Ex1U_3_mM_choices
   
   Ex 1 Minimax design choices
   
4. Once the choices for the design have been specified, click on the **Test SDOE** button to estimate the time taken for creating the designs. For the computer on which this example was developed, if we ran the minimum number of random starts (10^3=1000), it is estimated that the code would take 4 seconds to create the three designs (of size 8, 9 and 10). If we chose 10^4=10000 runs, then the code is estimated to take 44 seconds. It is estimated that 10^5=100000 random starts would take 7 minutes and 11 seconds, while 10^6=1 million random starts would take approximately 1 hour, 12 minutes. In this case, we selected to create designs based on 100000 random starts, since this was a suitable balance between timeliness and giving the algorithm a chance to find the best possible designs. Hence, select 10^5 for the **Number of Random Starts**, and then click **Run SDOE**.  

5. Since we are also interested in examining maximin designs for the same scenario, we click on the **Reload Design Specifications** button in the **Created Design** window to repopulate the right window with the same choices that we made for all of the design options.

.. figure:: figs/Ex1_4_mM_created_designs.png
   :alt: Home Screen
   :name: fig.Ex1_4_mM_created_designs
   
   Ex 1 Minimax created designs
   
6. After changing the  **Optimality Method Selection** to **maximin**, click on **Test SDOE**, select 10^5 for the **Number of Random Starts**, and then click **Run SDOE**. After waiting for the prescribed time, the **Created Designs** window will have 6 created designs - three that are minimax designs and three that are maximin designs.

.. figure:: figs/Ex1_5_all_created_designs.png
   :alt: Home Screen
   :name: fig.Ex1_5_all_created_designs
   
   Ex 1 Created designs
   
7. We now consider the choices between the designs to determine which is the best match for our experimental goals. We can see a list of the selected design points by clicking **View** for any of the created designs, and **Plot** allows us to see the spread of the design points throughout the input region. Clearly, there is a trade-off between the cost of the experiment (larger number of runs involve more time, effort and expense) and how well the designs fill the space. There is also a small difference in priorities between the minimax and the maximin criteria. Minimax seeks to minimize how far any candidate point (which defines our region of interest) is from a design point. Maximin seeks to spread out the design points and maximize how close the nearest points are to each other. As noted previously, minimax designs tend to avoid putting too many points on the edge of the region, while maximin designs often place a number of points right on the edges of the input space. After considering all of the trade-offs between the alternatives, select the design that best matches the goals of the experiment.

8. The file for the selected design can be found in the **SDOE_files** folder. The design can then be used to guide the implementation of the experiment with the input factor levels for each run.

Example 2: Augmenting the Example 1 design in a 2-D input space with a Uniform Space Filling Design
---------------------------------------------------------------------------------------------------

In this example, we consider the sequential aspect of design, by building on the first example results. Consider the scenario where based on the results of Example 1, the experimenter selected to actually implement and run the 8 run minimax design.

1. In the **Ensemble Selection** box, click on **Load from File** to select the candidate set that you would like to use for the construction of the design. This may be the same candidate set that was used in Example 1, or it might have been updated based on what was learned from the first data collection. For example, if it was learned that one corner of the design space might not be desirable, then the candidate set can be updated to remove candidate points that are now considered undesirable. For the **File Type** leave the designation as **Candidate**.

To load in the experimental runs that were already collected, click on **Load from File** again, and select the design file that was created in the  **SDOE_files** folder. This time, change the **File Type** to **History**. If you wish to view either of the candidate or history files, click on **View** to see either a table or plot.

2. Click on the **Confirm** button at the bottom right of the **Ensemble Selection** box. This will activate the **Ensemble Aggregation** box.

3. After examining that the desired files have been selected, click on the the **Uniform Space Filling** button at the bottom right corner of the **Ensemble Aggregation** window. This will open the second SDOE window that shows the **Sequential Design of Experiments Set-Up** window on the right hand side.

4. Select **Minimax** or **Maximin** for the type of design to create.

5. Select the **Min Design Size** and **Max Design Size** to match what is desired. If you wish to just generate a single design of the desired size, make **Min Design Size** = **Max Design Size**. Recall that this will be the number of additional points that will be added to the existing design, not the total design size.

6. Next, select the options desired in the box: a) Should any of the columns be excluded from the design creation? If yes, then unclick the **Include?** box.  b) For input factors to be used in the construction of the uniform space filling design, make sure that the **Type** is designated as **Input**. If there is a label column for the candidates, then designate this as **Index**.  c) Finally, you can optionally change the **Min** and **Max** ranges for the inputs to adjust the relative emphasis that distances in each input range are designated.

7. Once the set-up choices have been made, click **Test SDOE** to find out what the anticipated time is for generating designs based on different numbers of random starts.

8. Select the number of random starts to use, based on available time. Recall that using more random starts is likely to produce a design that is closer to the overall best optimum.

9. When the SDOE module has created the design(s) and the left window **Created Designs** is populated with the new design(s). These can be viewed with the **View** option, where the plot now shows the **History Data** with one symbol, and the newly added possible design with another symbol. This allows better assessment of the appropriateness of the new design subject to the data that have already been collected.

10. To access the file that contains the created designs, go to the **SDOE_files** folder. As before, a separate folder will have been created for each design.

11. If there is a desire to do another set in the sequential design, then the proceedure outlined above for Example 2 can be followed again. The only change will be that this time there will be 3 files that need to be imported: A **Candidate** file from which new runs can be selected, and two **History** files. The first of these files will be the selected design from Example 1, and the second the newly created design that was run as a result of Example 2. When the user clicks on **Confirm** in the **Ensemble Selection** window, the two **History** files will be aggregated into a single **Aggregated History** file.

Example 3: A Uniform Space Filling Design for a Carbon Capture example in a 5-D input space
-------------------------------------------------------------------------------------------

In this example, we consider a more realistic scenario of a sequential design of experiment. Here we explore a 5-dimensional input space with G, lldg, CapturePerc, L and SteamFlow denoting the space that we wish to explore with a space-filling design. the candidate set, **Candidate Points 8perc**, contains 93 combinations of inputs that have been validated using an ASPEN model as possible combinations for this scenario. The goal is to collect 18 runs in two stages that fill the input space. There are some constraints on the inputs, that make the viable region irregular, and hence the candidate set is useful to avoid regions where it would be problematic to collect useful data.

1. After selecting the **SDOE** tab in FOQUS, click on **Load from File** and select the candidate file, **Candidate Points 8perc**. 

.. figure:: figs/Ex3_view1.png
   :alt: Home Screen
   :name: fig.Ex3_view1
   
   Ex 3 Ensemble Selection window
   
2. To see the range of each input and how the viable region of interest is captured with the candidate set, select **View** and then plot. In this case we have chosen to just show the 5 input factors in the pairwise scatterplot.

.. figure:: figs/Ex3_candidate_plot.png
   :alt: Home Screen
   :name: fig.Ex3_candidate_plot
   
   Ex 3 plot of viable input space as defined by candidate set
   
3. After clicking **Confirm** in the **Ensemble Selection** box, and then **Uniform Space Filling** from the **Ensemble Aggregation** box, the **SDOE Set-up** box will appear on the right side of the second window. Here, select the options desired for the experiment to be run. For the illustrated figure, we selected a **Minimax** design with 3 potential sizes: 10, 11, 12. We specified that the column **Test No.** will be used as the Index, **G, lldg, CapturePerc, L, SteamFlow** will define the 5 factors to be used as inputs. We unclicked the **Include?** box for **CO2 captured** since we do not want to use it in the design construction.

.. figure:: figs/Ex3_setup.png
   :alt: Home Screen
   :name: fig.Ex3_setup
   
   Ex 3 set-up window for first stage
   
4. After running **Test SDOE** and selecting the number of random starts to be used, click **Run SDOE**. After the module has created the requested designs, they can be viewed and compared.

.. figure:: figs/Ex3_created_designs.png
   :alt: Home Screen
   :name: fig.Ex3_created_designs
   
   Ex 3 10,11,12 run designs created for first stage
   
5. By clicking **View** and then **Plot**, the designs can be viewed. Suppose that the experimenter decides to use the 12 run design in the initial phase, then this would be the design that would be implemented and data collected for these 12 input combinations.

.. figure:: figs/Ex3_12run_design.png
   :alt: Home Screen
   :name: fig.Ex3_12run_design
   
   Ex 3 chosen experiment for first stage
   
6. After these runs have been collected, the experimenter wants to collect additional runs. In this case, return to the first SDOE module window, and load in the candidate set (which can be change to reflect any knowledge gained during the first phase, such as undesirable regions or new combinations to include). The completed experiment should also be included as a **Hitory** file, by going to the **SDOE_files** folder and selecting the file containing the appropriate design.

.. figure:: figs/Ex3_ensemble_w_history.png
   :alt: Home Screen
   :name: fig.Ex3_ensemble_w_history
   
   Ex 3 ensemble selection box for second stage
   
7. After clicking **Confirm** in the **Ensemble Selection** box, and then **Uniform Space Filling** from the **Ensemble Aggregation** box, the **SDOE Set-up** box will appear on the right side of the second window. Here, select the options desired for the experiment to be run. For the illustrated figure, we selected a **Minimax** design with a design sizes of 6 (to use the remaining available budget). We again specified that the column **Test No.** will be used as the Index, **G, lldg, CapturePerc, L, SteamFlow** will define the same 5 factors to be used as inputs. 

.. figure:: figs/Ex3_setup_round2.png
   :alt: Home Screen
   :name: fig.Ex3_setup_round2
   
   Ex 3 setup box for second stage
   
8. After running **Test SDOE** and selecting the number of random starts to be used, click **Run SDOE**. After the module has created the requested design, they can be viewed. After selecting **View** and then **Plot**, the experimenter can see the new design with the historical runs included. This provides a good plot to allow the complete sequence of two experiments to be examined as a combined set of runs. Note that the first and second stages are shown in different colors and with different symbols.

.. figure:: figs/Ex3_6run_round2.png
   :alt: Home Screen
   :name: fig.Ex3_6run_round2
   
   Ex 3 setup box for second stage  
