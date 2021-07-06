.. _developer_main:

Developer Documentation
=======================

Since the `source code for all of FOQUS is publically available
<https://github.com/CCSI-Toolset/FOQUS>`_, the more adventurous user may wish to look at the
inner-workings of FOQUS to get a better understand how it works, contribute a fix to a bug, or add
new features to the source tree. Other members of our CCSI partnership (national laboratories,
industry and academic institutions) may be more actively involved in the development of FOQUS.

This chapter describes at a high level how any such person can set themselves up for getting,
building, running, testing, documenting and contributing to FOQUS development.

Development Tools, Technology and Process
-----------------------------------------

FOQUS is primarily written in Python. We use the following software development tools, technologies
and processes:

- GitHub is where the `FOQUS source code <https://github.com/CCSI-Toolset/FOQUS>`_ resides.

- We make extensive use of GitHub’s `Issue Tracker <https://github.com/CCSI-Toolset/FOQUS/issues>`_
  , `Pull Requests <https://github.com/CCSI-Toolset/FOQUS/pulls>`_ and `Project Boards
  <https://github.com/orgs/CCSI-Toolset/projects>`_ for managing the development tasks using a
  modified Kanban development process.

- `ReadTheDocs <https://foqus.readthedocs.io>`_ is used to generate and host our on-line
  documentation.

- `CircleCI <https://circleci.com/gh/CCSI-Toolset/FOQUS>`_ and `AppVeyor
  <https://www.appveyor.com/>`_ are the Continuous Integration system we use.

- `Anaconda <https://www.anaconda.com/distribution/>`_ for isolating Python runtime and development
  environment.

Developer Setup
---------------

Working as a developer is similar to how a user would work with FOQUS with the exception that they
will need a copy of the source to work with. Here is rough set of steps to get setup:

- Download and install `Anaconda <https://www.anaconda.com/distribution/>`_.

- In a terminal create a conda env in which to work::

    conda create --name ccsi-foqus python=3.7
    conda activate ccsi-foqus

- In a terminal, get the FOQUS source::

    conda activate ccsi-foqus
    cd CCSI-Toolset  # Or a dir of your choice
    git clone git@github.com:CCSI-Toolset/FOQUS.git  # Note: clone the FOQUS repo if you expect to contribute
    cd FOQUS

- Build and Install FOQUS as a developer::

    pip install -r requirements-dev.txt  # This will pick up both user and developer required packages.
    foqus  # Start the app


Run Tests
---------

From top level of foqus repo::

  pytest
  python foqus.py -s test/system_test/ui_test_01.py


Building the Docs locally
-------------------------

To build a local copy of the documentation::

    cd FOQUS/docs
    make clean html

Then open the file ``FOQUS/docs/build/html/index.html`` to view the results.

.. include:: ../contact.rst
