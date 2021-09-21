Example IRSF-1: Constructing Input-Response Space Filling maximin designs for a 2-D input space with 1-D response
=================================================================================================================

For this first Input-Response Space Filling design example, the goal is to construct a Pareto front of input-response space-filling designs, all with 20 runs in a 2-dimensional input space based on a regular unconstrained square region populated with a grid of candidate points, along with a single response variable. All designs on the Pareto front have a unique balance of space filling in the input space and response space, giving the experimenter latitude to choose which design is best for a particular situation. 

The choice of how to construct the candidate set should be based on: (a) what is the precision with which each of the inputs can be set in the experiment (the candidate set should not contain increments finer than what can be set in the experiment), and (b) timing for generating the designs. The finer the grid that is provided in the candidate set, the longer the search algorithm will take to run for a given number of random starts. In general, a finer grid will give better options for the best design, but with diminishing returns after a large number of candidates have already been provided.

As noted previously in the Basics section, in addition to specifying the candidate point input combinations, it is also required to supply an additional column of the likely response variable values (or multiple columns for multiple responses of interest). This column will be used to make sure that space filling is being accomplished in the response space as well as the input space. 

