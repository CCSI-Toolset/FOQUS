import os
import numpy as np
import pandas as pd
import random as rn
import tensorflow as tf

# set seed values for reproducibility
os.environ["PYTHONHASHSEED"] = "0"
os.environ[
    "CUDA_VISIBLE_DEVICES"
] = ""  # changing "" to "0" or "-1" may solve import issues
np.random.seed(46)
rn.seed(1342)
tf.random.set_seed(62)

# Example follows the sequence below:
# 1) Code at end of file to import data and create model
# 2) Call create_model() to define inputs and outputs
# 3) Call CustomLayer to define network structure, which uses
#    call() to define layer connections and get_config to attach
#    attributes to CustomLayer class object
# 4) Back to create_model() to compile and train model
# 5) Back to code at end of file to save, load and test model

# custom class to define Keras NN layers
# note that this model is identical to mea_column_model in every aspect
# except for normalization, but needs a unique class name for the Keras
# registry - otherwise this will throw errors when both are loaded in FOQUS


@tf.keras.utils.register_keras_serializable()
class mea_column_model_customnormform_json(tf.keras.layers.Layer):
    def __init__(
        self,
        n_hidden=1,
        n_neurons=12,
        layer_act="relu",
        out_act="sigmoid",
        input_labels=None,
        output_labels=None,
        input_bounds=None,
        output_bounds=None,
        normalized=False,
        normalization_form="Linear",
        normalization_function=None,
        **kwargs
    ):

        super(
            mea_column_model_customnormform_json, self
        ).__init__()  # create callable object

        # add attributes from training settings
        self.n_hidden = n_hidden
        self.n_neurons = n_neurons
        self.layer_act = layer_act
        self.out_act = out_act

        # add attributes from model data
        self.input_labels = input_labels
        self.output_labels = output_labels
        self.input_bounds = input_bounds
        self.output_bounds = output_bounds
        self.normalized = normalized  # FOQUS will read this and adjust accordingly
        self.normalization_form = (
            normalization_form  # tells FOQUS which scaling form to use
        )
        self.normalization_function = (
            normalization_function  # tells FOQUS scaling formula to use
        )

        # create lists to contain new layer objects
        self.dense_layers = []  # hidden or output layers
        self.dropout = []  # for large number of neurons, certain neurons
        # can be randomly dropped out to reduce overfitting

        for layer in range(self.n_hidden):
            self.dense_layers.append(
                tf.keras.layers.Dense(self.n_neurons, activation=self.layer_act)
            )

        self.dense_layers_out = tf.keras.layers.Dense(2, activation=self.out_act)

    # define network layer connections
    def call(self, inputs):

        x = inputs  # single input layer, input defined in create_model()
        for layer in self.dense_layers:  # hidden layers
            x = layer(x)  # h1 = f(input), h2 = f(h1), ... using act func
        for layer in self.dropout:  # no dropout layers used in this example
            x = layer(x)
        x = self.dense_layers_out(x)  # single output layer, output = f(h_last)

        return x

    # attach attributes to class CONFIG
    def get_config(self):
        config = super(mea_column_model_customnormform_json, self).get_config()
        config.update(
            {
                "n_hidden": self.n_hidden,
                "n_neurons": self.n_neurons,
                "layer_act": self.layer_act,
                "out_act": self.out_act,
                "input_labels": self.input_labels,
                "output_labels": self.output_labels,
                "input_bounds": self.input_bounds,
                "output_bounds": self.output_bounds,
                "normalized": self.normalized,
                "normalization_form": self.normalization_form,
                "normalization_function": self.normalization_function,
            }
        )
        return config


# method to create model
def create_model(data):

    inputs = tf.keras.Input(shape=(np.shape(data)[1],))  # create input layer

    layers = mea_column_model_customnormform_json(  # define the rest of network using our custom class
        input_labels=xlabels,
        output_labels=zlabels,
        input_bounds=xdata_bounds,
        output_bounds=zdata_bounds,
        normalized=True,
        normalization_form="Custom",
        normalization_function="(datavalue - dataminimum)/(datamaximum - dataminimum)",
    )

    outputs = layers(inputs)  # use network as function outputs = f(inputs)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)  # create model

    model.compile(loss="mse", optimizer="RMSprop", metrics=["mae", "mse"])

    model.fit(xdata, zdata, epochs=500, verbose=0)  # train model

    return model


# Main code

# import data
data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")

xdata = data.iloc[:, :6]  # there are 6 input variables/columns
zdata = data.iloc[:, 6:]  # the rest are output variables/columns
xlabels = xdata.columns.tolist()  # set labels as a list (default) from pandas
zlabels = zdata.columns.tolist()  #    is a set of IndexedDataSeries objects
xdata_bounds = {i: (xdata[i].min(), xdata[i].max()) for i in xdata}  # x bounds
zdata_bounds = {j: (zdata[j].min(), zdata[j].max()) for j in zdata}  # z bounds

# normalize data using Linear form, pass as custom string and parse with SymPy
# users can normalize with any allowed form # manually, and then pass the
# appropriate flag to FOQUS from the allowed list:
# ["Linear", "Log", "Power", "Log 2", "Power 2", "Custom] - see the
# documentation for details on the scaling formulations
xmax, xmin = xdata.max(axis=0), xdata.min(axis=0)
zmax, zmin = zdata.max(axis=0), zdata.min(axis=0)
xdata, zdata = np.array(xdata), np.array(zdata)
for i in range(len(xdata)):
    for j in range(len(xlabels)):
        xdata[i, j] = (xdata[i, j] - xmin[j]) / (xmax[j] - xmin[j])
    for j in range(len(zlabels)):
        zdata[i, j] = (zdata[i, j] - zmin[j]) / (zmax[j] - zmin[j])

model_data = np.concatenate(
    (xdata, zdata), axis=1
)  # Keras requires a Numpy array as input

# define x and z data, not used but will add to variable dictionary
xdata = model_data[:, :-2]
zdata = model_data[:, -2:]

# create model
model = create_model(xdata)
model.summary()

# save as JSON
json_model = model.to_json()
with open("mea_column_model_customnormform_json.json", "w") as json_file:
    json_file.write(json_model)
model.save_weights("mea_column_model_customnormform_json_weights.h5")
