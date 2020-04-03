.. _sec.flowsheet.starting.foqus:

Getting Started
===============

Follow the installation instructions provided in the :ref:`install_main` chapter.

The first time FOQUS is started, the user is prompted to specify a working directory. The working
directory preference is stored in ``%APPDATA%\.foqus.cfg`` on Windows (APPDATA is an environment
variable). On Linux or OSX, the working directory is specified in ``$HOME/.foqus.cfg``. Additionally
the user can override the working directory when starting FOQUS by using the ``--working_dir
<working dir>`` or ``-w <working dir>`` command line option. Log files, user plugins, and files
related to other FOQUS tools are stored in the working directory. The working directory can be
changed at a later time from within FOQUS. A full list of FOQUS command line arguments is available
using the ``-h`` or ``--help`` arguments.
