//DabnetInput.h

#ifndef __DABNETINPUT_H__
#define __DABNETINPUT_H__

class CDabnetInput
{
public:
	int ipredict_opt;						//prediction option, 0=Laguerre model, 1=balanced realization model
	int itrain_lag_opt;						//training option for Laguerre neural network, 0=back propagation, 1=IPOPT
	int itrain_red_opt;						//training option for reduced neural network, 0=back propagation, 1=IPOPT
	int iscale_lag_opt;						//Laguerre model ANN input scaling option, 0=no scaling, 1=scaling
	int iscale_red_opt;						//reduced or balanced model ANN input scaling option, 0=no scaling, 1=scaling
	int nmax_iter_ipopt_lag;				//maximum iteration number for Laguerre model IPOPT training
	int nmax_iter_ipopt_red;				//maximum iteration number for reduced model IPOPT training
	int nmax_iter_bp_lag;					//maximum iteration number for Laguerre model BP training
	int nmax_iter_bp_red;					//maximum iteration number for reduced model BP training
	double weight_init;						//uniform weight for initialization of ANN if applied

public:
	CDabnetInput();
	virtual ~CDabnetInput();
	CDabnetInput(const CDabnetInput &t);
	CDabnetInput& operator=(const CDabnetInput& t);
};

#endif