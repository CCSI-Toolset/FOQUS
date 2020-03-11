.. _tutorial.pyomo.test:

Tutorial: Running PYOMO Optimization Model in FOQUS
===================================================

Consider the following optimization problem to be solved with FOQUS using PYOMO.

min y

Subject to:
.. math::
y=x_1+x_2
.. math::
ax_1 + bx_2 \geq c

The complete FOQUS file (**Pyomo_Test_Example.foqus**), with the code written,
is located in: **examples/tutorial_files/PYOMO**

Instructions
~~~~~~~~~~~~

1. Open FOQUS, and under the Flowsheet Tab, create a Node.

2. Open the Node Editor, and let the Model Type be “None”.

3. Add the model parameters a, b, c as “Input Variables” within the Node Editor, with values 1, 2, 3 respectively.

4. Add x1, x2, & y as “Output Variables” within the Node Editor (They are meant to correspond to the decision variable values of the optimization model).

5. Under Node Script, set Script Mode to “Post”. This will ensure that the node script runs after the node simulation.
   Enter the following PYOMO code for the optimization model:
   code:: python

  * ``1. from pyomo.environ import (Var,Constraint,ConcreteModel,value,Param)``
  * ``2. from pyomo.opt import SolverFactory``
  * ``3. import pyutilib.subprocess.GlobalData ``
  * ``4. pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False ``
  * ``5. m=ConcreteModel() ``
  * ``6. m.x1=Var(within=PositiveReals) ``
  * ``7. m.x2=Var(within=PositiveReals) ``
  * ``8. m.y=Var() ``
  * ``9. m.c1=Constraint(expr=x["a"]*m.x1+x["b"]*m.x2>=x["c"]) ``
  * ``10.m.c2=Constraint(expr=m.x1+m.x2==m.y) ``
  * ``11.m.o=Objective(expr=m.y)``
  * ``12.opt = SolverFactory("ipopt") ``
  * ``13.opt.solve(m) ``
  * ``14.f["x1"]=m.x1.value ``
  * ``15.f["x2"]=m.x2.value ``
  * ``16.f["y"]=m.y.value ``

In the above code, lines (1), (2) are used to import the PYOMO package and SolverFactory function to develop the model and solve it by accessing an appropriate solver.

A PYOMO Concrete Model is declared, defining the variables, declaring the constraints using the parameters defined within “Input Variables” of the Node, and defining the objective function. (Lines (5) to (11)).

Lines (12) & (13) are used to access the solver, and solve the model via ipopt solver.

Note: ipopt can be installed using : conda install -c conda-forge ipopt or pip install ipopt

Once the model is solved, the values of decision variables "x1", "x2", "y" are assigned to the Node Output Variables in lines (14) to (16).

6. Click the Run button, Run the Flowsheet and check the decision variable values at optimum in the Node Output Variables.

It is to be noted that the parameter values within Node Input Variables can be changed as per user’s requirement, to run different cases.

Note: For more information on building and solving pyomo models, refer to the pyomo documentation:
https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html 
