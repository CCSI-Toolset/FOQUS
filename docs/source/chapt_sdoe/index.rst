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

*	Utility function – this is a mathematical expression of the goal (or goals) of the experiment that is used to guide the selection of new input combinations, based on the prior information before the start of the experiment and during the running of the experiment. The utility function can be based on a single goal or multiple competing goals, and can be either static throughout the experiment or evolving as different goals change in importance over the course of the experiment. Common choices of goals for the experiment are:

#.	refining the region of interest, 

#. 	improving the precision (or reducing the uncertainty) in the estimation of model parameters, 

#.	improving the precision of prediction for new observations in the design region, 

#. 	quantifying the discrepancy between the model and data, or 

#.	optimizing the value of responses of interest. 

An optimal design of experiment strategy uses the utility function to evaluate potential choices of input combinations to maximize the improvement in the utility function over the available candidates. If the optimal design strategy is sequential, then the goal is to use early results from the beginning of the experiment to guide the choice of new input combinations based on what has been learned about the responses.

Using SDoE Module - A Simple Example
------------------------------------

For this first example, the goal is to construct a simple space-filling design with 8 runs in a 2-dimensional space using the example files provided with FOQUS. 

1. From the FOQUS main screen, click the **SDOE** button. On the top left side, select **Load from File**, and select the candidate.csv file from examples folder. 
(Figure `[fig:sdoe_home] <#fig:sdoe_home>'  ).

.. figure: ../figs/1_home.png
   :alt: Home Screen
   
   Home Screen
   
   [Fig:sdoe_home]
   
   
