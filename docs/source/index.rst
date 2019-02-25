Contents
========

.. toctree::
    :maxdepth: 1

    chapt_intro/index
    chapt_flowsheet/index
    chapt_opt/index
    chapt_uq/index
    chapt_ouu/index
    chapt_surrogates/index
    chapt_sdoe/index
    chapt_solventfit/index
    chapt_sinter/index
    chapt_heat/index
    chapt_debug/index
    references

FOQUS
=====

Overview
--------

The Framework for Optimization, Quantification of Uncertainty, and Surrogates (FOQUS) serves as the primary computational platform enabling advanced Process Systems Engineering (PSE) capabilities to be integrated with commercial process simulation software. It can be used to synthesize, design, and optimize a complete carbon capture system while considering uncertainty. FOQUS enables users to effectively screen potential capture concepts in the context of a complete industrial process so that trade-offs can be appropriately evaluated. The technical and economic performance characteristics of the capture process are highly dependent on employing an effective approach for process synthesis. Since large-scale carbon capture processes are outside of current experience, heuristic and evolutionary approaches are likely to be inadequate. Thus, a key aspect of FOQUS is that it bridges this gap by supporting a superstructure-based approach to determine the optimal process configuration and equipment interconnections.

Modules
-------

1. SimSinter provides a wrapper to enable models created in process simulators to be linked into a FOQUS Flowsheet.
2. The FOQUS Flowsheet is used to link simulations together and connect model variables between simulations on the flowsheet. FOQUS enables linking models from different simulation packages.
3. Simulations are run through Turbine, which manages the multiple runs needed to build surrogate models, perform derivative-free optimization or conduct an Uncertainty Quantification (UQ) analysis. Turbine provides the capability for job queuing and enables these jobs to be run in parallel using cloud- or cluster-based computing platforms or a single workstation.
4. The Surrogates module can create algebraic surrogate models to support large-scale deterministic optimization, including superstructure optimization to determine process configurations. One of the available surrogate models is the Automated Learning of Algebraic Models for Optimization (ALAMO). ALAMO is an external product due to background Intellectual Property (IP) issues.
5. The Derivative-Free Optimization (DFO) module enables derivative-free (or simulation-based) optimization directly on the process models linked together on a FOQUS Flowsheet. It utilizes Excel to calculate complex objective functions, such as the cost of electricity.
6. The UQ module enables the effects of uncertainty to be propagated through the complete system model, sensitivity of the model to be assessed, and the most significant sources of uncertainty identified to enable prioritizing of experimental resources to obtain additional data.
7. The Optimization Under Uncertainty (OUU) module combines the capabilities of the DFO and the UQ modules to enable scenario-based optimization, such as optimization over a range of operating scenarios.
8. The SolventFit module is an uncertainty quantification tool for the calibration of an Aspen Plus® solvent process model. The current state of the art is a regression that yields single best fit point estimates of some parameters. This shows neither the level of uncertainty in each parameter, nor the level of uncertainty in model output, such as equivalent work. SolventFit allows for predictions with uncertainty bounds by accounting for uncertainty in model parameters and deficiencies in the model form. This yields an improved understanding of the model parameters and results in more complete predictions with uncertainty bounds. This distribution of parameters allows for predictions with uncertainty.
9. The Sequential Design of Experiments (SDOE) module currently provides a way to construct flexible space-filling designs based on a user-provided candidate set of input points. The method allows for new designs to be constructed as well as augmenting existing data to strategically select input combintions that minimizes the distance between points. Development of this module is continuing and will soon include other options for design construction.
