//NueralNetwork.cpp
#include <stdio.h>
#include <math.h>
#include <time.h>
#include <stdlib.h>
#include "NeuralNetwork.h"

CNeuralNetwork::CNeuralNetwork()
{
	irand_seed = 0;		//set to a const number of  0
	itrain_method = 1;
	ninput = 1;
	noutput = 1;
	nneuron = 5;
	nconnection = 10;
	nlayer = 3;
	nepoch_max = 50000;
	weight_init = 0.01;
	rate_learn = 0.6;
	coeff_momentum = 0.1;
	delta_min = 0;//1e-6;
	delta_max = 50;
	delta0 = 0.5;	
	eta_minus = 0.5;
	eta_plus = 1.2;
	iactivation_hidden = 2;
	iactivation_output = 0;
	steepness_hidden = 1;
	steepness_output = 1;
	error_pair = 0;
	error_batch = 0;
	error_batch_old = 0;
	error_stop = 0.00001;
	pnneuron_layer = NULL;
	piconn_anterior = NULL;
	pineuron_conn_from = NULL;
	pineuron_conn_to = NULL;
	pilayer_conn = NULL;
	py = NULL;
	py_derivative = NULL;
	py_2nd_derivative = NULL;
	pdelta = NULL;
	pweight = NULL;
	pweight_derivative = NULL;
	pweight_derivative_new = NULL;
	pweight_step_size = NULL;
	pweight_change = NULL;
	pmean = NULL;
	psigma = NULL;
}

CNeuralNetwork::~CNeuralNetwork()
{
	DeleteIntArrays();
	DeleteDoubleArrays();
}

void CNeuralNetwork::AllocateIntArrays()
{
	//nlayer and nneuron should have been set
	DeleteIntArrays();
	pnneuron_layer = new int [nlayer+nneuron+3*nconnection];
	piconn_anterior = pnneuron_layer + nlayer;
	pineuron_conn_from = piconn_anterior + nneuron;
	pineuron_conn_to = pineuron_conn_from + nconnection;
	pilayer_conn = pineuron_conn_to + nconnection;
}

void CNeuralNetwork::AllocateDoubleArrays()
{
	DeleteDoubleArrays();
	py = new double [nneuron*4 + nconnection*5 + (ninput+noutput)*2];
	py_derivative = py + nneuron;
	py_2nd_derivative = py_derivative + nneuron;
	pdelta = py_2nd_derivative + nneuron;
	pweight = pdelta + nneuron;
	pweight_derivative = pweight + nconnection;
	pweight_derivative_new = pweight_derivative + nconnection;
	pweight_step_size = pweight_derivative_new + nconnection;
	pweight_change = pweight_step_size + nconnection;
	pmean = pweight_change + nconnection;
	psigma = pmean + ninput + noutput;
}

void CNeuralNetwork::DeleteIntArrays()
{
	if (pnneuron_layer)
		delete [] pnneuron_layer;
	pnneuron_layer = NULL;
	piconn_anterior = NULL;
	pineuron_conn_from = NULL;
	pineuron_conn_to = NULL;
	pilayer_conn = NULL;
}

void CNeuralNetwork::DeleteDoubleArrays()
{
	if (py)
		delete [] py;
	py = NULL;
	py_derivative = NULL;
	py_2nd_derivative = NULL;
	pdelta = NULL;
	pweight = NULL;
	pweight_derivative = NULL;
	pweight_derivative_new = NULL;
	pweight_step_size = NULL;
	pweight_change = NULL;
	pmean = NULL;
	psigma = NULL;
}

