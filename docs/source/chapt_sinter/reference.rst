SimSinter Configuration
=======================

SimSinter is the standard interface library that FOQUS and Turbine use
to drive the target simulation software.

SimSinter currently supports:

* AspenPlus (versions 8, 9, and 10)
* Aspen Custom Modeler (ACM) (versions 8, 9, and 10)
* gPROMS
* Microsoft Excel

SimSinter is used to: (1) open the simulator, (2) initialize the
simulation, (3) set variables in the simulation, (4) run the simulation,
and (5) get resulting output variables from the simulation.

To drive a particular simulation, SimSinter must be told which input
variables to set and which output variables to read when the simulation
is finished (there are generally far too many variables in a simulation
to set and read them all). Each simulation must have a “Sinter Config
File” which records this information. FOQUS keeps the simulation file
and the “Sinter Config File” together and sends them to the Turbine
gateway when a simulation run is requested.

The configuration is simplified by a GUI included with the SimSinter
distribution called, “SinterConfigGUI.” FOQUS can launch the
SinterConfigGUI on simulations that have not been configured. To run the
“SinterConfigGUI” the user must have:

#. SimSinter distribution installed. SimSinter is installed by the FOQUS
   bundle installer.

#. The simulation file the user wants to configure. For example, if the
   user has an Aspen Custom Modeler simulation called BFB.acmf, that
   file must be on the user’s computer, and the user should know its
   location.

#. The application used to execute the simulation file. For example, if
   the user wants to configure an Aspen Custom Modeler simulation called
   BFB.acmf, Aspen Custom Modeler must be installed on the user’s
   machine.

The rest of this section details two step-by-step tutorials on
configuring a simulation with “SinterConfigGUI.” The first simulation is
an Aspen Custom Modeler simulation and the second, Aspen Plus. Please
also see the D-RM Builder tutorials for configuring dynamic ACM models.
For more details on SimSinter or a tutorial on how to configure a
Microsoft Excel file, please see the “SimSinter Technical Manual,” which
is included in the FOQUS distribution. The default location is at
C:\Program Files (x86)\foqus\foqus\doc. It is also available on the CCSI
website.
