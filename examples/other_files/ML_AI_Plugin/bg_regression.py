import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

### Promising things to check
### scaling the neural net input

# Data preprocessing
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Normalizer

# Neural Net modules
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.callbacks import EarlyStopping
from pyomo.common.fileutils import this_file_dir
import os

df = pd.read_csv(os.path.join(this_file_dir(), 'cd_x_y.csv'),sep=';',header=None)

# drop any rows with missing values
print(df.head())
# convert categorical variable into dummy variables
y = df[16]
X = df.drop(16, axis=1)
print(X.shape, y.shape)

# convert to numpy array
X = np.array(X)
y = np.array(y)

# split into X_train and X_test
# always split into X_train, X_test first THEN apply minmax scaler
X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                    test_size=0.2,
                                                    random_state=123)
print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

# use minMax scaler
min_max_scaler = MinMaxScaler()
X_train = min_max_scaler.fit_transform(X_train)
X_test = min_max_scaler.transform(X_test)

def build_model():
    model = Sequential()
    model.add(Dense(6, input_shape=(X_train.shape[1],), activation='relu')) # (features,)
    model.add(Dense(6, activation='relu'))
    model.add(Dense(1, activation='linear')) # output node
    model.summary() # see what your model looks like
    return model

model = build_model()

# compile the model
model.compile(optimizer='rmsprop', loss='mse', metrics=['mae'])

# early stopping callback
es = EarlyStopping(monitor='val_loss',
                   mode='min',
                   patience=50,
                   restore_best_weights = True)

# fit the model!
# attach it to a new variable called 'history' in case
# to look at the learning curves
history = model.fit(X_train, y_train,
                    validation_data = (X_test, y_test),
                    callbacks=[es],
                    epochs=100,
                    batch_size=50,
                    verbose=1)

history_dict = history.history
loss_values = history_dict['loss'] # you can change this
val_loss_values = history_dict['val_loss'] # you can also change this
epochs = range(1, len(loss_values) + 1) # range of X (no. of epochs)
#plt.plot(epochs, loss_values, 'bo', label='Training loss')
#plt.plot(epochs, val_loss_values, 'orange', label='Validation loss')
#plt.title('Training and validation loss')
#plt.xlabel('Epochs')
#plt.ylabel('Loss')
#plt.legend()
#plt.show()

pred = model.predict(X_test)
pred

trainpreds = model.predict(X_train)

from sklearn.metrics import mean_absolute_error
print(mean_absolute_error(y_train, trainpreds)) # train
print(mean_absolute_error(y_test, pred)) # test


def sigmoid_deriv(x):
    ### Input integer or numpy array
    ### Outputs the sigmoid derivative of the respective number(s)
    sig = 1/(1+math.e**(-1*x))
    return sig*(1-sig)


def calculate_derivatives(row,y):
    ### Manually calculates the derivatives
    ### Currently set to linear Neural Network
    ### Can be simplified to matrix multiplication
    final = []
    for r in range(len(row)):
        for i in range(16):
            first = model.layers[0].get_weights()[0][i]
            new = []
        for i in range(len(first)):
            new.append(first[i])
        weights = model.layers[1].get_weights()[0]
        second = [0]*len(model.layers[1].get_weights()[0][0])
        for a in range(len(new)):
            for b in range(len(second)):
                second[b] += (new[a]*weights[a][b])
        for b in range(len(second)):
            second[b] = second[b]
        x_final = 0
        for c in range(len(second)):
            x_final += second[c]*model.layers[2].get_weights()[0][c]
        final.append(x_final[0])
    return final


df = pd.read_csv(os.path.join(this_file_dir(), 'cd_x_y.csv'),sep=';',header=None)
y = df[16]
X1 = df.drop(16, axis=1)
### Normalization
scaler = MinMaxScaler()
X1 = scaler.fit_transform(X1)
print(len(X1))

with open('derivatives.csv','w') as f:
    for index in range(len(X1)):
        row = X1[index]
        final = calculate_derivatives(row,y[index])
        print(index)
        for i in range(len(final)):
            f.write(str(final[i]))
            if i == len(final)-1:
                f.write('\n')
            else:
                f.write(';')
f.close()