void CNeuralNetwork::SetNetworkStructure(int nin, int nout, int nlayer_hid, int* pnneuron_hid)
{
	//nin:			number of input parameters
	//nout:			number of output parameters
	//nlayer_hid:	number of hidden layers
	//pnneuron_hid:	number of neurons in each hidden layer excluding bias neuron
	//Note: current network structure is fully connected feed forward structure with one bias neuron in each layer including output layer
	int i, j, k;
	int ineuron1st;			//index of the first neuron in a layer
	int iconn;				//connection index
	int nneuron_prev_layer;		//number of neurons in previous layer including bias neuron
	ninput = nin;
	noutput = nout;
	nlayer = nlayer_hid + 2;
	//calculate total number of neurons and number of connectoins
	nneuron = ninput + noutput + nlayer_hid + 2;
	nconnection = 0;
	nneuron_prev_layer = ninput + 1;
	for (i=0; i<nlayer_hid; i++)
	{
		nneuron += pnneuron_hid[i];
		nconnection += nneuron_prev_layer*pnneuron_hid[i];
		nneuron_prev_layer = pnneuron_hid[i] + 1;
	}
	nconnection += noutput*nneuron_prev_layer;
	AllocateIntArrays();
	//initialize piconn_anterior[]
	for (i=0; i<nneuron; i++)
		piconn_anterior[i] = -1;
	pnneuron_layer[0] = ninput + 1;
	pnneuron_layer[nlayer-1] = noutput + 1;
	for (i=0; i<nlayer_hid; i++)
		pnneuron_layer[i+1] = pnneuron_hid[i] + 1;
	//calculate piconn_anterior[]
	ineuron1st = 0;
	iconn = 0;
	for (i=1; i<nlayer; i++)
	{
		ineuron1st += pnneuron_layer[i-1];
		for (j=0; j<pnneuron_layer[i]-1; j++)
		{
			piconn_anterior[ineuron1st+j] = iconn;
			iconn += pnneuron_layer[i-1];
		}
	}
	//calculate pineuron_conn_from, pineuron_conn_to and pilayer_conn
	//use nneuron_prev_layer as the first neuron index of previous layer
	ineuron1st = 0;
	iconn = 0;
	nneuron_prev_layer = 0;
	for (i=1; i<nlayer; i++)
	{
		ineuron1st += pnneuron_layer[i-1];
		for (j=0; j<pnneuron_layer[i]-1; j++)
		{
			for (k=0; k<pnneuron_layer[i-1]; k++)
			{
				pineuron_conn_from[iconn] = nneuron_prev_layer + k;
				pineuron_conn_to[iconn] = ineuron1st + j;
				pilayer_conn[iconn] = i-1;
				iconn++;
			}
		}
		nneuron_prev_layer = ineuron1st;
	}
	AllocateDoubleArrays();
	//also set default weight, weight derivative, weight step size, and weight delta
	if (irand_seed)
		srand((unsigned int)time(NULL));
	else
		srand(0);
	for (i=0; i<nconnection; i++)
	{
		pweight[i] = (double)rand()/(RAND_MAX-1)*2 - 1;
		pweight_derivative[i] = 0.0001;
		pweight_step_size[i] = delta0;
		pweight_change[i] = 0;
	}
	//set input neuron's y' y" and delta values
	for (i=0; i<ninput; i++)
	{
		py_derivative[i] = 1;
		py_2nd_derivative[i] = 0;
		pdelta[i] = 0;
	}
	//set bias neuron's y, y', y", and delta values
	ineuron1st = 0;
	for (i=0; i<nlayer; i++)
	{
		j = ineuron1st + pnneuron_layer[i] - 1;
		py[j] = 1;
		py_derivative[j] = 1;
		py_2nd_derivative[j] = 0;
		pdelta[j] = 0;
		ineuron1st += pnneuron_layer[i];
	}
	//finally set mean and sigma to default
	SetDefaultMeanSigma();
}

void CNeuralNetwork::SetDefaultMeanSigma()
{
	int i;
	int ninout = ninput + noutput;
	for (i=0; i<ninout; i++)
	{
		pmean[i] = 0;
		psigma[i] = 1;
	}
}

void CNeuralNetwork::ForwardPropagation()
{
	int i, j, k;
	int ineuron;			//neuron index
	int iactivation;		//activation function type
	int ncurrent1;			//number of neurons in current layer, excluding bias neuron
	int nanterior;			//number of neurons in anterior layer
	int icurrent1st;		//first neuron index in the current layer
	int ianterior1st = 0;	//first neuron index in the anterior layer
	int iconn = 0;			//connection index
	double steepness;		//steepness
	double sum;
	for (i=1; i<nlayer; i++)
	{
		nanterior = pnneuron_layer[i-1];
		ncurrent1 = pnneuron_layer[i] - 1;
		icurrent1st = ianterior1st + nanterior;
		if (i<nlayer-1)
		{
			iactivation = iactivation_hidden;
			steepness = steepness_hidden;
		}
		else
		{
			iactivation = iactivation_output;
			steepness = steepness_output;
		}
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			sum = 0;
			for (k=0; k<nanterior; k++)
				sum += py[ianterior1st+k]*pweight[iconn++];
			sum *= steepness;
			switch (iactivation)
			{
			case 0:		//linear
				py[ineuron] = sum;
				py_derivative[ineuron] = steepness;
				break;
			case 1:		//sigmoid
				sum = 1/(1+exp(-2*sum));
				py[ineuron] = sum;
				py_derivative[ineuron] = 2*steepness*sum*(1-sum);
				break;
			case 2:		//symmetric sigmoid
				sum = 2/(1+exp(-2*sum)) - 1;
				py[ineuron] = sum;
				py_derivative[ineuron] = steepness*(1-sum*sum);
				break;
			}
		}
		ianterior1st = icurrent1st;
	}
}

