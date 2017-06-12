//NeuralNetwork.h

#ifndef _NEURALNETWORK_H_
#define _NEURALNETWORK_H_

#include "DataCollection.h"
#include "Python.h"

#ifndef NULL
#define NULL 0
#endif

class CNeuralNetwork
{
private:
	int irand_seed;					//seeding method for random number generator, 0=using zero, 1=current time
	int itrain_method;				//training method, 0=classical, 1=iRPROP by Reidmiller, 2=iRPROP by Igel and Husken
	int ninput;						//number of input parameters
	int noutput;					//number of output parameters
	int nneuron;					//total number of neurons including a bias neuron in each layer
	int nconnection;				//total number of connections
	int nlayer;						//number of layers including input and output layers
	int iactivation_hidden;			//activation function type for hidden layers
	int iactivation_output;			//activation function type for output layers
	int nepoch_max;					//maximum number of epoches for training
	int* pnneuron_layer;			//number of neurons in each layer including the bias neuron [nlayer]
	int* piconn_anterior;			//index of the first anterior connection [nneuron]
	int* pineuron_conn_from;		//index of neuron the connection is from [nconnection]
	int* pineuron_conn_to;			//index of neuron the connection is to [nconnection]
	int* pilayer_conn;				//layer index of connection, 0=between input and 1st hidden, 1=between 1st hidden and 2nd hidden or output [nconnection]
	double weight_init;				//initial weight in case of uniform weight initialization
	double rate_learn;				//learning rate
	double coeff_momentum;			//momentum coefficient
	double delta_min;				//minimum delta
	double delta_max;				//maximum delta
	double delta0;					//initial delta
	double eta_minus;				//delta decreasing factor
	double eta_plus;				//delta increading factor
	double steepness_hidden;		//steepness of hidden layers
	double steepness_output;		//steepness of output layers
	double error_pair;				//error for single data pair
	double error_batch;				//error for the entire batch of data pairs
	double error_batch_old;			//error for the entire batch of data pairs in previous epoch
	double error_stop;				//error for stopping training
	double* py;						//array of neuron output [nneuron]
	double* py_derivative;			//derivative of y [nneuron]
	double* py_2nd_derivative;		//2nd derivative of y [nneuron]
	double* pdelta;					//array of error signal [nneuron]
	double* pweight;				//array of weights [nconnection]
	double* pweight_derivative;		//array of weight derivative [nconnection]
	double* pweight_derivative_new;	//array of new weight derivative [nconnection], needed for batch training
	double* pweight_step_size;		//array of weight step size [nconnection]
	double* pweight_change;			//array of change of weight [nconnection]
	double* pmean;					//array of mean values of input and output data [ninput+noutput]
	double* psigma;					//array of standard deviation of input and output data [ninput+noutput]

	void AllocateIntArrays();
	void DeleteIntArrays();
	void AllocateDoubleArrays();
	void DeleteDoubleArrays();
	void SetInputParameters(double* pin) {for (int i=0; i<ninput; i++) py[i]=pin[i];}
	void ClearNewWeightDerivative() {for (int i=0; i<nconnection; i++) pweight_derivative_new[i] = 0;}
	void ForwardPropagation();
	void ForwardPropagationWithoutDerivative();
	void ForwardPropagationWith2ndDerivative();
	void BackwardPropagation(double* pout);
	void BackwardPropagationWithoutWeightDerivative(double* pout);
	void UpdateConnectionData();
	void TrainDataPair(double* pin, double* pout);
	void TrainDataSetOnline(int npair, double** ppinout);
	void TrainDataSetBatch(int npair, double** ppinout);

public:
	CNeuralNetwork();
	virtual ~CNeuralNetwork();
	void SetRandomSeed(int i) {irand_seed = i;}
	void SetTrainMethod(int i) {itrain_method = i;}
	void SetNetworkStructure(int nin, int nout, int nlayer_hid, int* pnneuron_hid);
	void SetHiddenLayerActivationType(int i) {iactivation_hidden = i;}
	void SetOutputLayerActivationType(int i) {iactivation_output = i;}
	void SetHiddenLayerSteepness(double s) {steepness_hidden = s;}
	void SetOutputLayerSteepness(double s) {steepness_output = s;}
	void SetMaximumNumberOfEpoches(int n) {nepoch_max = n;}
	void SetWeightForInitialization(double w) {weight_init = w;}
	void SetLearningRate(double r) {rate_learn = r;}
	void SetMomentumCoefficient( double c) {coeff_momentum = c;}
	void SetStopError(double e) {error_stop = e;}
	void SetDefaultMeanSigma();
	double GetDataPairError() {return error_pair;}
	double GetBatchError() {return error_batch;}
	void Predict(double* pin, double* pout);
	void TrainDataSet(int npair, double** ppinout);
	void CalcMeanSigmaForInputOutputData(int npair, double** ppinout);
	void ScaleInputOutputData(int npair, double** ppinout);
	void ScaleInputData(double* pin);
	void UnscaleOutputData(double* pout);
	int GetNeuronCountOfFirstHiddenLayerExcludingBias() {return pnneuron_layer[1]-1;}
	int GetNumberOfWeights() {return nconnection;}
	double* GetWeightPointer() {return pweight;}
	double* GetSigmaPointer() {return psigma;}
	int GetHessianNonzeroCount();
	void GetHessianNonzeroIndices(int* pirow, int* picol);
	double CalcBatchErrorUsingGivenWeights(const double* pw, CDataCollection* pdc);
	void CalcBatchGradientUsingGivenWeights(const double* pw, CDataCollection* pdc, double* pg);
	void CalcBatchHessianUsingGivenWeights(const double* pw, CDataCollection* pdc, double* ph);
	void InitUniformWeights(double w);
	void InitWeightsForIpopt(double* pw);
	void WriteANNData(FILE* pf);
	void ReadANNData(FILE* pf);
	void WriteANNMatlabFile(FILE* pf, int iann=0);
	PyObject* GetAnnAsTuple();
};
#endif