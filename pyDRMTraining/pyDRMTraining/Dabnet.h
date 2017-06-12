//Dabnet.h
#ifndef __DABNET_H__
#define __DABNET_H__

#include <vector>
#include "DabnetInput.h"
#include "DataCollection.h"
#include "LaguerreStateSpace.h"
#include "NeuralNetwork.h"

class CDabnet
{
public:
	int ninput;										//number of inputs
	int noutput;									//number of outputs, currently always 1
	int ioutput;									//zero-based output index of modeled output variables
	int ipole_opt;									//pole value specification option, 0=user specified, 1=code optimized by Simplex
	int nneuron_hid;								//number of neurons in hidden layer
	int ilinear_ann;								//linear activation function in hidden layer of Laguerre and reduced ANNs
	int nstate_lag;									//total number of states of Laguerre models
	int nstate_red;									//total number of states of reduced models
	
	std::vector<int> ipole2_list;					//2-pole flag list
	std::vector<int> ndelay_list;					//delay list
	std::vector<int> norder_list;					//LaguerreStateSpace order list
	std::vector<int> norder2_list;					//2nd LaguerreStateSpace order list
	std::vector<double> pole_list;					//LaguerreStateSpace pole value list
	std::vector<double> pole2_list;					//2nd LaguerreStateSpace pole value list
	std::vector<CLaguerreStateSpace> lss_list;		//LaguerreStateSpace list
	std::vector<CStateSpace> rss_list;				//reduced StateSpace list
	CDabnetInput* pdabnet_input;					//pointer to option and parameter data
	CDataCollection* pid_data;						//pointer to plant identification data in CDRMContainer
	CDataCollection ann_data;						//data for ANN (training or test, Laguerre or reduced)
	CNeuralNetwork ann_lag;							//Laguerre state space based network
	CNeuralNetwork ann_red;							//reduced state space based network

	CDabnet(void);
	virtual ~CDabnet(void);
	void ResizeVectors(int ninput);
	void UpdateTotalLaguerreOrders();
	void CreateLaguerreStateSpaceList();
	void UpdateLaguerreStateSpaceList();
	void ResizeReducedModelStateSpaceList() {rss_list.resize(ninput);}
	void ProcessIdentificationDataForLaguerreTraining();
	void ProcessIdentificationDataForReducedModelTraining();
	void TrainLaguerreNeuralNetworkByBackPropagation();
	void TrainLaguerreNeuralNetworkByIpopt();
	void TrainLaguerreNeuralNetwork();
	void TrainReducedModelNeuralNetworkByBackPropagation();
	void TrainReducedModelNeuralNetworkByIpopt();
	void TrainReducedModelNeuralNetwork();
	void PrepareLaguerreNeuralNetworkWeightMatrices();
	void ReduceLaguerreStateSpace();
	void PredictByLaguerreModel(int np, double** ppin, double** ppout);
	void PredictByReducedModel(int np, double** ppin, double** ppout);
	void CalcMeanAndSigmaOfReducedModelStateVariables(int np, double** ppin, double* pmean, double* psigma);
	void PredictByDRM(int np, double** ppin, double** ppout);
	void WriteReducedModelStateSpaceMatrices(FILE* pf);
	void ReadReducedModelStateSpaceMatrices(FILE* pf);
	void WriteLaguerreModelStateSpaceMatrices(FILE* pf);
	void WriteDRMTextFile(FILE* pf);
	void WriteDRMMatlabFile(FILE* pf);
	void WriteWeightMatrixFile(FILE* pf);
	PyObject* GetDabnetAsTuple();
};

#endif