void CNeuralNetwork::ForwardPropagationWithoutDerivative()
{
	int i, j, k;
	int ineuron;			//neuron index
	int iactivation;		//activation function type
	int ncurrent1;			//number of neurons in current layer, excluding bias neuron
	int nanterior;			//number of neurons in anterior layer
	int icurrent1st;		//first neuron index in the current layer
	int ianterior1st = 0;	//first neuron index in the anterior layer
	int iconn = 0;			//connection index
	double steepness;		//steepness
	double sum;
	for (i=1; i<nlayer; i++)
	{
		nanterior = pnneuron_layer[i-1];
		ncurrent1 = pnneuron_layer[i] - 1;
		icurrent1st = ianterior1st + nanterior;
		if (i<nlayer-1)
		{
			iactivation = iactivation_hidden;
			steepness = steepness_hidden;
		}
		else
		{
			iactivation = iactivation_output;
			steepness = steepness_output;
		}
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			sum = 0;
			for (k=0; k<nanterior; k++)
				sum += py[ianterior1st+k]*pweight[iconn++];
			sum *= steepness;
			switch (iactivation)
			{
			case 0:		//linear
				py[ineuron] = sum;
				break;
			case 1:		//sigmoid
				sum = 1/(1+exp(-2*sum));
				py[ineuron] = sum;
				break;
			case 2:		//symmetric sigmoid
				sum = 2/(1+exp(-2*sum)) - 1;
				py[ineuron] = sum;
				break;
			}
		}
		ianterior1st = icurrent1st;
	}
}

void CNeuralNetwork::ForwardPropagationWith2ndDerivative()
{
	int i, j, k;
	int ineuron;			//neuron index
	int iactivation;		//activation function type
	int ncurrent1;			//number of neurons in current layer, excluding bias neuron
	int nanterior;			//number of neurons in anterior layer
	int icurrent1st;		//first neuron index in the current layer
	int ianterior1st = 0;	//first neuron index in the anterior layer
	int iconn = 0;			//connection index
	double steepness;		//steepness
	double sum;
	for (i=1; i<nlayer; i++)
	{
		nanterior = pnneuron_layer[i-1];
		ncurrent1 = pnneuron_layer[i] - 1;
		icurrent1st = ianterior1st + nanterior;
		if (i<nlayer-1)
		{
			iactivation = iactivation_hidden;
			steepness = steepness_hidden;
		}
		else
		{
			iactivation = iactivation_output;
			steepness = steepness_output;
		}
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			sum = 0;
			for (k=0; k<nanterior; k++)
				sum += py[ianterior1st+k]*pweight[iconn++];
			sum *= steepness;
			switch (iactivation)
			{
			case 0:		//linear
				py[ineuron] = sum;
				py_derivative[ineuron] = steepness;
				py_2nd_derivative[ineuron] = 0;
				break;
			case 1:		//sigmoid
				sum = 1/(1+exp(-2*sum));
				py[ineuron] = sum;
				py_derivative[ineuron] = 2*steepness*sum*(1-sum);
				py_2nd_derivative[ineuron] = 4*steepness*steepness*sum*(1-sum)*(1-2*sum);
				break;
			case 2:		//symmetric sigmoid
				sum = 2/(1+exp(-2*sum)) - 1;
				py[ineuron] = sum;
				py_derivative[ineuron] = steepness*(1-sum*sum);
				py_2nd_derivative[ineuron] = 2*steepness*steepness*sum*(1-sum*sum);
				break;
			}
		}
		ianterior1st = icurrent1st;
	}
}

void CNeuralNetwork::BackwardPropagation(double* pout)
{
	//Assume ForwardPropagation() has just been called
	int i, j, k;
	int ineuron;					//index of current neuron
	int ineuron_post;				//index of a posterior neuron
	int ncurrent1;					//number of neurons in current layer excluding bias neuron
	int nposterior1;				//number of neurons in the posterior layer excluding bias neuron
	int nanterior;					//numver of neurons in the anterior layer
	int icurrent1st;				//index of the 1st neuron in the current layer
	int iposterior1st;				//index of the 1st neuron in the posterior layer
	int ianterior1st;				//index of the 1st neuron in the anterior layer
	int iconn;						//connection index
	double sum;						//used for summation
	double err;						//difference between the given and predicted output
	//output layer delta and error
	icurrent1st = nneuron - noutput - 1;
	error_pair = 0;
	for (j=0; j<noutput; j++)
	{
		ineuron = icurrent1st + j;
		err = pout[j] - py[ineuron];
		error_pair += err*err;
		pdelta[ineuron] = err*py_derivative[ineuron];
	}
	error_pair /= 2;
	//hidden layer delta
	for (i=nlayer-2; i>0; i--)
	{
		ncurrent1 = pnneuron_layer[i] - 1;
		nposterior1 = pnneuron_layer[i+1] - 1;
		iposterior1st = icurrent1st;
		icurrent1st -= ncurrent1 + 1;
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			sum = 0;
			for (k=0; k<nposterior1; k++)
			{
				ineuron_post = iposterior1st + k;
				iconn = piconn_anterior[ineuron_post] + j;
				sum += pweight[iconn]*pdelta[ineuron_post];
			}
			pdelta[ineuron] = sum*py_derivative[ineuron];
		}
	}
	//calculate weight derivative
	iconn = 0;
	ianterior1st = 0;
	for (i=1; i<nlayer; i++)
	{
		nanterior = pnneuron_layer[i-1];
		ncurrent1 = pnneuron_layer[i] - 1;
		icurrent1st = ianterior1st + nanterior;
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			for (k=0; k<nanterior; k++)
			{
				pweight_derivative_new[iconn] -= pdelta[ineuron]*py[ianterior1st+k];
				iconn++;
			}
		}
		ianterior1st = icurrent1st;
	}
	//assign new pair error
	error_batch += error_pair;
}

