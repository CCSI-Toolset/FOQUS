#ifndef __LAGUERRESTATESPACE_H__
#define __LAGUERRESTATESPACE_H__

#include "StateSpace.h"
#include "Matrix.h"

class CLaguerreStateSpace : public CStateSpace
{
//currently for single input and single output without D matrix, and use Wang's realization of A=a, B=1, C=sqrt(1-a^2), D=0 for low-pass
//minimum number of states is 2 (at least one low-pass and one all-pass)
public:
	double a;				//1st pole, 1-T/tau_1
	double a2;				//2nd pole, 1-T/tau_2
	int	ndelay;				//number of delays, use the same delay for both Laguerre series
	int nstate2;			//state of the 2nd Laguerre series (nstate = nstart1+nstate2)
	int ipole2;				//flag for 2 poles, 0=false, 1=true
	CMatrix mweight;		//weight matrix from Laguerre neural network
	
	CLaguerreStateSpace(void);
	virtual ~CLaguerreStateSpace(void);
	void CreateUnbalancedStateSpace();
	void PrepareWeightMatrix(int nneuron, double** ppweight, double* psigma, int iscale);
	void RealizeBalancedStateSpace(CStateSpace* pss);
};

#endif