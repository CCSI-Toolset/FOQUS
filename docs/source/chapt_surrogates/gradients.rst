.. _gengrad:

Gradient Generation to Support Gradient-Enhanced Neural Networks
================================================================

Neural networks are useful in instances where multivariate process data
is available and the mathematical functions describing the variable
relationships are unknown. Training deep neural networks is most efficient
when samples of the variable derivatives, or gradients, are collected
simultaneously with process data. However, gradient data is often unavailable
unless the physics of the system are known and predetermined such as in
fluid dynamics with outputs of known physical properties.

These gradients may be estimated numerically using solely the process data. The
gradient generation tool described below requires a Comma-Separated Value (CSV) file
containing process samples (rows), with inputs in the left columns and outputs in the rightmost
columns. Multiple outputs are supported, as long as they are the rightmost columns, and
the variable columns may have string (text) headings or data may start in row 1. The method
produces a CSV file for each output variable containing gradients with respect to each input
variable (columns), for each sample point (rows). After navigating to the FOQUS directory
*examples/other_files/ML_AI_Plugin*, the code below sets up and calls the gradient generation
method on the example dataset *MEA_carbon_capture_dataset_mimo.csv*:

.. code:: python

  # required imports
  >>> import pandas as pd
  >>> import numpy as np
  >>> from generate_gradient_data import generate_gradients
  >>> 
  >>> data = pd.read_csv(r"MEA_carbon_capture_dataset_mimo.csv")  # get dataset
  >>> data_array = np.array(data, ndmin=2)  # convert to Numpy array
  >>> n_x = 6  # we have 6 input variables, in the leftmost 6 columns

  >>> gradients = generate_gradients(
  >>>   xy_data=data_array,
  >>>   n_x=n_x,
  >>>   show_plots=False,  # flag to plot regression results during gradient training
  >>>   optimize_training=True,  # will try many regression settings and pick the best result
  >>>   use_simple_diff=True  # flag to use simple partials instead of chain rule formula; defaults to False if not passed
  >>>   )
  >>> print("Gradient generation complete.")

  >>> for output in range(len(gradients)):  # save each gradient array to a CSV file
  >>>   pd.DataFrame(gradients[output]).to_csv("gradients_output" + str(output) + ".csv")
  >>>   print("Gradients for output ", str(output), " written to gradients_output" + str(output) + ".csv",)
  
Internally, the gradient generation methods automatically executes a series of actions on the dataset:

1. Import process data of size *(m, n_x + n_y)*, where *m* is the number of sample rows,
*n_x* is the number of input columns and *n_y* is the number of output columns. Given *n_x*,
the data is split into an input array *X* and an output array *Y*.

2. For each input *xi* and each output *yj*, estimate the gradient using a multivariate
chain rule approximation. For example, the gradient of y1 with respect to x1 is
calculated at each point as:

:math:`\frac{Dy_1}{Dx_1} = \frac{dy_1}{dx_1} \frac{dx_1}{dx_1} + \frac{dy_1}{dx_2} \frac{dx_2}{dx_1} + \frac{dy_1}{dx_3} \frac{dx_3}{dx_1} + ...`

where *D/D* represents the total derivative, *d/d* represents a partial derivative at each
sample point. *y1*, *x1*, *x2*, *x3*, and so on are vectors with values at each sample point *m*, and
this formula produces the gradients of each output with respect to each input at each sample point by iterating
through the dataset. The partial derivatives are calculated by simple finite difference. For example:

:math:`\frac{dy_1}{dx_1} (m_{1.5}) = \frac{y_1 (m_2) - y_1 (m_1)}{x_1 (m_2) - x_1 (m_1)}`

where *m_1.5* is the midpoint between sample points *m_2* and *m_1*. As a result, this scheme
calculates gradients at the points between the sample points, not the actual sample points.

3. Train an MLP model on the calculated midpoint and midpoint-gradient values. After normalizing the data
via linear scaling (see :ref:`mlaiplugin.datanorm`),
the algorithm leverages a small neural network model to generate gradient data for the actual
sampe points. Passing the argument *optimize_training=True* will train models using the optimizers
*Adam* or *RMSProp*, with activation functions *ReLu* or *Sigmoid* on hidden layers, using a *Linear*
or *ReLu* activation function on the output layer, building *2* or *8* hidden layers with *6* or *12*
neurons per hidden layer. The algorithm employs cross-validation to check the mean-squared-error (MSE) loss
on each model and uses the model with the smallest error to predict the sample gradients.

4. Predict the gradients at each sample point from the regressed model. This produces *n_y*
arrays with each having size *(m, n_x)* - the same size as the original input array *X*.

5. Concatenate the predicted gradients into a single array of size *(m, n_x, n_y)*. This is the
single object returned by the gradient generation method.
