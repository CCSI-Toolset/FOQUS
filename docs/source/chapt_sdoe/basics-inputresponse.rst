Basic Steps for an Input-Response Space-Filling Design
=======================================================

We now consider some details for each of these steps for the third type of design, where we want to have a design that seeks to balance even spacing in the input space with even spacing in the response space.

The algorithm works by finding the set of non-dominated designs that reside on a pareto front, including the single best design in the input space on one extreme, and the best design in the response space on the other. In the middle are a number of compromise designs that trade off different levels of space-filling properties in the input and response spaces. The experimenter is encouraged to examine all created designs on the pareto front (even creating multiple pareto fronts of designs if desired) and choose the design with the preferred balance of input and response space-filling. 

A step-by-step guide for using the SDOE module to create an Input-Response Space-Filling design is given below. For a set of worked examples, see the Examples section. 

1.
In the **Design Setup** box, click on the **Load Existing Set** button to select the file(s) to be used for the construction of the design. Several files can be selected and added to the box listing the chosen files.

.. figure:: figs/irsfb-0101-page1start.png
   :alt: Home Screen IRSF
   :name: fig.irsfb-home
   
   SDOE Module Home Screen

2.
For each of the files selected, using the pull-down menu, identify them as either a **Candidate file** or a **Previous Data** file. **Candidate** .csv files are comprised of possible input (and response) combinations from which the design can be constructed. The columns of the file should contain the different input factors that define the dimensions of the input space, with one or more columns of response values included for each input combination. Typically, these response values are determined from a previously-validated model of the underlying process. In fact, the determination of even spacing in the response space is only as trustworthy as the model used. 

.. note::
   It is important to make sure the process model is reliable and provides consistent results before attempting an input-response space-filling design.  If not, a better design fit would be using a uniform space-filling design. 

As previously stated, there is a requirement for at least one column to contain the response values. If this is not provided, then an input-response space-filling design cannot be created.

**Previous Data** .csv files should have the same number of columns for the input space as the candidate file (with matching column names), and represent data that have already been collected. Note that at least one response column is also required for the previous data file, as the determination of even spacing in the response space when taking into account previous data and the created design requires this. The algorithm for creating the design aims to place points farther away from locations where data have already been obtained, in both the input space and response space, while also filling the space around those locations.

Both the **Candidate** and **Previous Data** files should be .csv files that have the first row as the Column headings. The Input and Response columns should be numeric. Additional columns are allowed and can, if desired, be identified as not necessary to the design creation algorithm at a later stage.

3. 
Click on the **View** button to open the **Preview Inputs** pop-up window, to see the list of columns contained in each file. The left-hand side displays the first few rows of input combinations and responses from the file. Select the columns that you wish to see graphically in the right-hand box, and then click **Plot SDOE** to see a scatterplot matrix of the data.

.. figure:: figs/irsfb-0102a-candsetpreview.png
   :alt: View Candidate Set
   :name: fig.irsfb-candsetview
   
   Viewing Candidate Set

Displayed on the diagonals of the scatterplot matrix are histograms of each of the columns. These plots provide a view of the distribution of values as well as the range of each input. The off-diagonals show pairwise scatterplots of each pair of columns selected. This should provide the experimenter with the ability to assess if the ranges specified and any constraints for the inputs have been appropriately captured for the specified candidate set. In addition, repeating this process for any previous data will provide verification that the already observed data have been suitably characterized.

4. 
Once the data have been verified for both the **Candidate** and **Previous Data** files, click on the **Continue** button to make the **Design Construction** window active.

5. 
If more than one **Candidate** file was specified, then the **aggregate_candidates.csv** file that was created will have combined these files into a single file. Similarly, if more than one **Previous Data** file was specified, then the **aggregate_previousData.csv** file has been created with all runs from these files. If only a single file was selected for either of the **Candidate** or **Previous Data** files, then its corresponding aggregated file will be the same as the original.

To view the aggregated files for both the candidate and previous data files (if provided), click View, which lies in the right-most column of the Output Directory row. Once selected, this has a similar interface as that shown in step 3. If both types of files have been provided, a single plot of the combined candidate and previous data files will be displayed. In this plot, the points representing the candidate locations and points of already collected data from the previous data file are shown in different colors. 


.. figure:: figs/irsfb-0102b-page1after.png
   :alt: Home Page Design Construction Window
   :name: fig.irsfb-page1after
   
   SDOE Design Construction Window

.. note::
   If a candidate point, c, is close to a previous data point, p, and that candidate point, c, is chosen in the design, then we might expect the value of the response at c to be quite similar to the response value at p nearby. This means that the chosen design won’t give as much information about the process as if a different design was chosen. To gain as much new information as possible in the experiment, ensure that candidate points do not reside too close to previous data points when viewing in Step 5. 

6. 
Once the data have been verified as the desired set to be used for the design construction, click on **Input-Response Space Filling** from the **Design Method** drop-down menu in the **Design Construction** window. This opens the second SDOE window, which allows for specific design choices to be made.

