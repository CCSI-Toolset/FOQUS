Examples
========

Next, we illustrate the use of the SDOE capability for several different scenarios. 

Example USF-1 constructs several uniform space filling designs of size 8 to 10 runs for a 2-dimensional input space based on a regular square region with a candidate set that is a regularly spaced grid. Both minimax and maximin designs are constructed to illustrate the difference in the criteria.
Example USF-2 takes one of the designs created in Example 1, and considers how it might be used for sequential updating with additional experimentation. In this case the Example 1 design is considered as historical data, and the goal is to augment the design with several additional runs.
Example USF-3 considers a 5-dimensional input space based on a CCSI example, and demonstrates what the process of Sequential Design of Experiments might look like with several iterations of constructing uniform space filling designs.

Example NUSF-1 constructs several non-uniform space filing designs of size 15 in a 2-dimensional regular input space. Several designs are generated using the same weights, but with different Maximum Weight Ratios (MWRs), to illustrate how the concentration of points can be altered to match the experimenter's preferences.
Example NUSF-2 considers a CCSI example, with a non-regular region, and the weights that were derived from the width of the confidence interval for prediction based on an existing model. The goal is to concentrate more of the new runs in regions where there is greater uncertainty, and hence the widths of the confidence intervals are larger. Again multiple designs are created to show how the MWR influences the concentration of the points in different regions.

Example IRSF-1 constructs a set of "best" designs (a Pareto front) along a spectrum of input and response space-filling. The designs are based on a 2-dimensional input space and a 1-dimensional response. Different designs along the Pareto front are compared to illustrate (a) what a Pareto front is and (b) how to choose a design from those on the Pareto front. 

The files for these tutorials are located in: **examples/tutorial_files/SDOE**

.. note:: |examples_reminder_text|

.. toctree::
    :maxdepth: 2

    examples-uniform
    examples-nonuniform
    examples-inputresponse
