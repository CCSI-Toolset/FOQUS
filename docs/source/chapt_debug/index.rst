Debugging
=========

This chapter contains information that may be helpful in resolving a
problem or filing a bug report.

How to Debug
------------

Log files may contain very useful information when reporting problems.
The log files are contained in the logs sub-directory of the FOQUS
working directory. To change the log message levels in FOQUS go to the
FOQUS **Settings** button from the Home window. From there various log
settings can be changed. The debugging log level provides the highest
level of information.

Almost any error that occurs in FOQUS should be logged. Occasionally, an
error may occur that is difficult to find, or causes FOQUS to crash
before logging it. In that case the “FOQUS Console” application can be
used. All output from FOQUS, including messages that cannot be seen
otherwise will be shown in a “cmd” window which will remain open even
after FOQUS closes.

| When running heat integration, the debugging information can be found
  in
| \\gams\HeatIntegration.lst. This file includes detailed results and
  errors returned by GAMS.

Most UQ routines interact with PSUADE via Python wrappers. When PSUADE
is running, the stdout is written to psuadelog in the working directory.
(At present, only some PSUADE commands write to this log; however, this
will be standardized in the near future so that all PSUADE commands
write to this log.) Other errors that are due to the Python wrappers or
PySide GUI components are written to the logs subdirectory in the
working directory.

Known Issues
------------

The following are known unresolved issues:

-  Calculator blocks that use Excel in Aspen Plus do not work in FOQUS,
   because they are not supported by the Aspen Plus COM interface, and
   can only be used in interactive mode.

-  The FOQUS flowsheet can be edited while a flowsheet evaluation,
   optimization, or UQ is running. This should not be allowed, and may
   cause unexpected behaviors. Currently changes to a flowsheet while
   running an evaluation will be ignored and reset when the evaluation
   is completed.

-  The win32com module generates Python code, which it needs to run.
   This code is generated in the FOQUS install location
   “\\dist\win32com\gen_py.” In some cases there may be a problem
   writing to that directory due to permission settings. This will
   prevent FOQUS from running simulations locally. If this error is
   encountered the solution is to make the “gen_py” directory user
   writable. So far, in testing, this error seems to occur in Windows 8
   and 10, but not 7.

-  FOQUS has trouble getting files from Turbine and saving them to the
   DMF when dealing with files in Turbine involving directories.

-  The default port for TurbineLite is 8080. If another program is
   already using port 8080, there will be an error in FOQUS when
   connecting to TurbineLite. In the **Turbine** Tab of the Settings
   window, there is a tool to change the TurbineLite port. If the
   TurbineLite port is changed the configuration file that FOQUS uses to
   connect to TurbineLite, must also be changed.

.. include:: ../contact.rst
