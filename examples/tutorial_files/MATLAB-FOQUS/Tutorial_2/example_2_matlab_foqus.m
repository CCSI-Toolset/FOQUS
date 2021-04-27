clear all
clc

% This is the path where the MATLAB model, the "matlab_foqus_script.m" file and the PSUADE file "data.dat" are located
path = "C:\Users\yancycd\MATLAB-FOQUS\";
% This is the PSUADE file name
PsuadFileName = 'data.dat';
% This is the MATLAB function name that contains the model
MatlabFunctionName = @(x) CSTR_Steady_State(x);
% Call the "matlab_foqus_script.m" file
matlab_foqus_script(MatlabFunctionName, PsuadFileName, path)