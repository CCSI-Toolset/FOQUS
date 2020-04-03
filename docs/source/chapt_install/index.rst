.. _install_main:

FOQUS Installation and Running
==============================

This chapter covers how to install and run FOQUS as well as how to install other
optional components for use within FOQUS.

Quick Start
-----------

For those familiar with the details, here is a summary of how to install and run
FOQUS:

  - Download and install `Anaconda <https://www.anaconda.com/distribution/>`_.

  - In a terminal, to setup and install::
      
      conda create --name ccsi-foqus python=3.7
      conda activate ccsi-foqus
      pip install ccsi-foqus

  - In a terminal, to run::
      
      conda activate ccsi-foqus
      foqus.py   #  Linux or OSX
      python %CONDA_PREFIX%/Scripts/foqus.py  # On Windows

For a detailed explanations see the following sub-sections.

Contents
--------

.. toctree::
    :maxdepth: 1

    install_python
    install_foqus
    run_foqus
    install_optional
