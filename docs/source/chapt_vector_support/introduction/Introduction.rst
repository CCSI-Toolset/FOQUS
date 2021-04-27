Vector Variable Support Capability - Introduction
=================================================

Motivation:
-----------

Vector variables and parameters have often been a part of chemical process,
property, and economic models developed by scientists and engineers.
Some process variables of this kind, include component concentrations in a
material stream, and temperature, pressure, component concentration
profiles across separation columns used for absorption, regeneration, and
distillation operations. Model parameters for some physical and thermodynamic
properties like viscosity, surface tension, interfacial area, enthalpy, entropy,
fugacity, etc., are also vectors. Economic models include capital
and operating costs indexed over different components, like unit operations,
raw materials, utilities, and time horizon.

In order to develop or leverage such models for implementing simulation,
optimization, and quantitative analysis in general, it is important for the
modeling/model integration platform to support vector variables. Hence, the
vector variable support capability is introduced in FOQUS, to allow creating
and interfacing with vector variables across different modeling platforms like
Python, MATLAB, and Aspen Plus.


New Features in FOQUS for vector support:
-----------------------------------------

In order to support vector variables, along with continued support for scalar
variables, the following new features have been introduced in FOQUS:

1. Automated GUI enabled addition and deletion of input and output vector
variable elements in the node panel.

2. Access vector variable elements in the node script through a specific
index-based python syntax.

3. Automated GUI enabled modification of SimSinter files based on Aspen models,
for including the required vector variable elements in it.

4. Access vector variable elements from Aspen models by uploading the modified
SimSinter files to turbine, and loading the turbine simulation in a FOQUS node.

5. Run node simulations successfully with vector-based Python, Pyomo, Aspen,
and MATLAB models.

6. Access vector variable elements from the node, in the optimization module,
easily through an index-based python syntax.

Potential Applications:
-----------------------

The vector variable support capability in FOQUS can be used for various
applications based on the models, after they have been successfully set up.

Some of the applications include, but are not limited to:

1. Parameter estimation for vector-based models.

2. Decision making for process design, using sensitivity study for process
vector variables.

3. Access and analyze computational fluid dynamics model profiles.
