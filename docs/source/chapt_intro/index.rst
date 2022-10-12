Introduction
============

The Framework for Optimization, Quantification of Uncertainty, and Surrogates (FOQUS) software provides a graphical interface and standard platform for several Carbon Capture Simulation Initiative (CCSI) tools. The primary feature of FOQUS is its ability to interact with commonly-used chemical engineering process modeling software. Models constructed using a variety of software can be combined into a larger composite model. The CCSI tool SimSinter provides connectivity to external process simulation software. SimSinter also provides a standard library to enable interfacing with other software. The CCSI FOQUS Cloud on Amazon Web Services (AWS) is fully compatible with the FOQUS UI, and can be used to submit flowsheets with Aspen ACM/AspenPlus simulations to be run remotely and in large batch submissions to take advantage of high parallelism enabled through cloud architecture including on-demand Cloud resource scaling.

In FOQUS, simulations can be connected in a meta-flowsheet, which enables parts of a process to be modeled using the most appropriate software and combines them into a single large model, possibly including recycle streams. For example, in studying a carbon capture system for a coal-fired power plant: a power plant may be modeled in Thermoflex; a solvent-based carbon capture system may be modeled in Aspen Plus; and a compression system may be modeled in gPROMS. To optimize the entire system, these models can be combined into a single large model. The resulting meta-flowsheet can be used for simulation-based optimization, uncertainty quantification (UQ), or generation of surrogate models.

This section provides brief overview and motivating examples, for different uses of FOQUS.

Simulation Based Optimization
-----------------------------

Simulation-based optimization considers a process simulation to be a black box model, which is a model where the mathematical details are not known. In this case, models are evaluated using process simulation software; multiple models can be combined to form larger models. Due to the long run times and the limitations of the methods used, a limited set of optimization variables (usually less than 30) is considered. Simulation-based optimization has some advantages and disadvantages, compared to equation-based optimization methods. With simulation-based optimization, there is no need to provide simplified algebraic models, problem formulation is relatively simple, and a good solution can usually be obtained; however, a provably-global optimum cannot be found and it is impractical to deal with very large numbers of variables. Large numbers of variables may be found in superstructure and heat integration problems where the structure of a process is being optimized. Both simulation and equation-based optimization methods are used in CCSI.

Capture of CO\ :sub:`2` from a pulverized coal-fired power plant involves several very different systems including: a boiler, steam cycle, flue gas desulfurization, carbon capture, and CO\ :sub:`2` compression. It is convenient to separate many of these processes into smaller, more reliable simulations. The different processes may also be better simulated in different software packages.  Although some process simulation software contains optimization features, there are several reasons these may not be practical for a large composite system. It may be hard to develop a large model of the entire system that reliably converges. Many optimization methods have a difficult time dealing with simulation errors, and many black box derivative free optimization solvers are better able to handle occasional simulation failures. It may not be practical to simulate the entire process accurately using a single tool. Derivatives are also difficult to estimate for many systems when models do not provide exact derivatives, making derivative-free methods a good option.

The motivating example used to demonstrate the optimization framework is fairly simple. The system consists of a series of bubbling fluidized bed (BFB) CO\ :sub:`2` adsorbers and regenerators modeled in Aspen Custom Modeler (ACM). The details of the BFB system are described in the CCSI BFB model documentation. A cost analysis for a 650 MW power plant and capture system is presented in an Excel spreadsheet. The simulation and spreadsheet files are provided in the examples directory in the FOQUS installation directory (see the tutorial in Section \ref{tutorial.sim.flowsheet} for more information). The spreadsheet contains capital cost as well as operating and maintenance cost estimates, which are used to estimate the cost of electricity.

In this example, the objective function is the cost of electricity; the decision variables are design and operating variables in the ACM model. The cost of electricity is minimized while maintaining a 90 CO\ :sub:`2` percent capture rate. The BFB system model and the cost of electricity are contained in separate models connected in a FOQUS flowsheet, which enables the cost of electricity to be calculated in Excel, using data acquired from the ACM model. See Sections \ref{tutorial.sim.flowsheet} and \ref{sec.opt.tutorial} for more information about the optimization problem.

