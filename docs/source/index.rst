Contents
========

.. toctree::
    :maxdepth: 1

    chapt_install/index
    chapt_intro/index
    chapt_flowsheet/index
    chapt_opt/index
    chapt_uq/index
    chapt_ouu/index
    chapt_surrogates/index
    chapt_sdoe/index
    chapt_odoe/index
    chapt_HI/index
    chapt_pyomo/index
    chapt_idaes/index
    chapt_matlab/index
    chapt_sinter/index
    chapt_sm_optimizer/index
    chapt_debug/index
    chapt_dev/index
    chapt_vector_support/index
    references
    contact
    copyright

FOQUS
=====

Overview
--------

The Framework for Optimization, Quantification of Uncertainty, and Surrogates (FOQUS) serves as the
primary computational platform enabling advanced Process Systems Engineering (PSE) capabilities to
be integrated with commercial process simulation software. It can be used to synthesize, design, and
optimize a complete carbon capture system while considering uncertainty. FOQUS enables users to
effectively screen potential capture concepts in the context of a complete industrial process so
that trade-offs can be appropriately evaluated. The technical and economic performance
characteristics of the capture process are highly dependent on employing an effective approach for
process synthesis. Since large-scale carbon capture processes are outside of current experience,
heuristic and evolutionary approaches are likely to be inadequate. Thus, a key aspect of FOQUS is
that it bridges this gap by supporting a superstructure-based approach to determine the optimal
process configuration and equipment interconnections.

Modules
-------

1. SimSinter provides a wrapper to enable models created in process simulators to be linked into a
   FOQUS Flowsheet.

2. The FOQUS Flowsheet is used to link simulations together and connect model variables between
   simulations on the flowsheet. FOQUS enables linking models from different simulation packages.
   
3. Simulations are run through Turbine, which manages the multiple runs needed to build surrogate
   models, perform derivative-free optimization or conduct an Uncertainty Quantification (UQ)
   analysis. Turbine provides the capability for job queuing and enables these jobs to be run in
   parallel using cloud- or cluster-based computing platforms or a single workstation.
   
4. The Surrogates module can create algebraic surrogate models to support large-scale deterministic
   optimization, including superstructure optimization to determine process configurations. One of
   the available surrogate models is the Automated Learning of Algebraic Models for Optimization
   (ALAMO). ALAMO is an external product due to background Intellectual Property (IP) issues.
   
5. The Derivative-Free Optimization (DFO) module enables derivative-free (or simulation-based)
   optimization directly on the process models linked together on a FOQUS Flowsheet. It utilizes
   Excel to calculate complex objective functions, such as the cost of electricity.
   
6. The UQ module enables the effects of uncertainty to be propagated through the complete system
   model, sensitivity of the model to be assessed, and the most significant sources of uncertainty
   identified to enable prioritizing of experimental resources to obtain additional data.
   
7. The Optimization Under Uncertainty (OUU) module combines the capabilities of the DFO and the UQ
   modules to enable scenario-based optimization, such as optimization over a range of operating
   scenarios.
   
8. The Sequential Design of Experiments (SDOE) module currently provides a way to construct flexible
   space-filling designs based on a user-provided candidate set of input points. The method allows
   for new designs to be constructed as well as augmenting existing data to strategically select
   input combintions that minimizes the distance between points. Development of this module is
   continuing and will soon include other options for design construction.

Application Based Examples
--------------------------

FOQUS has been used to solve problems based on comprehensive analysis and optimization of carbon
capture systems. Some relevant research work that includes FOQUS can be found in the following
publications:

Chen, Y., Eslick, J.C., Grossmann, I.E., Miller, D.C., 2015. Simultaneous process optimization and
heat integration based on rigorous process simulations. Computers and Chemical Engineering 81,
180–199.

Gao, Q., Miller, D.C., 2015. Optimization of amine-based solid sorbent chemistry for post-combustion
carbon capture. Paper presented at: 2015 International Pittsburgh Coal Conference; 5–8 October 2015;
Pittsburgh, PA, USA.

Ma, J., Mahapatra, P., Zitney, S.E., Biegler, L.T., Miller, D.C., 2016. D-RM Builder: A software
tool for generating fast and accurate nonlinear dynamic reduced models from high-fidelity
models. Computers and Chemical Engineering 94, 60–74.

Miller, D.C., Agarwal, D., Bhattacharyya, D., Boverhof, J., Chen, Y., Eslick, J., Leek, J., Ma, J.,
Mahapatra, P., Ng, B., Sahinidis, N.V., Tong, C., Zitney, S.E., 2017. Innovative computational tools
and models for the design, optimization and control of carbon capture processes, in: Papadopoulos,
A.I., Seferlis, P. (Eds.), Process Systems and Materials for CO2 Capture: Modelling, Design, Control
and Integration. John Wiley & Sons Ltd, Chichester, UK, pp. 311–342.

Soepyan, F.B., Anderson-Cook, C.M., Morgan, J.C., Tong, C.H., Bhattacharyya, D., Omell, B.P.,
Matuszewski, M.S., Bhat, K.S., Zamarripa, M.A., Eslick, J.C., Kress, J.D., Gattiker, J.R., Russell,
C.S., Ng, B., Ou, J.C., Miller, D.C., 2018. Sequential Design of Experiments to Maximize Learning
from Carbon Capture Pilot Plant Testing. In: Eden, M.R., Ierapetritou, M.G., Towler, G.P. (Editors),
13th International Symposium on Process Systems Engineering (PSE 2018). Elsevier, Amsterdam,
pp. 283-288.

Additional research work can be found on https://www.acceleratecarboncapture.org/publications 

.. include:: contact.rst
