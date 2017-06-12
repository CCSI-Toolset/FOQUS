classdef DRM_NARMA < handle
    
% Class definition for NARMA based dynamic reduced models
%
% Written and developed by:
% Priyadarshi Mahapatra, URS Corporation / National Energy Technology Laboratory, 2013
% Jinliang Ma, URS Corporation / National Energy Technology Laboratory, 2013
%
% For details of D-RM Builer application and D-RMs, refer to CCSI's D-RM Builer user's manual
% 
% Last Modified: September 2013

    properties
        dt;         %sampling time interval
        nu;         %number of input variables
        ny;         %number of output variables
        nhistory;   %number of history points used
        u_mean;     %vector of means of input variables, size [nu]
        y_mean;     %vector of means of output varaibles, size [ny]
        u_sigma;    %vector of standard deviations of input variables, size [nu]
        y_sigma;    %vector of standard deviations of output varaibles, size [ny]
        ANN;        %artifitial neural networks
        u_history;  %matrix of scaled input history data
        y_history;  %matrix of scaled output history data
        x_ann;      %neural network input vector, size [(nu+ny)*nhistory]
        y;          %output vector, size [ny]
        fjacobian;  %flag for calculating Jacobian matrix when calling neural network predict() function
    end
    
    methods
        function obj = DRM_NARMA(dt,nu,ny,nhistory,u_mean,y_mean,u_sigma,y_sigma,NN)
            if nargin == 9
                obj.dt = dt;
                obj.nu = nu;
                obj.ny = ny;
                obj.nhistory = nhistory;
                obj.u_mean = u_mean';
                obj.y_mean = y_mean';
                obj.u_sigma = u_sigma';
                obj.y_sigma = y_sigma';
                obj.ANN = DRM_ANN(NN(1));
                obj.fjacobian = 0;
                obj.u_history = zeros(obj.nu,obj.nhistory);
                obj.y_history = zeros(obj.ny,obj.nhistory);
                obj.x_ann = zeros((obj.nu+obj.ny)*obj.nhistory,1);
                obj.y = zeros(obj.ny,1);
            end
        end
        
        function initialize(obj,u_ss,y_ss)
            u_scaled = (u_ss - obj.u_mean)./obj.u_sigma; % Scale steady-state input vector
            y_scaled = (y_ss - obj.y_mean)./obj.y_sigma; % Scale steady-state output vector
            %prepare x_ann
            k = 1;
            for i = 1:obj.nu
                for j = 1:obj.nhistory
                    obj.x_ann(k) = u_scaled(i);
                    obj.u_history(i,j) = u_scaled(i);
                    k = k + 1;
                end
            end
            for i = 1:obj.ny
                for j = 1:obj.nhistory
                    obj.x_ann(k) = y_scaled(i);
                    obj.y_history(i,j) = y_scaled(i);
                    k = k + 1;
                end
            end
            [ym_scaled] = obj.ANN.predict(obj.x_ann);
            for i = 1:obj.ny
                obj.y_history(i,obj.nhistory) = ym_scaled(i);
                obj.y(i) = ym_scaled(i)*obj.y_sigma(i) + obj.y_mean(i); % Descale output vector
            end
        end
        
        function evalNextStep(obj,u)
            u_scaled = (u - obj.u_mean)./obj.u_sigma; % Scale input vector
            k = 1;
            for i = 1:obj.nu
                for j = 1:obj.nhistory-1
                    obj.u_history(i,j) = obj.u_history(i,j+1);
                    obj.x_ann(k) = obj.u_history(i,j);
                    k = k + 1;
                end
                obj.u_history(i,obj.nhistory) = u_scaled(i);
                obj.x_ann(k) = u_scaled(i);
                k = k + 1;
            end
            for i = 1:obj.ny
                for j = 1:obj.nhistory-1
                    obj.x_ann(k) = obj.y_history(i,j);
                    obj.y_history(i,j) = obj.y_history(i,j+1);
                    k = k + 1;
                end
                obj.x_ann(k) = obj.y_history(i,obj.nhistory);
                k = k + 1;
            end
            [ym_scaled] = obj.ANN.predict(obj.x_ann);
            for i = 1:obj.ny
                obj.y(i) = ym_scaled(i)*obj.y_sigma(i) + obj.y_mean(i); % De-scale output-vector
                obj.y_history(i,obj.nhistory) = ym_scaled(i);
            end            
        end
    end
end