void CNeuralNetwork::BackwardPropagationWithoutWeightDerivative(double* pout)
{
	//Assume ForwardPropagation() has just been called
	int i, j, k;
	int ineuron;					//index of current neuron
	int ineuron_post;				//index of a posterior neuron
	int ncurrent1;					//number of neurons in current layer excluding bias neuron
	int nposterior1;				//number of neurons in the posterior layer excluding bias neuron
	int icurrent1st;				//index of the 1st neuron in the current layer
	int iposterior1st;				//index of the 1st neuron in the posterior layer
	int iconn;						//connection index
	double sum;						//used for summation
	double err;						//difference between the given and predicted output
	//output layer delta and error
	icurrent1st = nneuron - noutput - 1;
	for (j=0; j<noutput; j++)
	{
		ineuron = icurrent1st + j;
		err = pout[j] - py[ineuron];
		pdelta[ineuron] = err*py_derivative[ineuron];
	}
	//hidden layer delta
	for (i=nlayer-2; i>0; i--)
	{
		ncurrent1 = pnneuron_layer[i] - 1;
		nposterior1 = pnneuron_layer[i+1] - 1;
		iposterior1st = icurrent1st;
		icurrent1st -= ncurrent1 + 1;
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			sum = 0;
			for (k=0; k<nposterior1; k++)
			{
				ineuron_post = iposterior1st + k;
				iconn = piconn_anterior[ineuron_post] + j;
				sum += pweight[iconn]*pdelta[ineuron_post];
			}
			pdelta[ineuron] = sum*py_derivative[ineuron];
		}
	}
}

void CNeuralNetwork::UpdateConnectionData()
{
	//update weight and other data for connections
	int i, j, k;
	int ineuron;					//index of current neuron
	int ncurrent1;					//number of neurons in current layer excluding bias neuron
	int nanterior;					//numver of neurons in the anterior layer
	int icurrent1st;				//index of the 1st neuron in the current layer
	int ianterior1st;				//index of the 1st neuron in the anterior layer
	int iconn;						//connection index
	double weight_derivative_new;	//new weight derivative
	double product;					//a product of two numbers
	double step_size;				//step size
	double minus_sign;				//-sign function
	iconn = 0;
	ianterior1st = 0;
	for (i=1; i<nlayer; i++)
	{
		nanterior = pnneuron_layer[i-1];
		ncurrent1 = pnneuron_layer[i] - 1;
		icurrent1st = ianterior1st + nanterior;
		for (j=0; j<ncurrent1; j++)
		{
			ineuron = icurrent1st + j;
			for (k=0; k<nanterior; k++)
			{
				weight_derivative_new = pweight_derivative_new[iconn];
				switch (itrain_method)
				{
				case 0:	//classical method
					pweight_change[iconn] = coeff_momentum*pweight_change[iconn] - rate_learn*weight_derivative_new;
					pweight[iconn] += pweight_change[iconn];
					break;
				case 1:	//RPROP by Reidmiller
					product = pweight_derivative[iconn]*weight_derivative_new;
					if (product>0)
					{
						step_size = pweight_step_size[iconn]*eta_plus;
						pweight_step_size[iconn] = step_size>delta_max ? delta_max : step_size;
						minus_sign = weight_derivative_new>0 ? -1 : (weight_derivative_new<0 ? 1 : 0);
						pweight_change[iconn] = minus_sign*pweight_step_size[iconn];
						pweight[iconn] += pweight_change[iconn];
						pweight_derivative[iconn] = weight_derivative_new;
					}
					else
					{
						if (product<0)
						{
							step_size = pweight_step_size[iconn]*eta_minus;
							pweight_step_size[iconn] = step_size<delta_min ? delta_min : step_size;
							pweight_derivative[iconn] = 0;
						}
						else		//product==0
						{
							//does not change step size
							minus_sign = weight_derivative_new>0 ? -1 : (weight_derivative_new<0 ? 1 : 0);
							pweight_change[iconn] = minus_sign*pweight_step_size[iconn];
							pweight[iconn] += pweight_change[iconn];
							pweight_derivative[iconn] = weight_derivative_new;
						}
					}
					break;
				case 2:		//iRPROP by Igel and Husken
					product = pweight_derivative[iconn]*weight_derivative_new;
					if (product>0)
					{
						step_size = pweight_step_size[iconn]*eta_plus;
						pweight_step_size[iconn] = step_size>delta_max ? delta_max : step_size;
						minus_sign = weight_derivative_new>0 ? -1 : (weight_derivative_new<0 ? 1 : 0);
						pweight_change[iconn] = minus_sign*pweight_step_size[iconn];
						pweight[iconn] += pweight_change[iconn];
						pweight_derivative[iconn] = weight_derivative_new;
					}
					else
					{
						if (product<0)
						{
							step_size = pweight_step_size[iconn]*eta_minus;
							pweight_step_size[iconn] = step_size<delta_min ? delta_min : step_size;
							if (error_batch>error_batch_old)
							{
								pweight[iconn] -= pweight_change[iconn];
								pweight_change[iconn] = 0;
							}
							pweight_derivative[iconn] = 0;	//tested sould set to zero, otherwise not always converge
						}
						else		//product==0
						{
							//does not change step size
							minus_sign = weight_derivative_new>0 ? -1 : (weight_derivative_new<0 ? 1 : 0);
							pweight_change[iconn] = minus_sign*pweight_step_size[iconn];
							pweight[iconn] += pweight_change[iconn];
							pweight_derivative[iconn] = weight_derivative_new;
						}
					}
					break;
				}
				iconn++;
			}
		}
		ianterior1st = icurrent1st;
	}
}