Uncertainty Quantification
--------------------------


The Uncertainty Quantification (UQ) module of FOQUS encompasses a rich selection of mathematical, statistical, and diagnostic tools for application users to perform UQ studies on their simulation models. The PSUADE tool provides most of the UQ functionality available in FOQUS :ref:`(Tong 2011)<Tong_2011>`. The recommended systematic multi-step approach consists of the following steps:

1. Define the objectives of the analysis (e.g., identify the most important sources of uncertainties).
2. Specify a simulation model to be studied. Acquire the model input files and the executable that runs the simulation (i.e., an executable that uses the specified inputs and generates model outputs). Identify the outputs of interest, identify all relevant sources of uncertainties, and ensure that they can be used as input variables to the simulation model.
3. Select some or all input parameters that have uncertainty attributed. Characterize the prior probability distribution of these selected parameters by specifying the upper/lower bounds. For non-uniform prior distributions (e.g., Gaussian), additional information (e.g., mean and standard deviation) is required to define the shape of the prior distribution. This prior distribution represents the user's best initial guess about the selected parameters' uncertainties.
4. Identify, if available, relevant data from physical experiments that can be used for model parameter calibration. Model calibration is a process that applies the observational data to update the prior distribution. The model calibration correlates the observational data to predict a distribution as a result.
5. Select a sample scheme and sample size. From this information, a set of input values are sampled from the prior distribution. The choice of sampling scheme (which affects how the samples populate the input space) depends on the UQ objective(s) specified in the first step.
6. "Run" the input samples. Running the input samples is the process where each sampled input value is fed to the simulation executable (specified in Step 2) and the corresponding output value is returned.
7. Analyze the results and make decisions on how to proceed.

Steps 1-4 are often done through expert knowledge elicitation and/or literature search. Steps 5-7 can be achieved through software provided in the FOQUS UQ module.

The FOQUS UQ module provides a number of sampling and analysis methods, including:

* Parameter screening methods: computes the importance of input parameters to identify which are important (to be kept in subsequent analyses) and which to ignore (to be weeded out).
* Response surface (used interchangeably with 'surrogate') construction: approximates the relationship between the input samples and their outputs via a smooth mathematical function. This response surface or surrogate can then be used in place of the actual simulation model to speed up lengthy simulations.
* Response surface validation methods: evaluates how well a given response surface fits the data. This is important for choosing different response surfaces.
* Basic uncertainty analysis: propagates input uncertainty to output uncertainty.
* Sensitivity analysis methods: quantifies how much varying an input value can impact the resulting output value.
* Bayesian calibration: applies observational data to refine the estimate of input uncertainties.
* Visualization tools: views computed distributions and response surfaces.
* Diagnostics tools (mainly in the form of scatter plots): checks samples and model behaviors (e.g., outliers).

The adsorber 650.1 subsystem process model is used to demonstrate the UQ framework. The A650.1 process model was developed and is continuously refined by our Process Synthesis and Design Team. The model is based on their design and optimization of an initial full-scale design of a solid sorbent capture system for a net 650 MW (before capture) supercritical pulverized coal power plant. The A650.1 model describes a solid sorbent-based carbon capture system that uses the NETL-32D sorbent. NETL-32D is a mixture of polyethyleneamine (PEI) and aminosilanes impregnated into the mesoporous structure of a silica substrate. CO\ :sub:`2` removal is achieved through chemical reactions between the amine sites within the sorbent. The A650.1 model is implemented in Aspen Custom Modeler (ACM) and contains many components (e.g., adsorbers, regenerators, compressors, heat exchangers). For the UQ analyses, this manual focuses on the adsorber units, which are responsible for the adsorption of CO\ :sub:`2` from the input flue gas.

