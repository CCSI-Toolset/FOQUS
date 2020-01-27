.. _tutorial.pyomo.test:

Tutorial: Running PYOMO Optimization Model in FOQUS
===================================================

Consider the following optimization problem to be solved with FOQUS using PYOMO.

min y

Subject to:

y = x1  + x2

a * x1 + b * x2 ≥ c.

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

  * ``from pyomo.environ import (Var,Constraint,ConcreteModel,value,Param) (1)``
  * ``from pyomo.opt import SolverFactory (2)``
  * ``import pyutilib.subprocess.GlobalData (3)``
  * ``pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False (4)``
  * ``m=ConcreteModel() (5)``
  * ``m.x1=Var(within=PositiveReals) (6)``
  * ``m.x2=Var(within=PositiveReals) (7)``
  * ``m.y=Var() (8)``
  * ``m.c1=Constraint(expr=x["a"]*m.x1+x["b"]*m.x2>=x["c"]) (9)``
  * ``m.c2=Constraint(expr=m.x1+m.x2==m.y) (10)``
  * ``m.o=Objective(expr=m.y) (11)``
  * ``opt = SolverFactory("ipopt") (12)``
  * ``opt.solve(m) (13)``
  * ``f["x1"]=m.x1.value (14)``
  * ``f["x2"]=m.x2.value (15)``
  * ``f["y"]=m.y.value (16)``

In the above code, lines (1), (2) are used to import the PYOMO package and SolverFactory function to develop the model and solve it by accessing an appropriate solver.

The solvers can be accessed in 2 ways:
(i) Directly through PYOMO : directly accessing the solvers through Pyomo, like glpk, cplex, baron, etc.

Eg: Opt = SolverFactory(“glpk”).

(ii) PYOMO GAMS Interface: In case some of the licensed solvers like BARON or CPLEX are not directly available to users, they can be accessed in PYOMO through GAMS.

More information on the syntax can be found in the following link: https://pyomo.readthedocs.io/en/latest/library_reference/solvers/gams.html.

In order to allow a subprocess to be created for solving the model on another thread apart from the main one, lines (3) & (4) are used to set the default signal handler within pyutilib package of PYOMO to “false” (ie: removing it).

This is followed by declaring a PYOMO Concrete Model, defining the variables, declaring the constraints using the parameters defined within “Input Variables” of the Node, and defining the objective function. (Lines (5) to (11)).

Lines (12) & (13) are used to access the solver, and solve the model via ipopt solver.

Note: ipopt can be installed using : conda install -c conda-forge ipopt or pip install ipopt

Once the model is solved, the values of decision variables "x1", "x2", "y" are assigned to the Node Output Variables in lines (14) to (16).

6. Click the Run button, Run the Flowsheet and check the decision variable values at optimum in the Node Output Variables.

It is to be noted that the parameter values within Node Input Variables can be changed as per user’s requirement, to run different cases.