void CNeuralNetwork::Predict(double* pin, double* pout)
{
	int ioutput1st = nneuron - noutput - 1;		//first neuron index in output layer
	SetInputParameters(pin);
	ForwardPropagation();
	//get output
	for (int i=0; i<noutput; i++)
		pout[i] = py[ioutput1st+i];
}

void CNeuralNetwork::TrainDataPair(double* pin, double* pout)
{
	ClearNewWeightDerivative();
	SetInputParameters(pin);
	ForwardPropagation();
	BackwardPropagation(pout);
	UpdateConnectionData();
}

void CNeuralNetwork::TrainDataSetOnline(int npair, double** ppinout)
{
	//a row in ppinout contain a data pair with input parameters followed by output parameters
	int i;
	int iepoch;
	double* pin;
	double* pout;
	for (iepoch=0; iepoch<nepoch_max; iepoch++)
	{
		error_batch = 0;
		for (i=0; i<npair; i++)
		{
			pin = ppinout[i];
			pout = pin + ninput;
			TrainDataPair(pin, pout);
			error_batch += error_pair;
		}
		error_batch /= npair;
		if (error_batch<error_stop)
		{
			printf("Reached desired error.  Error=%lg\n",error_batch);
			break;
		}
		if (iepoch%10000==0)
			printf("Epoch=%d. Error=%lg\n",iepoch,error_batch);
	}
	printf("Epoch=%d. Error=%lg\n",iepoch,error_batch);
}

void CNeuralNetwork::TrainDataSetBatch(int npair, double** ppinout)
{
	//a row in ppinout contain a data pair with input parameters followed by output parameters
	int i;
	int iepoch;
	double* pin;
	double* pout;
	for (iepoch=0; iepoch<nepoch_max; iepoch++)
	{
		error_batch_old = error_batch;
		error_batch = 0;
		ClearNewWeightDerivative();
		for (i=0; i<npair; i++)
		{
			pin = ppinout[i];
			pout = pin + ninput;
			SetInputParameters(pin);
			ForwardPropagation();
			BackwardPropagation(pout);
		}
		UpdateConnectionData();
		//error_batch /= npair;
		if (error_batch/npair<error_stop)
			break;
		if (iepoch%1000==0)
		{
			printf("At Epoch=%d, Average Error=%lg.\n",iepoch,error_batch/npair);
		}
	}
	printf("At Epoch=%d, Average Error=%lg.\n",iepoch,error_batch/npair);
}

void CNeuralNetwork::TrainDataSet(int npair, double** ppinout)
{
	if (itrain_method)
		TrainDataSetBatch(npair, ppinout);
	else
		TrainDataSetOnline(npair, ppinout);
}

void CNeuralNetwork::CalcMeanSigmaForInputOutputData(int npair, double** ppinout)
{
	int i, j;
	int ninout = ninput + noutput;
	double sum;
	double dx;
	for (j=0; j<ninput+noutput; j++)
	{
		sum = 0;
		for (i=0; i<npair; i++)
			sum += ppinout[i][j];
		pmean[j] = sum/(double)npair;
	}
	for (j=0; j<ninout; j++)
	{
		sum = 0;
		for (i=0; i<npair; i++)
		{
			dx = ppinout[i][j] - pmean[j];
			sum += dx*dx;
		}
		psigma[j] = sqrt(sum/(double)(npair-1));
	}
}

void CNeuralNetwork::ScaleInputOutputData(int npair, double** ppinout)
{
	int i, j;
	int ninout = ninput + noutput;
	for (i=0; i<npair; i++)
	{
		for (j=0; j<ninout; j++)
			ppinout[i][j] = (ppinout[i][j]-pmean[j])/psigma[j];
	}
}