In its original form, the A650.1 model consists of a deterministic simulation model, which means to consider all the parameters (e.g. chemical reaction parameters, heat and mass transfer coefficients) to have a fixed value (most likely fixed to a mean value, lower or upper bound for robustness). With the FOQUS UQ module, the model uncertainties can be addressed. Thus, UQ analysis of the A650.1 model would help to develop a robust design by addressing the following questions:
* How accurately does each subsystem model predict actual system performance (under uncertain operating conditions)?
* Which input parameters should be examined to improve prediction accuracy?
* What is each input parameters' contribution to prediction uncertainty?

Optimization Under Uncertainty
------------------------------

The Optimization Under Uncertainty (OUU) module in FOQUS is an extension of simulation-based optimization by including the contribution of model parameter uncertainties in the objective function. OUU is useful when inclusion of uncertainties may significantly alter the optimal design configurations. A straightforward approach to include the effect of uncertainty is to replace the objective function with its statistical mean on an ensemble drawn from the probability distributions of the continuous uncertain parameters (other options are available in FOQUS). Alternatively, users can provide a set of 'scenarios', where each scenario is associated with a probability. The latter case is often called 'scenario optimization.' The FOQUS OUU accommodates both continuous and scenario-based uncertain parameters. OUU makes use of the flowsheet for evaluations of the objective function. Naturally, OUU requires more computational resources than deterministic optimization. However, the ensemble runs can be launched in parallel so ideally, the turnaround time remains about the same as that of deterministic optimization if high performance computing capability (such as the CCSI FOQUS Cloud) is used in conjunction with FOQUS.

Surrogate Models
----------------

Process simulations are often time consuming and occasionally fail to converge. For mathematical optimization, it is sometimes necessary to replace a simulation with a surrogate model, which is a simplified model that executes much faster. FOQUS contains tools for creating and quantifying the uncertainty associated with surrogate models.

ALAMO
~~~~~

While simulation based optimization can often do a good job of providing optimal design and operating conditions for a predetermined flowsheet, it cannot provide an optimal flowsheet.  To obtain a more optimal flowsheet, a mixed integer nonlinear program must be solved. These types of problems cannot generally be solved using simulation based optimization. A solution is to generate relatively simple algebraic models that accurately represent the high fidelity models. FOQUS currently provides an interface for ALAMO :ref:`(Cozad et al. 2014)<Cozad_2014>`, which builds surrogate model that are well suited for superstructure optimization.

ACOSSO
~~~~~~

The Adaptive Component Selection and Shrinkage Operator (ACOSSO) surface approximation was developed under the Smoothing Spline Analysis of Variance (SS-ANOVA) modeling framework :ref:`(Storlie et al. 2011)<Storlie_2011>`. As it is a smoothing type method, ACOSSO works best when the underlying function is somewhat smooth. For functions which are known to have sharp changes or peaks, etc., other methods may be more appropriate. Since it implicitly performs variable selection, ACOSSO can also work well when there are a large number of input variables. To facilitate the description of ACOSSO, the univariate smoothing spline is reviewed first. The ACOSSO procedure also allows for categorical inputs :ref:`(Storlie et al. 2013) <Storlie_2013>`.

BSS-ANOVA
~~~~~~~~~

The Bayesian Smoothing Spline ANOVA (BSS-ANOVA) is essentially a Bayesian version of ACOSSO :ref:`(Reich 2009)<Reich_2009>`. It is Gaussian Process (GP) model with a non-conventional covariance function that borrows its form from SS-ANOVA. It tackles the high dimensionality (of inputs) on two fronts: (1) variable selection to eliminate uninformative variables from the model and (2) restricting the level of interactions involved among the variables in the model. This is done through a fully Bayesian approach which can also allow for categorical input variables with relative ease. Since it is closely related to ACOSSO, it generally works well in similar settings as ACOSSO. The BSS-ANOVA procedure also allows for categorical inputs :ref:`(Storlie et al. 2013) <Storlie_2013>`.
