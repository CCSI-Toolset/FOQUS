function matlab_foqus_script(MatlabFunctionName,PsuadFileName,path)

    data_imp = py.foqus_lib.framework.uq.LocalExecutionModule.LocalExecutionModule.readSampleFromPsuadeFile(path+PsuadFileName);

    df = py.pandas.DataFrame(data_imp.inputData);
    df_dict = df.to_dict();

    i = 1;
    for idx = py.list(df.shape)
        shp(i) = double(idx{1});
        i = i+1;
    end

    in_names = py.list(data_imp.model.inputNames);
    out_names = py.list(data_imp.model.outputNames);
    names = in_names + out_names;
    n_in = length(in_names);
    n_out = length(out_names);
    n = length(names);
    m = shp(1);

    data = zeros(m,n) ;
    data(:,1:n_in) = double(data_imp.inputData);

    outputs = zeros(m,n_out) ;
    for i=1:m
        inputs = data(i,1:n_in);
        try
            outputs(i, 1:n_out-1) = MatlabFunctionName(inputs);
            outputs(i, n_out) = 0;
        catch
            outputs(i, 1:n_out-1) = 0;
            outputs(i, n_out) = 1;     
        end

    end

    data(:,n_in+1:n) = outputs ;

    data_array = py.numpy.array(data);
    index = py.numpy.arange(0,100,1);
    df_data = py.pandas.DataFrame(data_array,index,names);
    save = df_data.to_csv(path+'outputs.csv') ;
    % "PreserveVariableNames" was introduced in MATLAB 2019b, so if you are
    % using older MATLAB versions, you need to remove that parameter below.
    T = readtable(path+'outputs.csv','PreserveVariableNames',true);
    %T = readtable(path+'outputs.csv');
    [~,n1]=size(T);
    writetable(T(:,2:n1),path+'outputs.csv')
end