void CNeuralNetwork::ScaleInputData(double* pin)
{
	int j;
	for (j=0; j<ninput; j++)
		pin[j] = (pin[j]-pmean[j])/psigma[j];
}

void CNeuralNetwork::UnscaleOutputData(double* pout)
{
	int j;
	for (j=0; j<noutput; j++)
		pout[j] = pout[j]*psigma[ninput+j] + pmean[ninput+j];
}

int CNeuralNetwork::GetHessianNonzeroCount()
{
	int ncount = nconnection*(nconnection+1)/2;
	ncount -= noutput*(noutput-1)/2*pnneuron_layer[1]*pnneuron_layer[1];
	return ncount;
}

void CNeuralNetwork::GetHessianNonzeroIndices(int* pirow, int* picol)
{
	int j, k, ilayer0, ilayer1;
	int n = 0;
	for (j=0; j<nconnection; j++)
	{
		ilayer0 = pilayer_conn[j];
		for (k=0; k<=j; k++)
		{
			ilayer1 = pilayer_conn[k];
			if (ilayer0==1 && ilayer1==1 && pineuron_conn_to[j]!=pineuron_conn_to[k])
				continue;
			else		//nonzero
			{
				pirow[n] = j;
				picol[n] = k;
				n++;
			}
		}
	}
	//assert that n == nconnection*(1+nconnection)/2 - noutput*(noutput-1)/2*pnneuron_layer[1]*pnneuron_layer[1];
	if (n!=nconnection*(1+nconnection)/2 - noutput*(noutput-1)/2*pnneuron_layer[1]*pnneuron_layer[1])
		printf("incorrect nonzero emement count!\n");
}

double CNeuralNetwork::CalcBatchErrorUsingGivenWeights(const double* pw, CDataCollection* pdc)
{
	//evaluation error for IPOPT training
	int i, j;
	int icurrent1st;
	int ineuron;
	int npair = pdc->npair;
	double err;
	double* pin;
	double* pout;
	double** ppdata = pdc->ppdata;
	//assign weights
	for (i=0; i<nconnection; i++)
		pweight[i] = pw[i];
	//calculate batch error
	error_batch = 0;
	for (i=0; i<npair; i++)
	{
		pin = ppdata[i];
		pout = pin + ninput;
		SetInputParameters(pin);
		ForwardPropagationWithoutDerivative();
		icurrent1st = nneuron - noutput - 1;
		error_pair = 0;
		for (j=0; j<noutput; j++)
		{
			ineuron = icurrent1st + j;
			err = pout[j] - py[ineuron];
			error_pair += err*err;
		}
		error_pair /= 2;
		error_batch += error_pair;
	}
	return error_batch;
}

void CNeuralNetwork::CalcBatchGradientUsingGivenWeights(const double* pw, CDataCollection* pdc, double* pg)
{
	//evaluation gradient with respect to weights for IPOPT training
	int i;
	int npair = pdc->npair;
	double* pin;
	double* pout;
	double** ppdata = pdc->ppdata;
	//assign weights
	for (i=0; i<nconnection; i++)
		pweight[i] = pw[i];
	//reset gradients
	ClearNewWeightDerivative();
	//calculate the weight derivative and accumulate to pweight_derivative_new
	for (i=0; i<npair; i++)
	{
		pin = ppdata[i];
		pout = pin + ninput;
		SetInputParameters(pin);
		ForwardPropagation();
		BackwardPropagation(pout);
	}
	//assign to pg
	for (i=0; i<nconnection; i++)
		pg[i] = pweight_derivative_new[i];
}

