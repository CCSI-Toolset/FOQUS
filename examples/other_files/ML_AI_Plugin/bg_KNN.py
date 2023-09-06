import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import LeaveOneOut
from pyomo.common.fileutils import this_file_dir
import os

def get_dataset(y):
    data_file = os.path.join(this_file_dir(), 'cd_x_y.csv')
    df = pd.read_csv(data_file, sep=';', header=None)
    derivative_file = os.path.join(this_file_dir(), 'cd_dy.csv')
    df_1 = pd.read_csv(derivative_file, sep=';', header=None)
    features = df.iloc[:,:16]
    labels = df_1.iloc[:,y-1:y]
    return df, df_1, features, labels

def main(nn,y):
    df, df_1, features, labels = get_dataset(y)

    # Split the dataset into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.3,shuffle=False)

    # Standardize the feature data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Create the KNN regressor
    n_neighbors = nn  # Number of neighbors to consider
    knn_regressor = KNeighborsRegressor(n_neighbors=n_neighbors)

    # Fit the KNN regressor to the training data
    knn_regressor.fit(X_train_scaled, y_train)

    # Predict target values for the test set
    y_pred = knn_regressor.predict(X_test_scaled)

    # Calculate the root mean squared error (RMSE)
    RMSE = np.sqrt(mean_squared_error(y_test, y_pred))
    predictions = pd.DataFrame(y_pred)
    knn_regressor = KNeighborsRegressor(n_neighbors=10)
    knn_regressor.fit(X_train_scaled, y_train)

    # Calculate feature importance using LOOCV

    # Print or analyze the feature importance scores
    return knn_regressor, RMSE,y_train,predictions

# Assuming you have already created the KNN model and feature scaled data

if __name__ == "__main__":
    final_df = pd.DataFrame()
    models=[]
    for i in range(1,17):
        print(i)
        model,RMSE,y_train,predictions = main(nn=10,y=i)
        models.append(model)
        final_df[i-1] = pd.concat([y_train,predictions.rename(columns={0:i-1})],ignore_index=True)
        print(i,RMSE)
    final_df.to_csv('derivatives.csv',sep=';',index=False)



