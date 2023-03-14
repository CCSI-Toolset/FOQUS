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

- We make extensive use of GitHub's `Issue Tracker <https://github.com/CCSI-Toolset/FOQUS/issues>`_
  , `Pull Requests <https://github.com/CCSI-Toolset/FOQUS/pulls>`_ and `Project Boards
  <https://github.com/orgs/CCSI-Toolset/projects>`_ for managing the development tasks using a
  modified Kanban development process.

- `ReadTheDocs <https://foqus.readthedocs.io>`_ is used to generate and host our on-line
  documentation.

- For Continuous Integration (CI) we use `GitHub Actions <https://github.com/CCSI-Toolset/FOQUS/actions>`_.

- `Anaconda <https://www.anaconda.com/distribution/>`_ for isolating Python runtime and development
  environment.

Developer Setup
---------------

Working as a developer is similar to how a user would work with FOQUS with the exception that they
will need a copy of the source to work with. Here is rough set of steps to get setup:

- Download and install `Anaconda <https://www.anaconda.com/distribution/>`_.

- In a terminal create a conda env in which to work::

    conda create --name ccsi-foqus -c conda-forge python=3.8 pywin32
    conda activate ccsi-foqus

- In a terminal, get the FOQUS source::

    conda activate ccsi-foqus
    cd CCSI-Toolset  # Or a dir of your choice
    git clone git@github.com:CCSI-Toolset/FOQUS.git  # Note: clone the FOQUS repo if you expect to contribute
    cd FOQUS

- Build and Install FOQUS as a developer::

    pip install -r requirements-dev.txt  # This will pick up both user and developer required packages.
    foqus  # Start the app

Pre-commit hooks (optional, but recommended)
--------------------------------------------

`Pre-commit hooks <https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks>`_ are scripts that are automatically run by Git "client-side" (i.e. on a developer's local machine)
whenever ``git commit`` is run. If the pre-commit scripts terminates with an error, the commit will be interrupted,
requiring the developer to address the failure before being able to complete the commit.

.. note:: This is different (and complementary to) "server-side" checks, i.e. scripts that check the code on the side of the Git remote
   *after* the code is committed and pushed, such as the Continuous Integration (CI) suite triggered whenever a commit is pushed to an open PR
   in the FOQUS GitHub repository.

Pre-commit checks are especially useful to ensure that the code is formatted correctly *before* it is pushed to the FOQUS GitHub repository, which otherwise typically would
cause the developer to 1) be notified by the failing CI check that the code wasn't formatted; 2) run the formatter manually; 3) create a new commit with the formatting changes; 4)
push the formatted code again.

FOQUS uses the `pre-commit <https://pre-commit.com/>`_ framework to manage a few hooks that are useful for FOQUS developers.

The ``pre-commit`` command is already installed as part of FOQUS's developer dependencies.
However, the pre-commit *checks* (i.e. the actual scripts that Git will be running) must be installed (using ``pre-commit install``) as a separate step whenever the FOQUS repository is cloned:

   .. code-block:: shell

     pre-commit install

For more information, refer to the `pre-commit "Quick Start" page <https://pre-commit.com/#quick-start>`_.

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