void CNeuralNetwork::CalcBatchHessianUsingGivenWeights(const double* pw, CDataCollection* pdc, double* ph)
{
	//evaluation Hessian matrix with respect to weights for IPOPT training
	//currently implemeted for one hidden layer only
	int i, j, k, n, m;
	int ineuron_from0, ineuron_from1;
	int ineuron_to0, ineuron_to1;
	int ilayer0, ilayer1;
	int ineuron_output;
	int npair = pdc->npair;
	int nelement = GetHessianNonzeroCount();		//Hessian nonzero element count
	double sum, sum1;
	double* pin;
	double* pout;
	double** ppdata = pdc->ppdata;
	double* phm = new double[nneuron];
	//assign weights
	for (i=0; i<nconnection; i++)
		pweight[i] = pw[i];
	//reset Hessians
	for (i=0; i<nelement; i++)
		ph[i] = 0;
	//calculate the weight derivative and accumulate to pweight_derivative_new
	error_batch = 0;
	for (i=0; i<npair; i++)
	{
		pin = ppdata[i];
		pout = pin + ninput;
		SetInputParameters(pin);
		ForwardPropagationWith2ndDerivative();
		BackwardPropagation(pout);
		//calculate Hm at outlet
		for (j=0; j<noutput; j++)
		{
			ineuron_to0 = nneuron - noutput - 1 + j;
			phm[ineuron_to0] = py_2nd_derivative[ineuron_to0]*(py[ineuron_to0]-pout[j]) + py_derivative[ineuron_to0]*py_derivative[ineuron_to0];
		}
		//calculate Hessian elements
		n = 0;
		for (j=0; j<nconnection; j++)
		{
			ilayer0 = pilayer_conn[j];
			ineuron_from0 = pineuron_conn_from[j];
			ineuron_to0 = pineuron_conn_to[j];
			for (k=0; k<=j; k++)
			{
				ilayer1 = pilayer_conn[k];
				ineuron_from1 = pineuron_conn_from[k];
				ineuron_to1 = pineuron_conn_to[k];
				if (ilayer0==1)
				{
					if (ilayer1==1)		//both weights in the second layer
					{
						if (ineuron_to0 == ineuron_to1)		//delta(m,m')=1
							ph[n++] += py[ineuron_from0]*py[ineuron_from1]*phm[ineuron_to0];
					}
					else				//one weight in each layer, ilayer0==1 and ilayer1==0
					{
						sum = py[ineuron_from0]*pweight[piconn_anterior[ineuron_to0]+ineuron_to1-ninput-1]*phm[ineuron_to0];
						if (ineuron_to1==ineuron_from0)
							sum -= pdelta[ineuron_to0];
						ph[n++] += py[ineuron_from1]*py_derivative[ineuron_to1]*sum;
					}
				}
				else		//both weights in the first layer
				{
					sum = 0;
					for (m=0; m<noutput; m++)
					{
						ineuron_output = m + nneuron - noutput - 1;
						sum += phm[ineuron_output]*pweight[piconn_anterior[ineuron_output]+ineuron_to0-ninput-1]*pweight[piconn_anterior[ineuron_output]+ineuron_to1-ninput-1];
					}
					sum *= py_derivative[ineuron_to0]*py_derivative[ineuron_to1];
					sum1 = 0;
					if (ineuron_to0==ineuron_to1)
					{
						for (m=0; m<noutput; m++)
						{
							ineuron_output = m + nneuron - noutput - 1;
							sum1 -= pdelta[ineuron_output]*pweight[piconn_anterior[ineuron_output]+ineuron_to0-ninput-1];
						}
						sum1 *= py_2nd_derivative[ineuron_to0];
					}
					ph[n++] = py[ineuron_from0]*py[ineuron_from1]*(sum + sum1);
				}
			}
		}
	}
	delete [] phm;
}

void CNeuralNetwork::InitUniformWeights(double w)
{
	int i;
	for (i=0; i<nconnection; i++)
		pweight[i] = w;
}

void CNeuralNetwork::InitWeightsForIpopt(double* pw)
{
	//it was found that uniform small weight help bananced reduction
	int i;
	for (i=0; i<nconnection; i++)
		pw[i] = weight_init;
}

void CNeuralNetwork::WriteANNData(FILE* pf)
{
	int i;
	int nhid = nlayer - 2;
	fprintf(pf,"%d\t//number of input\n",ninput);
	fprintf(pf,"%d\t//number of output\n",noutput);
	fprintf(pf,"%d\t//number of hidden layers\n",nhid);
	for (i=0; i<nhid; i++)
		fprintf(pf,"%d\t",pnneuron_layer[i+1]-1);
	fprintf(pf,"number of neurons in hidden layer excluding bias neuron\n");
	fprintf(pf,"%d\t//iactivation_hidden\n",iactivation_hidden);
	fprintf(pf,"%d\t//iactivation_output\n",iactivation_output);
	fprintf(pf,"%lg\t//steepness_hidden\n",steepness_hidden);
	fprintf(pf,"%lg\t//steepness_output\n",steepness_output);
	//write weights
	fprintf(pf,"//list of weights for %d connections\n",nconnection);
	for (i=0; i<nconnection; i++)
		fprintf(pf,"%lg\n",pweight[i]);
	//write mean and sigma of input and output data
	for (i=0; i<ninput+noutput; i++)
		fprintf(pf,"%lg\t",pmean[i]);
	fprintf(pf,"//mean of training data\n");
	for (i=0; i<ninput+noutput; i++)
		fprintf(pf,"%lg\t",psigma[i]);
	fprintf(pf,"//standard deviation of training data\n");
}

