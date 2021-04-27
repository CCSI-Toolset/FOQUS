function outputs = CSTR_Steady_State(inputs)
    % This function simulates a Steady State Non-Adiabatic CSTR Reactor based on:
    % Jiri Vojtesek and Petr Dostal. A New Equilibrium Shortcut Temperature 
    % Swing Adsorption Model for Fast Adsorbent Screening. 
    % International Journal of Mathematics and Computers in Simulation 2011 6(5), 528-535
    
    % Initial guess for unknowns
    %    [q, k1, T, CA, qc, a1]
    % x0 = [1,10^10,300,0.5,1,0.01];
    x0 = [inputs(8),1e10,inputs(12),inputs(1),1,inputs(8)/inputs(14)];
    
    % Call and solve the CSTR function 
    fun = @(x) cstr_ss(x, inputs);
    % options = optimoptions('fsolve','Algorithm','trust-region', 'Display','off');
    options = optimoptions('fsolve', 'Display','off');
    x = fsolve(fun,x0,options) ;
	
    % Retrieve outputs
    q = x(1); % Volumetric flow rate of reactant [l/min]
    k1 = x(2); % Reaction rate [1/min]
    T = x(3); % Product's temperature [K]
    CA = x(4); % Final concentration of reactant A [mol/l]
    qc = x(5); % Volumetric flow rate of cooling [l/min]
    a1 = x(6); % Constant 1 [1/min]
    XA = (inputs(1)-CA)/inputs(1); % Conversion of reactant A [-]
    
    outputs = [a1, CA, k1, q, qc, T, XA] ;
    
    % Function definition
    function F = cstr_ss(vars, inputs)
        % Input Parameters
        CA0 = inputs(1); % Feed concentration [mol/l]
        cp = inputs(2); % Specific heat of the reactant [cal/g/K]
        cpc = inputs(3); % Specific heat of the cooling [cal/g/K]
        delH_neg = inputs(4); % Reaction heat [cal/mol]
        E_R = inputs(5); % Activation energy to R [K]
        ha = inputs(6); % Heat transfer coefficient [cal/min/K]
        k0 = inputs(7); % Reaction rate constant [1/min]
        q0 = inputs(8); % Volumetric flow rate of reactant [l/min]
        qc0 = inputs(9); % Volumetric flow rate of cooling [l/min]
        rho = inputs(10); % Density of the reactant [g/l]
        rho_c = inputs(11); % Density of the cooling [g/l]
        T0 = inputs(12); % Reactant’s feed temperature [K]
        TC0 = inputs(13); % Inlet coolant temperature [K]
        V = inputs(14); % Reactor’s volume [l]
        % Constants
        a3 = rho_c*cpc/(rho*cp*V);
        a2 = delH_neg/(rho*cp);
        a4 = -ha/(rho_c*cpc);
        % System of Nonlinear Equations
        F(1) = vars(1) - q0;
        F(2) = vars(5) - qc0;
        F(3) = vars(6) - vars(1)/V;
        F(4) = vars(2) - k0*exp(-E_R/vars(3));
        F(5) = (vars(1)/V)*(CA0-vars(4)) - vars(2)*vars(4);
        F(6) = (vars(1)/V)*(T0 - vars(3)) + a2*(vars(2)*vars(4)) + a3*vars(5)*(1 - exp(a4/vars(5)))*(TC0 - vars(3));
    end
end