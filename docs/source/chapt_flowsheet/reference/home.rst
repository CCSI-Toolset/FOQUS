Home Menu
=========

Session Information Display
---------------------------

Information related to a flowsheet and tool settings is organized into a FOQUS session. The session screen displays information about the current session. A menu is available by clicking the **Session** drop-down menu. The figure below illustrates the Home window.

.. figure:: ../figs/homescreen.svg
    :width: 600px
    :align: center
    :figclass: align-center

    Home Screen


1. The buttons displayed at the top of the Home window, excluding **Help**, are tab-like buttons that change the window when selected. The depressed button indicates the currently displayed window.

  A. **Session** displays the Session window, which contains a description of the session that is currently open. **Session** has a drop-down menu that displays the Session menu.
  B. **Flowsheet** displays the meta-flowsheet editing window.
  C. **Uncertainty** displays the interface for PSAUDE and UQ visualization.
  D. **Optimization** displays the simulation-based optimization interface.
  E. **OUU** displays the optimization under uncertainty interface.
  F. **Surrogates** displays the surrogate model generation window.
  G. **DRM-Builder** displays the dynamic reduced model builder, which can be used to develop reduced models for dynamic simulations.
  H. **Settings** displays the main FOQUS settings window.

2. **Help** toggles the Help browser. The Help browser contains HTML help, as well as additional licensing information about other libraries and software included in the FOQUS installation.

3. The main Session window displays information about the current session and is divided into three tabs:

  * **Metadata** displays information about the current FOQUS session. The **Session Name** provides a descriptive name for the session. This name is used by the data management framework and when running flowsheets remotely, so a name is required. Entering a name should be the first step in creating a FOQUS flowsheet. **Version** number can be used to keep track of changes to a FOQUS session. **Confidence** describes whether the FOQUS session is expected to produce reliable results or not. **ID** is a unique identifier to identify a particular saved version of the session. **Creation Time** is the date and time that the flowsheet was first saved. **Modification Time** is the time and date that the flowsheet was last saved.
  * **Description** displays a detailed explanation of the purpose of the current session file, the problem being solved, and other useful information provided by the creator of the session file.
  * **Change Log** displays a record of changes made to the file. If the **Automatically create backup session file, when saving changes** checkbox is selected in FOQUS **Settings**, a backup file should exist for entries in the **Change Log**. The backup can be matched to the **Change Log** by the unique identifier appended to the file name.

Session Menu
------------

The figure below illustrates the **Session** menu.

.. figure:: ../figs/sessionMenu.svg
    :width: 300px
    :align: center
    :figclass: align-center

    Home Window, Session Drop-Down Menu


Adding or Changing Turbine Simulations
--------------------------------------


.. figure:: ../figs/turbineUpload.svg
    :width: 500px
    :align: center
    :figclass: align-center

    Turbine Upload Dialog Box
