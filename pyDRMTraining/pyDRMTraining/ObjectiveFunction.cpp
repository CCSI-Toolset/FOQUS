//ObjectiveFunction.cpp
#include "ObjectiveFunction.h"

CObjectiveFunction::CObjectiveFunction()
{
	ncount = 0;
}

CObjectiveFunction::~CObjectiveFunction()
{
}

double CObjectiveFunction::CalcObjectiveFunction(double* pvar)
{
	//if 2 poles for each input, pvar contains the 1st pole followed by the 2nd pole for each input
	int i, j;
	int ninput = pmodel->ninput;
	//assign pvar to pole_list
	printf("Trying Laguerre pole values at [");
	j = 0;
	if (pmodel->ipole_opt==1 || pmodel->ipole_opt==2)
	{
		for (i=0; i<ninput; i++)
		{
			pmodel->pole_list[i] = pvar[j++];
			printf("%lg ", pmodel->pole_list[i]);
		}
	}
	if (pmodel->ipole_opt==1 || pmodel->ipole_opt==3)
	{
		for (i=0; i<ninput; i++)
		{
			if (pmodel->ipole2_list[i])
			{
				pmodel->pole2_list[i] = pvar[j++];
				printf("%lg ", pmodel->pole2_list[i]);
			}
		}
	}
	printf("]\n");
	pmodel->UpdateLaguerreStateSpaceList();
	pmodel->ProcessIdentificationDataForLaguerreTraining();
	pmodel->TrainLaguerreNeuralNetwork();
	ncount++;
	printf("Objective function has been called for %d times.\n",ncount);
	return pmodel->ann_lag.GetBatchError();
}