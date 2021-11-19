.. _run_foqus:

Run FOQUS
---------

The specific command to launch FOQUS depends on the operating system.

To launch FOQUS, open the Anaconda prompt (or appropriate terminal or shell depending on operating
system and choice of Python), and run the following commands::

    conda activate ccsi-foqus
    foqus

Alternatively on Windows you can start FOQUS by double-clicking on the "ccsi-foqus" Desktop
shortcut created when FOQUS was first installed.  That shortcut can be recreated at any time by
opening a terminal, as described above, and starting FOQUS with the "make shortcut" option::

    foqus --make-shortcut

.. note::
   The first time FOQUS is run, it will ask for a working directory location.  This is the location
   FOQUS will put any working files. This setting can be changed later.

.. note::
   Files passed as command line arguments to FOQUS will be relative to where FOQUS is run. Once
   FOQUS starts, file paths will be relative to the FOQUS working directory.

Running FOQUS without a graphical interface ("batch" or "headless" mode)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default usage mode for FOQUS is through its graphical interface, or GUI.
However, it's still still possible to use FOQUS in situations where a graphical interface is not available and/or practical,
such as batch computing (e.g. in an HPC cluster) or automation (e.g. within a script).

To enable this mode, set the :code:`QT_QPA_PLATFORM` environment variable to one of the supported values *before* starting FOQUS,
e.g., for the Bash shell:

.. code-block:: bash

   export QT_QPA_PLATFORM=minimal


.. note::
   If FOQUS is not configured to enable batch/headless mode as described above, the following error messages might occur when starting FOQUS:

   .. code-block:: none

     PyQt5 or Qt not available

   or:

   .. code-block:: none

     qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
     This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

     Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.

If, on the contrary, a graphical interface *is* desired but the errors above occur, it is possible that the system is not yet configured to support graphical applications.
In this case, try installing the :code:`libgl1-mesa-glx` and/or :code:`libxkbcommon-x11-0` packages using
the package manager appropriate for your Linux distrubution (i.e. :code:`apt-get install` on Ubuntu).
