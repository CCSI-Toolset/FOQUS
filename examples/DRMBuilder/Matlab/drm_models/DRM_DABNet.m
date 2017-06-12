classdef DRM_DABNet < handle
% Class definition for DABNet based dynamic reduced models
%
% Written and developed by:
% Priyadarshi Mahapatra, URS Corporation / National Energy Technology Laboratory
% Jinliang Ma, URS Corporation / National Energy Technology Laboratory
%
% For details of D-RM Builer application and D-RMs, refer to CCSI's D-RM Builer user's manual
% 
% For detailed description of the mathematical formulation and concepts, please refer to:
% G.B. Sentoni and L.T. Biegler, State-Space Nonlinear Process Modeling: Identification and Universality, AIChE Journal, Vol. 44, No. 10, October 1998
%
% Last Modified: July, 2014.  The current version can be used by unscented Kalman filter

    properties
        dt;             % sampling time interval
        u_name;         % names of all input variables including those not varied, cell array of strings
        y_name;         % names of all output variables including those not varied, cell array of strings
        u_idx;          % indices of varied inputs, integer array
        y_idx;          % indices of varied outputs, integer array
        nu;             % number of input variables
        ny;             % number of output variables
        nx_ann;         % vector of number of states for each output [ny]
        u_mean;         % vector of means of input variables, size [nu]
        y_mean;         % vector of means of output varaibles, size [ny]
        u_sigma;        % vector of standard deviations of input variables, size [nu]
        y_sigma;        % vector of standard deviations of output varaibles, size [ny]
        A;              % 2-D cell array of A matrices, size {ny,nu}
        B;              % 2-D cell array of B vectors, size {ny,nu}
        ANN;            % 1-D array of artifitial neural networks, size [ny]
        x;              % 2-D cell array of decoupled state-space vector, size {ny,nu}
        x_ann;          % 1-D cell array of neural network input vector, size {ny}
        y;              % output vector, size [ny]
        dxann_ddu;      % array of ny cells, containing dxann/du information for each output
        fJacobianPopulated = 0;
    end

    methods
            %function obj = DRM_DABNet(dt,input_names,output_names,input_indices,output_indices,nu,ny,u_mean,y_mean,u_sigma,y_sigma,A,B,NN)
        function obj = DRM_DABNet(Ts,A,B,NN,u_mean,y_mean,u_sigma,y_sigma,varargin)
            % constructor, parameters of the function are assigned by a MATLAB script exported by D-RM Builder
            obj.dt = Ts; obj.A = A; obj.B = B;
            obj.nu = size(obj.A,2); obj.ny = size(obj.A,1);
            obj.ANN = DRM_ANN.empty(obj.ny,0);
            for i=1:obj.ny
                obj.ANN(i) = DRM_ANN(NN(i));
            end
            obj.u_mean = u_mean'; obj.y_mean = y_mean';
            obj.u_sigma = u_sigma'; obj.y_sigma = y_sigma';
            obj.x = cell(obj.ny,obj.nu); 
            obj.y = zeros(obj.ny,1);
            %calculate size of ANN input vector for each output variable
            obj.nx_ann = zeros(obj.ny,1);
            for i = 1:obj.ny
                for j = 1:obj.nu
                    obj.nx_ann(i) = obj.nx_ann(i) + length(obj.A{i,j});
                end
                obj.x_ann{i} = zeros(obj.nx_ann(i),1);
            end

            if nargin >= 10 % DRM_DABNet(...,um_idx,ym_idx)
                obj.u_idx = varargin{1}; obj.y_idx = varargin{2};
                if nargin >= 12 % DRM_DABNet(...,um_idx,ym_idx,u_name,y_name) 
                    obj.u_name = varargin{3}; obj.y_name = varargin{4};
                end
            end
        end

        function initialize(obj,u0_ss)
        % initialize the state and output variables based on input variables assuming steady-state condition
        % u0_ss is the initial steady-state input vector
            u_scaled = (u0_ss - obj.u_mean)./obj.u_sigma; % scale steady-state input vector
            for i = 1:obj.ny
                for j = 1:obj.nu
                    nele = length(obj.A{i,j});
                    % steady-state solution: x = Ax + Bu or x = inv(I-A)Bu
                    obj.x{i,j} = (eye(nele)-obj.A{i,j})\obj.B{i,j}*u_scaled(j);
                end
                % populate ANN state variables based on decoupled state variables
                obj.populateAnnStatesFromDecoupledStates(i);
                [ym_scaled] = obj.predictSingleOutput(i); % Nonlinear mapping of states to outputs through neural-network
                obj.y(i) = ym_scaled*obj.y_sigma(i) + obj.y_mean(i); % de-scale output-vector
            end
        end

        function evalNextStep(obj,u,varargin)
        % calculate all state and output variables in next step
        % u is the input vector applied between the current time and the end of the next step
        % this function is called by dynamic simulator
            P = 1;
            if nargin > 2
                P = varargin{1};
            end
            M = size(u,2);
            if M < P
                u = [u repmat(u(:,end),1,P-M)];
            else
                u = u(:,1:P);
            end
            % march states by N-steps
            for p = 1:P
                u_scaled = (u(:,p) - obj.u_mean)./obj.u_sigma; % scale input vector
                for i = 1:obj.ny
                    for j = 1:obj.nu
                        obj.x{i,j} = obj.A{i,j}*obj.x{i,j} + obj.B{i,j}*u_scaled(j); % linear marching of states: x[k+1] = Ax[k] + Bu[k]
                    end
                end
            end
            % populate output only at final step
            for i = 1:obj.ny
                obj.populateAnnStatesFromDecoupledStates(i);
                [ym_scaled] = obj.predictSingleOutput(i); % Nonlinear mapping of states to outputs through neural-network
                obj.y(i) = ym_scaled*obj.y_sigma(i) + obj.y_mean(i); % de-scale output-vector
            end
        end

        function [y_P,dyP_dduM] = predictNextStep(obj,u,varargin)
            % Predict response (not update DRM) using defined input(s) (general)
            % Usage: [y_P,dy_du] = predictNextStep(u,P)
            %   where, size(u,2) ~ M
            P = 1;
            if nargin > 2
                P = varargin{1};
            end
            M = size(u,2);
            if nargout >=2 && ~obj.fJacobianPopulated
                obj.generatePredictionMatrices(P,M);
            end
            if M < P
                u = [u repmat(u(:,end),1,P-M)];
            else
                u = u(:,1:P);
            end
            
            y_P = repmat(obj.y,1,P);
            x_ = obj.x;
            x_ann_ = obj.x_ann;
                        
            y_du = cell(P,M);
            yiP_duM = cell(obj.ny,1);
            
            for iy = 1:obj.ny
                for p = 1:P
                    u_scaled = (u(:,p) - obj.u_mean)./obj.u_sigma; % scale input vector
                    for j = 1:obj.nu
                        x_{iy,j} = obj.A{iy,j}*x_{iy,j} + obj.B{iy,j}*u_scaled(j); % linear marching of states: x[k+1] = Ax[k] + Bu[k]
                    end
                    % Equivalent of populateAnnStatesFromDecoupledStates(i)
                    ifirst = 1;
                    for j = 1:obj.nu
                        ilast = ifirst + length(obj.A{iy,j}) - 1;
                        x_ann_{iy}(ifirst:ilast) = x_{iy,j}(1:end);
                        ifirst = ilast + 1;
                    end
                    if nargout >= 2
                        [ym_scaled,dy_dxann] = obj.ANN(iy).predict(x_ann_{iy});
                        for m = 1:M
                            y_du{p,m} = (dy_dxann.*obj.y_sigma(iy)) * obj.dxann_ddu{iy}{p,m};
                        end
                    else
                        [ym_scaled] = obj.ANN(iy).predict(x_ann_{iy});
                    end
                    y_P(iy,p) = ym_scaled*obj.y_sigma(iy) + obj.y_mean(iy); % de-scale output-vector
                end
                
                if nargout >= 2
                    yiP_duM{iy} = cell2mat(y_du);
                end
            end

            if nargout >= 2
                dyP_dduM = cell(P,M);
                for p = 1:P
                    for m = 1:M
                        for iy = 1:obj.ny
                            dyP_dduM{p,m}(iy,:) = yiP_duM{iy}(p,(m-1)*obj.nu+1:m*obj.nu);
                        end
                    end
                end
            end
        end
            
        function generatePredictionMatrices(obj,P,M)
			obj.dxann_ddu = cell(obj.ny);
            J = cell(P,M);
            % obtain augmented matrices for each output
            Ai = cell(obj.nu,obj.nu); Bi = cell(obj.nu,obj.nu);
            for iy = 1:obj.ny
                for i = 1:obj.nu
                    for j = 1:obj.nu
                        if i == j
                            Ai{i,j} = obj.A{iy,i};
                            Bi{i,j} = obj.B{iy,i}./obj.u_sigma(i);
                        else
                            Ai{i,j} = zeros(size(obj.A{iy,i},1),size(obj.A{iy,j},2));
                            Bi{i,j} = zeros(size(obj.B{iy,i}));
                        end
                    end
                end
                A_aug = cell2mat(Ai); B_aug = cell2mat(Bi);
                
                for i = 1:P
                    for j = 1:M
                        if j <= i
                            sum = B_aug;
                            for k = 1:i-j
                                sum = sum + (A_aug^k)*B_aug;
                            end
                            J{i,j} = sum;
                        else
                            J{i,j} = zeros(size(B_aug));
                        end
                    end
                end
                obj.dxann_ddu{iy} = J;
            end
            obj.fJacobianPopulated = 1;
        end
            

        function evalNextStateRelatedToOutputs(obj,u,iy)
        % calculate x{i,j} and then update x_ann{} related to defined outputs
        % iy is vector of indices of related output variables
        % this function is called by Kalman filter's predict function
            u_scaled = (u - obj.u_mean)./obj.u_sigma; % Scale input vector
            niy = size(iy,1);
            for i = 1:niy
                iyi = iy(i);
                for j = 1:obj.nu
                    obj.x{iyi,j} = obj.A{iyi,j}*obj.x{iyi,j} + obj.B{iyi,j}*u_scaled(j); % linear marching of states: x[k+1] = Ax[k] + Bu[k]
                end
                obj.populateAnnStatesFromDecoupledStates(iyi);
            end
        end

        function y_out = evalRelatedOutputsFromAnnStates(obj,iy)
        % calculate related outputs using the related states in x_ann{} without touching the decoupled state variables x{i,j}
        % iy is vector of indices of related output variables
            niy = size(iy,1);
            y_out = zeros(niy,1);
            for i = 1:niy
                [ym_scaled] = obj.predictSingleOutput(iy(i)); % nonlinear mapping of states to outputs through neural-network
                y_out(i) = ym_scaled*obj.y_sigma(iy(i)) + obj.y_mean(iy(i)); % de-scale output-vector
            end
        end

        function populateAnnStatesFromDecoupledStates(obj,i)
        % set ANN states x_ann{i} using decoupled states in x{i,:}
        % i is the index of output
            ifirst = 1;
            for j = 1:obj.nu
                ilast = ifirst + length(obj.A{i,j}) - 1;
                obj.x_ann{i}(ifirst:ilast) = obj.x{i,j}(1:end);
                ifirst = ilast + 1;
            end
        end

        function populateDecoupledStatesFromAnnStates(obj,i)
        % set decoupled states x{i,:} using ANN states x_ann{i}
        % i is the index of output
            ifirst = 1;
            for j = 1:obj.nu
                ilast = ifirst + length(obj.A{i,j}) - 1;
                obj.x{i,j}(1:end) = obj.x_ann{i}(ifirst:ilast);
                ifirst = ilast + 1;
            end
        end

        function x_all = getAnnStatesRelatedToOutputs(obj,iy)
        % get states related to outputs in x_ann{}
        % x_all is a vector of all related state variables
        % iy is an array of indices of related outputs
            niy = size(iy,1);
            nstate = 0;
            for i = 1:niy
               nstate = nstate + obj.nx_ann(iy(i));
            end
            x_all = zeros(nstate,1);
            ifirst = 1;
            for i = 1:niy
                ilast = ifirst + obj.nx_ann(iy(i)) - 1;
                x_all(ifirst:ilast) = obj.x_ann{iy(i)}(1:end);
                ifirst = ilast + 1;
            end
        end

        function setAnnStatesRelatedToOutputs(obj,x_all,iy)
        % set states related to outputs in x_ann{}
        % x_all is a vector of all related state variables
        % iy is an array of indices of related outputs
            niy = size(iy,1);
            ifirst = 1;
            for i = 1:niy
                ilast = ifirst + obj.nx_ann(iy(i)) - 1;
                obj.x_ann{iy(i)}(1:end) = x_all(ifirst:ilast);
                ifirst = ilast + 1;
            end
        end

        function setAnnAndDecoupledStatesRelatedToOutputs(obj,x_all,iy)
        % set states related to ouputs in x_ann{} and x{i,j}
        % x_all is a vector of all related state variables
        % iy is an array of indices of related outputs
            niy = size(iy,1);
            ifirst = 1;
            for i = 1:niy
                ilast = ifirst + obj.nx_ann(iy(i)) - 1;
                obj.x_ann{iy(i)}(1:end) = x_all(ifirst:ilast);
                obj.populateDecoupledStatesFromAnnStates(iy(i));
                ifirst = ilast + 1;
            end
        end

        function [y,dy_dxann] = predictSingleOutput(obj,i)
        % do neural network mapping from state variables to scaled output
        % i is the output index
            if nargout >= 2
                [y,dy_dxann] = obj.ANN(i).predict(obj.x_ann{i});
            else
                [y] = obj.ANN(i).predict(obj.x_ann{i});
            end
        end

        function nx = getNumberOfStatesRelatedToOutputs(obj,iy)
        % get number of states related to specified outputs
        % iy is vector of indices of related output variables
            niy = size(iy,1);
            nx = 0;
            for i = 1:niy
                nx = nx + obj.nx_ann(iy(i)); 
            end
        end

        function icross = getCrossIndices(obj,iy)
        % returned icross is an augmented matrix with 1 for sub-matrices of x_ann{} and 0 in anywhere else, i.e. 0 for decoupled outputs
        % iy is vector of indices of related output variables
            niy = size(iy,1);
            nx = obj.getNumberOfStatesRelatedToOutputs(iy);
            icross = zeros(nx,nx);
            ifirst = 1;
            for i = 1:niy
                ilast = ifirst + obj.nx_ann(iy(i)) - 1;
                for ii = ifirst:ilast
                    for jj = ifirst:ilast
                        icross(ii,jj) = 1;
                    end
                end
                ifirst = ilast + 1;
            end
        end

        function icross = getCrossIndices2(obj,iy)
        % returned icross is an augmented matrix with 1 for sub-matrices of A{i,j} and 0 in anywhere else
        % iy is vector of indices of related output variables
            niy = size(iy,1);
            nx = obj.getNumberOfStatesRelatedToOutputs(iy);
            icross = zeros(nx,nx);
            ifirst = 1;
            for i = 1:niy
                for j = 1:obj.nu
                    ilast = ifirst + length(obj.A{iy(i),j}) - 1;
                    for ii = ifirst:ilast
                        for jj = ifirst:ilast
                            icross(ii,jj) = 1;
                        end
                    end
                    ifirst = ilast + 1;
                end
            end
        end
    end
end