void CNeuralNetwork::ReadANNData(FILE* pf)
{
	int i;
	int nin, nout, nhid;
	int* pnneuron_hid;
	char cline[500];
	fscanf(pf,"%d",&nin);
	fgets(cline,499,pf);
	fscanf(pf,"%d",&nout);
	fgets(cline,499,pf);
	fscanf(pf,"%d",&nhid);
	fgets(cline,499,pf);
	pnneuron_hid = new int [nhid];
	for (i=0; i<nhid; i++)
		fscanf(pf,"%d",&pnneuron_hid[i]);
	fgets(cline,499,pf);

	//create network struction
	SetNetworkStructure(nin,nout,nhid,pnneuron_hid);
	
	fscanf(pf,"%d",&iactivation_hidden);
	fgets(cline,499,pf);
	fscanf(pf,"%d",&iactivation_output);
	fgets(cline,499,pf);
	fscanf(pf,"%lg",&steepness_hidden);
	fgets(cline,499,pf);
	fscanf(pf,"%lg",&steepness_output);
	fgets(cline,499,pf);
	fgets(cline,499,pf);
	for (i=0; i<nconnection; i++)
		fscanf(pf,"%lg",&pweight[i]);
	//read mean and sigma of input and output data
	for (i=0; i<ninput+noutput; i++)
		fscanf(pf,"%lg",&pmean[i]);
	fgets(cline,499,pf);
	for (i=0; i<ninput+noutput; i++)
		fscanf(pf,"%lg",&psigma[i]);
	fgets(cline,499,pf);
}

void CNeuralNetwork::WriteANNMatlabFile(FILE* pf, int iann)
{
	//iann: zero-based ANN index, default is 0. For DABNet, multiple ANN's are used, iann varies from 0 to noutput-1
	int i;
	int nhid = nlayer - 2;
	iann++;		//convert to 1-based array index for MATLAB
	fprintf(pf,"NN(%d).nx = %d;\n",iann,ninput);
	fprintf(pf,"NN(%d).ny = %d;\n",iann,noutput);
	fprintf(pf,"NN(%d).nhid = %d;\n",iann,nhid);
	for (i=0; i<nhid; i++)
		fprintf(pf,"NN(%d).nneuron_hid = %d;\n",iann,pnneuron_layer[i+1]-1);
	fprintf(pf,"NN(%d).iactivation_hidden = %d;\n",iann,iactivation_hidden);
	fprintf(pf,"NN(%d).iactivation_output = %d;\n",iann,iactivation_output);
	fprintf(pf,"NN(%d).steepness_hidden = %lg;\n",iann,steepness_hidden);
	fprintf(pf,"NN(%d).steepness_output = %lg;\n",iann,steepness_output);
	//weights
	for (i=0; i<nconnection; i++)
		fprintf(pf,"NN(%d).weight(%d) = %lg;\n",iann,i+1,pweight[i]);
	//write mean and sigma of input and output data
	for (i=0; i<ninput; i++)
		fprintf(pf,"NN(%d).mean_in(%d) = %lg;\n",iann,i+1,pmean[i]);
	for (i=0; i<noutput; i++)
		fprintf(pf,"NN(%d).mean_out(%d) = %lg;\n",iann,i+1,pmean[i+ninput]);
	for (i=0; i<ninput; i++)
		fprintf(pf,"NN(%d).sigma_in(%d) = %lg;\n",iann,i+1,psigma[i]);
	for (i=0; i<noutput; i++)
		fprintf(pf,"NN(%d).sigma_out(%d) = %lg;\n",iann,i+1,psigma[i+ninput]);
}

PyObject* CNeuralNetwork::GetAnnAsTuple()
{
	int i, icount;
	int nhid = nlayer - 2;
	int nsize = 8 + nhid + nconnection + 2*(ninput + noutput);
	PyObject* obj_result = PyTuple_New(nsize);
	PyTuple_SetItem(obj_result, 0, Py_BuildValue("i", ninput));
	PyTuple_SetItem(obj_result, 1, Py_BuildValue("i", noutput));
	PyTuple_SetItem(obj_result, 2, Py_BuildValue("i", nhid));
	icount = 3;
	for (i=0; i<nhid; i++)
	{
		PyTuple_SetItem(obj_result, icount, Py_BuildValue("i", pnneuron_layer[i+1]-1));
		icount++;
	}
	PyTuple_SetItem(obj_result, icount++, Py_BuildValue("i", iactivation_hidden));
	PyTuple_SetItem(obj_result, icount++, Py_BuildValue("i", iactivation_output));
	PyTuple_SetItem(obj_result, icount++, Py_BuildValue("d", steepness_hidden));
	PyTuple_SetItem(obj_result, icount++, Py_BuildValue("d", steepness_output));
	PyTuple_SetItem(obj_result, icount++, Py_BuildValue("i", nconnection));
	for (i=0; i<nconnection; i++)
		PyTuple_SetItem(obj_result, icount++, Py_BuildValue("d", pweight[i]));
	//write mean and sigma of input and output data
	for (i=0; i<ninput+noutput; i++)
		PyTuple_SetItem(obj_result, icount++, Py_BuildValue("d", pmean[i]));
	for (i=0; i<ninput+noutput; i++)
		PyTuple_SetItem(obj_result, icount++, Py_BuildValue("d", psigma[i]));
	return obj_result;
}