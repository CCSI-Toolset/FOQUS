.. _install_python:

Install Python
--------------

Python version 3.7 up through 3.9 is required to run FOQUS.

We recommend using either the `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ or
`Anaconda <https://www.anaconda.com/download/>`_ Python distribution and package management
system. The choice of Miniconda or Anaconda is up to the user, with Miniconda being smaller and
quicker to download while Anaconda is larger but more self-contained. For Windows users, Anaconda is
likely a better choice as it also comes with the "Anaconda Prompt" which is a command terminal
already set up for working with Anaconda. The primary advantage of using Miniconda or Anaconda is
being able to isolate and customize a python environment specifically for FOQUS without having to
modify your existing system python environment. It does this by allowing the ordinary user the
ability to create self-contained python environments without any need for administrator
privileges. These separate environments can have different set of packages, isolating version
dependencies when working with multiple python projects.

If you have a working version of Python 3.7 through 3.9, which you prefer over Anaconda, you can
skip these steps.

Anaconda or Miniconda Install and Setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Download one of `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ or `Anaconda
   <https://www.anaconda.com/download/>`_.

2. Install the above package following the `install instructions
   <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_ for your operating
   system.

3. Create a ccsi-foqus conda environment; this environment will be referred to as ``ccsi-foqus`` in
   the installation documentation, but you can use any name you like.  If you would like to install
   multiple version of FOQUS (for example a stable version and the latest development version), this
   can be done by running the following command multiple times with different environment names
   after the ``--name`` flag in the below command.  In a terminal (or on Windows in the Anaconda
   Prompt) type::

    conda create --name ccsi-foqus -c conda-forge python=3.8 pywin32

   Then follow the prompts.  This will create a new conda environment with a minimal set of
   packages.  To use a different version of python, change the version specified after ``python=`` in
   the command.

   .. note::
      The command above installs the ``pywin32`` Conda package immediately after creating the Conda environment.
      The ``pywin32`` package is strictly required to run FOQUS on Windows, and should be installed with Conda from the ``conda-forge`` channel
      or errors might occur. For other platforms (Linux, macOS), the ``pywin32`` package is not required. However, the ``pywin32`` package itself is still available,
      and therefore the command above is compatible with all platforms for which FOQUS is supported.

4. Activate the environment on Linux in a terminal type::

    conda activate ccsi-foqus

If you create an environment in which to install FOQUS, you will need to ensure that environment is
active before installing FOQUS. On Windows, once FOQUS is installed a batch file is created that
will activate the proper environment when running FOQUS. On Linux or Mac, you will need to activate
the appropriate environment before running FOQUS.
