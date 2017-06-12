#ifndef __DATACOLLECTION_H__
#define __DATACOLLECTION_H__

#include <stdio.h>

class CDataCollection
{
//currently for single input and single output without D matrix
public:
	int npair;				//number of data pairs
	int nin;				//number of inputs for each data pair
	int nout;				//number of outputs for each data pair
	double** ppdata;		//data as 2-D array, for each pair, input data followed by output data
	double* pmean;			//mean value
	double* psigma;			//standard deviation
	
	CDataCollection(void);
	virtual ~CDataCollection(void);
	CDataCollection(const CDataCollection &t);
	CDataCollection& operator=(const CDataCollection& t);
	virtual void AllocateMemory();
	virtual void DeleteMemory();
	void SetSize(int np, int ni, int no);
	void AssignInputOutputData(double* pin, double* pout);
	void CalcMeanAndSigma();
	void ScaleInputData();
	void ScaleOutputData();
	void UnscaleInputData();
	void UnscaleOutputData();
};

#endif