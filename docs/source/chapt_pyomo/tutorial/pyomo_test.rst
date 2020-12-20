.. _tutorial.pyomo.test:

Tutorial: Running PYOMO Optimization Model in FOQUS
===================================================

Consider the following optimization problem to be solved with FOQUS using PYOMO.

min y

Subject to:

.. math::
   y = x_1 + x_2

   ax_1 + bx_2 \geq c

The complete FOQUS file (**Pyomo_Test_Example.foqus**), with the code written,
is located in: **examples/tutorial_files/PYOMO**

.. note:: |examples_reminder_text|

Instructions
~~~~~~~~~~~~

1. Open FOQUS, and under the Flowsheet Tab, create a Node.

2. Open the Node Editor, and let the Model Type be “None”.

3. Add the model parameters ``a``, ``b``, ``c`` as “Input Variables” within the Node Editor, with values ``1``, ``2``, ``3`` respectively.

4. Add ``x1``, ``x2``, ``y``, ``converged``, and ``optimal`` as “Output Variables” within the Node Editor.

   Note that ``x1``, ``x2`` and ``y`` correspond to the optimization variable values.

   ``converged`` is meant to be a binary variable that would denote whether the optimization model has converged, by checking the solver status.

   ``optimal`` is meant to be a binary variable that would denote whether the solver returns an optimal solution.

5. Under Node Script, set Script Mode to “Post”. This will ensure that the node script runs after the node simulation.
   Enter the following PYOMO code for the optimization model:

   .. code-block:: python
      :linenos:

      from pyomo.environ import (Var,
                                 Constraint,
                                 ConcreteModel,
                                 PositiveReals,
                                 Objective)
      from pyomo.opt import SolverFactory
      import pyutilib.subprocess.GlobalData

      pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
      m = ConcreteModel()
      m.x1 = Var(within=PositiveReals)
      m.x2 = Var(within=PositiveReals)
      m.y = Var()
      m.c1 = Constraint(expr=x["a"]*m.x1+x["b"]*m.x2 >= x["c"])
      m.c2 = Constraint(expr=m.x1+m.x2 == m.y)
      m.o = Objective(expr=m.y)
      opt = SolverFactory("ipopt")
      r = opt.solve(m)
      f["x1"] = m.x1.value
      f["x2"] = m.x2.value
      f["y"] = m.y.value
      f["converged"] = (str(r.solver.status) == "ok")
      f["optimal"] = (str(r.solver.termination_condition) == "optimal")

   In the above code, lines 1-6 are used to import the PYOMO package and SolverFactory function to develop the model and solve it by accessing an appropriate solver.

   A PYOMO Concrete Model is declared, defining the variables, declaring the constraints using the parameters defined within “Input Variables” of the Node, and defining the objective function with
   lines 10 to 16.

   Line 17 sets the solver to ipopt and line 18 sends the problem to be solved to the solver. Ipopt is a nonlinear optimization solver.

   .. note::
      ipopt will need to be available in your environment.  To install it into your conda environment you should use the command: ``conda install -c conda-forge ipopt``
      The conda install method is preferred for Windows users.


   Once the model is solved, the values of decision variables ``x1``, ``x2``, ``y`` are assigned to the Node Output Variables in lines 19 to 21.

   The code lines 22 and 23 check the solver status and termination condition. If the solver status is "ok", it means that the model has converged, and the 'converged' variable is assigned
   the value 1. Else, it is assigned the value 0, which means that the model has not converged.
   If the solver termination condition is "optimal", it means that the solver has found an optimal solution for the optimization model. Else, the solution is either feasible if the solver status is "ok",
   or infeasible altogether.

6. Click the Run button to run the python script and check the Node Output Variables section.

It should be noted that the parameter values within Node Input Variables can be changed as per user’s requirement, to run different cases.

.. note::
   For more information on building and solving pyomo models, refer to the pyomo documentation:
   https://pyomo.readthedocs.io/en/stable/solving_pyomo_models.html
