.. _run_foqus:

Run FOQUS
---------

The specific command to launch FOQUS depends on the operating system.

To launch FOQUS, open the Anaconda prompt (or appropriate terminal or shell depending on operating
system and choice of Python), and run the following commands:

Windows::

    conda activate ccsi-foqus
    python %CONDA_PREFIX%/Scripts/foqus.py

Linux or OSX::

    conda activate ccsi-foqus
    foqus.py

.. note::
   The first time FOQUS is run, it will ask for a working directory location.  This is the location
   FOQUS will put any working files. This setting can be changed later.

.. note::
   Files passed as command line arguments to FOQUS will be relative to where FOQUS is run. Once
   FOQUS starts, file paths will be relative to the FOQUS working directory.
