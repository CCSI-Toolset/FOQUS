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

.. note::
   If when running on a remote Linux server or Virtual Machine you encounter an
   error when starting FOQUS similar to:

   .. code-block:: none

     PyQt5 or Qt not available

   or:

   .. code-block:: none

     qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
     This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

     Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.

   Try installing the :code:`libgl1-mesa-glx` and/or :code:`libxkbcommon-x11-0` packages using
   the package manager appropriate for your Linux distrubution.  (i.e. :code:`apt-get install` on Ubuntu).
