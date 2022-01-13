ODoE Overview
==============
The FOQUS ODoE module supports several variants of optimal experimental
design. This chapter presents an overview of these variants.
Subsequently, details of the ODoE graphical user
interface will be discussed in the :ref:`odoe_tutorials` section.

.. note::
   To run this version of ODoE, make sure you have the latest version of PSUADE installed (1.9.0).

ODoE Variables
--------------
Suppose a simulation model is available for this study. Let this
simulation model be represented by the following function:

.. math:: Y = F(X,U)

which is characterized by two types of variables:

#. **Design/Decision variables**

   -  Notation: :math:`X` with dimension :math:`n_x`

   -  Definition: Design variables are continuous variables that are
      bounded in some specific ranges. A requirement is that the
      simulation output should be a smooth function of these design
      variables.

#. **Continuous uncertain variables**

   -  Notation: :math:`U` with dimension :math:`n_u`

   -  Definition: Continuous uncertain variables are associated with a
      joint probability distribution function from which a sample can be
      drawn to compute the basic statistics.

ODoE Objective Functions
------------------------
There are a few variants of the objective functions. They can be
divided into two classes: those that optimize certain metrics associated
with the posterior distributions of the uncertain variables (D-, A-, and
E-optimality), and those that optimize certain metrics associated with
the prediction uncertainties (G- and I-optimality).

#. D-optimality: D-optimal methods seek to find an optimal subset of
   points in the candidate set (provided by users) that minimizes the
   product of eigenvalues (or determinant) of the covariance matrix
   constructed from the posterior distributions of the uncertain variables.

#. A-optimality: A-optimal methods seek to find an optimal subset of
   points in the candidate set (provided by users) that minimizes the
   sum of eigenvalues of the covariance matrix constructed from the
   posterior distributions of the uncertain variables.

#. E-optimality: E-optimal methods seek to find an optimal subset of
   points in the candidate set (provided by users) that minimizes the
   maximum eigenvalue of the covariance matrix constructed from the
   posterior distributions of the uncertain variables.

#. G-optimality: G-optimal methods seek to find an optimal subset of
   points in the candidate set (provided by users) that minimizes the
   maximum prediction uncertainty (induced by the posterior distributions
   of the uncertain variables) among an evaluation set.

#. I-optimality: I-optimal methods seek to find an optimal subset of
   points in the candidate set (provided by users) that minimizes the
   mean prediction uncertainty (induced by the posterior distributions
   of the uncertain variables) among an evaluation set.

These methods can be computationally intensive when the candidate set
is large and/or the sought-after optimal subset is large. FOQUS uses
some global optimization algorithm in this context. Since there may
exist many local minima, most of the time it may only be possible to
find a sub-optimal subset given limited computational time (that is,
exhaustive search may be computationally prohibitive).
