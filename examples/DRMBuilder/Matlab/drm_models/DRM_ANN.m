classdef DRM_ANN < handle
    
% Class-definition for artifitial neural network used by D-RM Builder
%
% Written and developed by:
% Priyadarshi Mahapatra, URS Corporation / National Energy Technology Laboratory, 2013
% Jinliang Ma, URS Corporation / National Energy Technology Laboratory, 2013
%
% Last Modified: September 2013

    properties
        nx;                 %number of input variables
        ny;                 %number of output variables
        nlayer_hid;         %number of hidden layers, always 1
        nneuron_hid;        %number of neurons in hidden layer
        steepness_hid;      %steepness in hidden layers
        steepness_out;      %steepness in output layer
        iactivation_hid;    %activation function type in hidden layers
        iactivation_out;    %activation function type in output layer
        weight;             %weight vector
        mean_in;            %mean vector of input variables
        sigma_in;           %standard deviation vector of input variables
        mean_out;           %mean vector of output variables
        sigma_out;          %standard deviation vector of output variables
    end
    
    methods
        function obj = DRM_ANN(ann)
            if nargin == 1
                obj.nx = ann.nx;
                obj.ny = ann.ny;
                obj.nlayer_hid = ann.nhid;
                obj.nneuron_hid = ann.nneuron_hid;
                obj.steepness_hid = ann.steepness_hidden;
                obj.steepness_out = ann.steepness_output;
                obj.iactivation_hid = ann.iactivation_hidden;
                obj.iactivation_out = ann.iactivation_output;
                obj.weight = ann.weight;
                obj.mean_in = ann.mean_in;
                obj.mean_out = ann.mean_out;
                obj.sigma_in = ann.sigma_in;
                obj.sigma_out = ann.sigma_out;
            end
        end
        
        function [y,dy_dx] = predict(obj,x)
            nlayer = 2 + obj.nlayer_hid;
            nneuron_layer = [obj.nx+1 obj.nneuron_hid+1 obj.ny+1];
            nneuron_total = obj.nx+obj.ny+obj.nneuron_hid+3;
            iconn_prev = 1:nneuron_total;
            ineuron_prev = 1:nneuron_total;
            value = zeros(1,nneuron_total);
            y = zeros(1,obj.ny);
            dy_dx = zeros(obj.ny,obj.nx);
            for i=1:obj.nx
                value(i) = (x(i)-obj.mean_in(i))/obj.sigma_in(i);
            end
            value(obj.nx+1) = 1;
            ineuron_start_prev = 1;
            ineuron_start_curr = nneuron_layer(1) + 1;
            iconn = 1;
            for i=2:nlayer
                nneuron_layer_prev = nneuron_layer(i-1);
                nneuron_layer_curr = nneuron_layer(i);
                for j=1:nneuron_layer_curr - 1
                    ineuron = ineuron_start_curr + j - 1;
                    ineuron_prev(ineuron) = ineuron_start_prev;
                    iconn_prev(ineuron) = iconn;
                    sum = 0;
                    for k=1:nneuron_layer_prev
                        sum = sum + value(ineuron_start_prev + k - 1)*obj.weight(iconn);
                        iconn = iconn + 1;
                    end
                    if i<nlayer
                        steepness = obj.steepness_hid;
                        itype_activation = obj.iactivation_hid;
                    else
                        steepness = obj.steepness_out;
                        itype_activation = obj.iactivation_out;
                    end
                    sum = sum*steepness;
                    switch itype_activation
                    case 0
                        value(ineuron) = sum;
                    case 1
                        value(ineuron) = 1/(1 + exp(-2*sum));
                    case 2
                        value(ineuron) = 2/(1+exp(-2*sum))-1;
                    otherwise
                        value(ineuron) = sum;
                    end
                end
                value(ineuron + 1) = 1;
                ineuron_start_prev = ineuron_start_curr;
                ineuron_start_curr = ineuron_start_curr + nneuron_layer_curr;
            end
            ineuron_start_curr = nneuron_total - obj.ny - 1;
            for i=1:obj.ny
                y(i) = value(ineuron_start_curr + i)*obj.sigma_out(i) + obj.mean_out(i);
            end

            % Calculate the Jacobians (needed for APC prediction)
            if nargout >= 2
                derivative = ones(1,nneuron_total);
                ineuron_start_curr = nneuron_layer(1);
                for i=2:nlayer
                    nneuron_layer_curr = nneuron_layer(i);
                    if i<nlayer
                        steepness = obj.steepness_hid;
                        itype_activation = obj.iactivation_hid;
                    else
                        steepness = obj.steepness_out;
                        itype_activation = obj.iactivation_out;
                    end
                    for j=1:nneuron_layer_curr-1
                        ineuron = ineuron_start_curr + j;
                        switch itype_activation
                        case 0
                            derivative(ineuron) = steepness;
                        case 1
                            derivative(ineuron) = 2*steepness*value(ineuron)*(1-value(ineuron));
                        case 2
                            derivative(ineuron) = steepness*(1-value(ineuron)*value(ineuron));
                        otherwise
                            derivative(ineuron) = steepness;
                        end
                    end
                    ineuron_start_curr = ineuron_start_curr + nneuron_layer_curr;
                end
                for j=1:obj.ny
                    derivative_chain = zeros(1,nneuron_total);
                    ineuron = nneuron_total - obj.ny - 1 + j;
                    ineuron_pre = ineuron_prev(ineuron);
                    iconn_pre = iconn_prev(ineuron);
                    for i=1:nneuron_layer(nlayer-1) - 1
                        ineuron_p = ineuron_pre + i - 1;
                        derivative_chain(ineuron_p) = derivative_chain(ineuron_p) + derivative(ineuron)*obj.weight(iconn_pre + i - 1);
                    end
                    ineuron_start_curr = nneuron_total - obj.ny - nneuron_layer(nlayer-1);
                    for ilayer=nlayer-1:-1:2
                        for k=1:nneuron_layer(ilayer) - 1
                            ineuron = ineuron_start_curr + k - 1;
                            ineuron_pre = ineuron_prev(ineuron);
                            iconn_pre = iconn_prev(ineuron);
                            for i=1:nneuron_layer(ilayer-1) - 1
                                ineuron_p = ineuron_pre + i - 1;
                                derivative_chain(ineuron_p) = derivative_chain(ineuron_p) + derivative(ineuron)*obj.weight(iconn_pre + i - 1)*derivative_chain(ineuron);
                            end
                        end
                        ineuron_start_curr = ineuron_start_curr - nneuron_layer(ilayer);
                    end
                    for i=1:obj.nx
                        dy_dx(j,i) = derivative_chain(i)*obj.sigma_out(j)/obj.sigma_in(i);
                    end
                end
            end
        end 
    end
end
