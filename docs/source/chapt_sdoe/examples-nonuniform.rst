Example NUSF-1: Constructing Non-Uniform Space Filling maximin designs for a 2-D input space
-----------------------------------------------------------------------------------------------

For this first Non-Uniform Space Filling design example, the goal is to construct a non-uniform space-filling design with 15 runs in a 2-dimensional space based on a regular unconstrained square region populated with a grid of candidate points. The choice of how to construct the candidate set should be based on: a) what is the precision with which each of the inputs can be set in the experiment, and b) timing for generating the designs. Note that the finer the grid that is provided in the candidate set, the longer the search algorithm will take to run for a given number of random starts. In general a finer grid will give better options for the best design, but with diminishing returns after a large number of candidates have already been provided

As noted previously in the Basics section, in addition to specifying the candidate point input combinations, it is also required to supply an additional column of weights. This column will provide the necessary information about which regions of the input space should be emphasized more, and which should be emphasized less. The figure below shows some of the characteristics of the candidate set.

.. figure:: figs/NUSFex1-wts.png
   :alt: Home Screen
   :name: fig.NUSFex1-wts
   
   Ex NUSF1 Candidate set of points with their associated weights. Left shows the underlying relationship used to generate the design, and right shows the candidates with the size of the point proportional to the assigned weight.
   
The candidates are laid out in a regular grid with equal spacing between levels of each of X1 and X2. A contour plot of the weight function that was used to generate the weights is shown on the left side of the plot. The weights range from -14.48 to 50, with the  largest values of the weights near the bottom right corner of the input space. The smallest values lie in the top left corner. On the right hand side, we can see a plot where the relative size of the points is proportionate to the size of the weight assigned to that candidate point. This second representation is helpful when the candidate points do not fall on a regular grid, or if the relationship for determining the weights is not smooth.

Here is the process for generating NUSF designs for this problem:
1. From the FOQUS main screen, click the **SDOE** button. On the top left side, select **Load from File**, and select the "NUSFex1.csv" file from examples folder.

2. Next, by selecting **View** and then **Plot** it is possible to see the grid of points that will be used as the candidate points. In this case, the range for each of the inputs, X1 and X2, has been chosen to be between -1 and 1.

3. Next, click on **Confirm** to advance to the **Ensemble Aggregation** Window, and the click on **Non-Uniform Space Filling** to advance to the second SDOE screen, where particular choices about the design can be made.