.. figure:: figs/irsfb-0103-page2full.png
   :alt: Second Page Design Choices
   :name: fig.irsfb-page2full
   
   SDOE Second Page

7. 
Similar to Non-Uniform Space Filling designs, the choice of the optimality criterion to be used is fixed at **maximin**. Recall that a **maximin** design looks to choose design points that are as far away from each other as possible. In this case, the design criterion is looking to maximize how close any two points in the input space are away from their nearest neighbor and the same in the response space.

8. 
Select the **Size** of the design desired. A larger design will give more information than a smaller design. This choice often comes down to the size of the budget for the design. 

9. 
Next select the **Type** for each column. In general, most of the columns should be designated as **Inputs**, which means they will be used to define the input space and to find the best design for the input space. For Input-Response Space-Filling designs in particular, there is a required column for the **Response**, which the experimenter will determine from the model. Multiple response columns can be given if desired. The algorithm will use the response(s) to find the best design for the response space. All of the Input and Response columns will be used in the determination of the pareto front of best designs in both spaces. 

In addition, there is a system-created **Index** column displayed amongst the other columns of the candidate set; it should be listed first. Using an index column makes tracking which runs are included in the constructed designs easier. It will have the name **“_id”** with a Min value of 1 and Max value that is the number of rows in the set. The **Type** will be pre-set to “Index”. If the candidate set already included an index column, simply uncheck the **Include?** checkbox next to the column name that should be left out of design creation. Only one Index column can be included in design creation. If using a different index column than the one provided, remember to change the **Type** to **Index**. 

Finally, the **Min** and **Max** columns in the box allow the range of values for each input column, except for **“_id”**, to be specified. The default is to extract the smallest and largest values from the candidate and previous data files, and use these. This approach generally works well, as it scales the inputs to be in a uniform hypercube for comparing distances between the design points.

.. note::
   The default values for **Min** and **Max** can generally be left at their defaults unless: (1) The range of some inputs represent very different amounts of change in the process. For example, if temperature is held nearly constant, while a flow rate changes substantially, then it may be desirable to extend the range of the temperature beyond its nominal values to make the amount of change in temperature more commensurate with the amount of change in the flow rate. This is a helpful strategy to make the calculated distance between any points a more accurate reflection of how much of an adjustment each input requires. (2) If changes are made in the candidate or previous data files. For example, if one set of designs are created from one candidate set, and then another set of designs are created from a different candidate set. These designs and the achieved criterion value will not be comparable unless the range of each input has been fixed at matching values.

10. 
Once the design choices have been made, click on the **Estimate Runtime** button. This generates a small number of iterations of the search algorithm to calibrate the timing for constructing and evaluating the designs. The time taken to generate a design is a function of the size of the candidate set, the size of the design, as well as the dimensions of the input space and response space.

.. figure:: figs/irsfb-0104a-numrandstarts.png
   :alt: SDOE Progress Box
   :name: fig.irsfb-numrandstarts
   
   Number of Random Starts

.. note::
   The number of random starts looks very different from what was done with the Uniform Space Filling Design. In that case, the number of random starts was offered in powers of 10. In this case, similar to Non-Uniform Space-Filling, since a more sophisticated search algorithm is being used, each random start takes longer to run, but generally many fewer starts are needed. There is a set of choices for the number of random starts, which ranges from 5 to 500. Producing a sample design for demonstration purposes with a small number of random starts (say 5 to 30) should work adequately, but recall that the choice of **Number of Random Starts** involves a trade-off between the quality of the design generated and the time to generate the design. The larger the chosen number of random starts, the better the design is likely to be. However, there are diminishing gains for increasingly large numbers of random starts. If running the actual experiment is expensive, it is generally recommended to choose as large a number of random starts as possible for the available time frame, to maximize the quality of the design generated.

.. figure:: figs/irsfb-0104b-nrs-dropdown-menu.png
   :alt: NRS Dropdown Menu
   :name: fig.irsfb-nrs-dropdown-menu
   
   Choosing the Number of Random Starts

11. 
Once the slider has been set to the desired **Number of Random Starts**, click on the **Run SDOE** button, and initiate the construction of the designs. 

12. 
When the SDOE module has completed the design creation process, the left window **Created Designs** will be populated with a single file containing all results. The column entries summarize the key features of the collection of designs, including **Design Size** (d, the number of runs in each of the created designs), **# of Random Starts** (n), **Runtime** (number of seconds needed to create the designs), **# of Designs** (the number of designs found on the pareto front). Clicking the **View** button in the **Plot SDOE** column gives a view of the pareto front, with options to examine each of the created designs individually.  

.. figure:: figs/irsfb-0105-createddesigns-partial.png
   :alt: Partial View of Created Designs Window
   :name: fig.irsfb-createddesigns-partial
   
   Created Designs Window

