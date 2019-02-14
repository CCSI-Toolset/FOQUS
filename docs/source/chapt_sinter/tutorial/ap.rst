Aspen Plus Configuration
========================

#. The initial steps for opening a simulation and entering metadata for
   an Aspen Plus simulation are similar to ACM. Refer to the SimSinter
   ACM tutorial `[sec.tut.simsinter.acm] <#sec.tut.simsinter.acm>`__. In
   this tutorial, a flash model “Flash_Example.bkp” installed in the
   “C:\SimSinterFiles\Aspen_Plus_Install_Test” is used as an example.
   Open the Aspen Plus file and enter the metadata as shown in Figure
   `[fig.sinter.ap.metadata] <#fig.sinter.ap.metadata>`__.

   .. figure:: ../figs/ap/04_MetaDataFilled.png
      :alt: SinterConfigGUI Simulation Meta-Data with Data Completed
      :name: fig.sinter.ap.metadata

      SinterConfigGUI Simulation Meta-Data with Data Completed

#. The **SinterConfigGUI Variable Configuration Page** displays as
   illustrated in Figure
   `[fig.sinter.ap.variableempty] <#fig.sinter.ap.variableempty>`__.
   Aspen Plus has no settings, so there are no setting variables in the
   input section. Unlike ACM, AspenPlus displays the **Variable Tree**
   on the left side, so the user can explore the tree as is done in
   Aspen Plus Tools :math:`\rightarrow` Variable Explorer.
   Unfortunately, searching is not possible.

   .. figure:: ../figs/ap/05_VariablesEmpty.png
      :alt: SinterConfigGUI Variable Configuration Page Empty Variables
      :name: fig.sinter.ap.variableempty

      SinterConfigGUI Variable Configuration Page Empty Variables

#. **Variable Tree** nodes can be expanded for searching (Figure
   `[fig.sinter.ap.expandtree] <#fig.sinter.ap.expandtree>`__).

   .. figure:: ../figs/ap/06_VariablesExpanded.png
      :name: fig.sinter.ap.expandtree

      SinterConfigGUI Variable Configuration Page Expanded Aspen Plus
      Variable Tree

#. The user can type the node address directly into the **Selected
   Path** field (this is useful for copy/paste from Aspen Plus’ Variable
   Explorer) (Figure
   `[fig.sinter.ap.selectvar] <#fig.sinter.ap.selectvar>`__). Click
   **Lookup** or **Preview** (which automatically causes the tree to
   expand and selects selected variables in the **Variable Tree**).

   .. figure:: ../figs/ap/07_VariablesSelected.png
      :name: fig.sinter.ap.selectvar

      SinterConfigGUI Variable Configuration Page Aspen Plus Variable
      Selected

#. To make the temperature of the Flash chamber an **Input Variable**,
   click **Make Input**. Additionally, the user can **Name** the
   variable, fix the **Description**, and enter the **Min/Max** fields
   by clicking on the appropriate text and entering it.

   .. figure:: ../figs/ap/08_VariablesInput.png
      :alt: SinterConfigGUI Variable Configuration Page Input Variable
      :name: fig.sinter.ap.inputvar

      SinterConfigGUI Variable Configuration Page Input Variable

#. Select an **Output Variable**, **Preview** it, and click **Make
   Output**. Next, update the fields as with the **Input Variable** to
   give a better **Name** and **Description**.

   .. figure:: ../figs/ap/09_VariablesOutput.png
      :alt: SinterConfigGUI Variable Configuration Page Output Variable
      :name: fig.sinter.ap.outputvar

      SinterConfigGUI Variable Configuration Page Output Variable

#. The task is complete. Save it by clicking **Save** or CTRL+S. The
   file is saved to the location specified in the SinterConfigGUI
   Simulation Meta-Data page. If the user wishes to save a copy under a
   different name, navigate back to the SinterConfigGUI Simulation
   Meta-Data page and change the name.
