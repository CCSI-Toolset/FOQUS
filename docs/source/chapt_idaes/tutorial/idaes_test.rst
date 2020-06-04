.. _tutorial.idaes.test:

Tutorial: Running IDAES model in FOQUS
===================================================

Consider the following process flowsheet that has been developed in IDAES:

.. figure:: ../figs/flowsheet.png
   :alt: Heater Flash Flowsheet
   :name: fig.flowsheet

**Feed Conditions:**

Flowrate = 1 kmol/hr

Temperature = 353 K

Pressure = 101325 K

Benzene Mole Fraction = 0.4

Toluene Mole Fraction = 0.6


**Heater Specification:**

Outlet Temperature (HTOUT stream) = 370 K


**Flash Specification:**

Heat Duty = 0 W

Pressure Drop = 0 Pa


The IDAES model for this flowsheet can be accessed and simulated in FOQUS as follows:

Instructions
~~~~~~~~~~~~

1. Open FOQUS, and under the Flowsheet Tab, create a Node named "IDAES_Model".

2. Open the Node Editor, and let the Model Type be “None”.

3. Add the following input variables with their corresponding values in the Node Editor:
   ``heater_inlet_molflow``: 1 kmol/hr

   ``heater_inlet_pressure``: 101325 Pa

   ``heater_inlet_temperature``: 353 K

   ``heater_inlet_benzene_molfrac``: 0.4

   ``heater_inlet_toluene_molfrac``: 0.6

   ``heater_outlet_temperature``: 370 K

   ``flash_heat_duty``: 0 W

   ``flash_pressure_drop``: 0 Pa

4. Add the following output variables with their corresponding values in the Node Editor:
   ``heater_heat_duty``

   ``flash_liq_molflow``

   ``flash_liq_pressure``

   ``flash_liq_temperature``

   ``flash_liq_benzene_molfrac``

   ``flash_liq_toluene_molfrac``

   ``flash_vap_molflow``

   ``flash_vap_pressure``

   ``flash_vap_temperature``

   ``flash_vap_benzene_molfrac``

   ``flash_vap_toluene_molfrac``

5. Under Node Script, set Script Mode to “Post”. This will ensure that the node script runs after the node simulation.
   Enter the following code for the IDAES model:

   .. code-block:: python
      :linenos:

      # Import objects from pyomo package
      from pyomo.environ import ConcreteModel, SolverFactory,TransformationFactory, value

      import pyutilib.subprocess.GlobalData
      pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False

      # Import the main FlowsheetBlock from IDAES. The flowsheet block will contain the unit model

      import idaes
      from idaes.core.flowsheet_model import FlowsheetBlock

      # Import the BTX_ideal property package to create a properties block for the flowsheet
      from idaes.generic_models.properties.activity_coeff_models import BTX_activity_coeff_VLE

      # Import heater unit model from the model library
      from idaes.generic_models.unit_models.heater import Heater

      # Import flash unit model from the model library
      from idaes.generic_models.unit_models.flash import Flash

      # Import methods for unit model connection and flowsheet initialization
      from pyomo.network import Arc, SequentialDecomposition

      # Import idaes logger to set output levels
      import idaes.logger as idaeslog

      # Create the ConcreteModel and the FlowsheetBlock, and attach the flowsheet block to it.
      m = ConcreteModel()

      m.fs = FlowsheetBlock(default={"dynamic": False}) # dynamic or ss flowsheet needs to be specified here

      # Add properties parameter block to the flowsheet with specifications
      m.fs.properties = BTX_activity_coeff_VLE.BTXParameterBlock(default={"valid_phase":
                                                           ('Liq', 'Vap'),
                                                           "activity_coeff_model":
                                                           "Ideal"})

      # Create an instance of the heater unit, attaching it to the flowsheet
      # Specify that the property package to be used with the heater is the one we created earlier.
      m.fs.heater = Heater(default={"property_package": m.fs.properties})

      m.fs.flash = Flash(default={"property_package": m.fs.properties})

      # Connect heater and flash models using an arc
      m.fs.heater_flash_arc = Arc(source=m.fs.heater.outlet, destination=m.fs.flash.inlet)

      TransformationFactory("network.expand_arcs").apply_to(m)

      #Feed Specifications to heater
      m.fs.heater.inlet.flow_mol.fix(x["heater_inlet_molflow"]*1000/3600) # converting to mol/s as unit basis is mol/s
      m.fs.heater.inlet.mole_frac_comp[0, "benzene"].fix(x["heater_inlet_benzene_molfrac"])
      m.fs.heater.inlet.mole_frac_comp[0, "toluene"].fix(x["heater_inlet_toluene_molfrac"])
      m.fs.heater.inlet.pressure.fix(x["heater_inlet_pressure"]) # Pa
      m.fs.heater.inlet.temperature.fix(x["heater_inlet_temperature"]) # K

      # Unit model specifications
      m.fs.heater.outlet.temperature.fix(x["heater_outlet_temperature"])
      m.fs.flash.heat_duty.fix(x["flash_heat_duty"])
      m.fs.flash.deltaP.fix(x["flash_pressure_drop"])

      #Flowsheet Initialization
      def function(unit):
              unit.initialize(outlvl=1)

      opt = SolverFactory('ipopt')
      seq = SequentialDecomposition()
      seq.options.select_tear_method = "heuristic"
      seq.run(m, function)

      # Solve the flowsheet using ipopt
      opt = SolverFactory('ipopt')
      solve_status = opt.solve(m)

      #Assign IDAES model output values to FOQUS output values
      f["flash_liq_molflow"] = value(m.fs.flash.liq_outlet.flow_mol[0])
      f["flash_liq_benzene_molfrac"] = value(m.fs.flash.liq_outlet.mole_frac_comp[0,"benzene"])
      f["flash_liq_toluene_molfrac"] = value(m.fs.flash.liq_outlet.mole_frac_comp[0,"toluene"])
      f["flash_liq_temperature"] = value(m.fs.flash.liq_outlet.temperature[0])
      f["flash_liq_pressure"] = value(m.fs.flash.liq_outlet.pressure[0])
      f["flash_vap_molflow"] = value(m.fs.flash.vap_outlet.flow_mol[0])
      f["flash_vap_benzene_molfrac"] = value(m.fs.flash.vap_outlet.mole_frac_comp[0,"benzene"])
      f["flash_vap_toluene_molfrac"] = value(m.fs.flash.vap_outlet.mole_frac_comp[0,"toluene"])
      f["flash_vap_temperature"] = value(m.fs.flash.vap_outlet.temperature[0])
      f["flash_vap_pressure"] = value(m.fs.flash.vap_outlet.pressure[0])
      f["heater_heat_duty"] = value(m.fs.heater.heat_duty[0])

   .. note::
      ipopt will need to be available in your environment.  To install it into your conda or pip environment you could use: ``conda install -c conda-forge ipopt`` or ``pip install ipopt``


   Once the model is solved, the values of flowsheet output variables are assigned to the node output variables.

6. Click the Run button to run the python script and check the node output variables section.

It should be noted that the values within Node Input Variables can be changed as per user’s requirement, to run different cases.

.. note::
   For more information on installing IDAES, along with building and solving IDAES models, refer to the IDAES documentation:
   https://idaes-pse.readthedocs.io/en/stable/index.html

   The complete FOQUS file (**FOQUS_IDAES.foqus**), that includes the IDAES model,
   is located in: **examples/tutorial_files/IDAES**
