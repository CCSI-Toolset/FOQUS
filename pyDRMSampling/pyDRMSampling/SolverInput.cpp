//SolverInput.cpp
#include "SolverInput.h"

CSolverInput::CSolverInput()
{
	ireverse = 1;
	ndim = 2;
	npoint = 3;
	nduration = 1;
	duration0 = 5;
	nstep = 0;
}

CSolverInput::~CSolverInput()
{
}

bool CSolverInput::CheckVariedInputDimension()
{
	int i;
	int ncount = 0;
	int ndim_all = vbvaried.size();
	for (i=0; i<ndim_all; i++)
	{
		if (vbvaried[i])
			ncount++;
	}
	return ncount==ndim;
}

void CSolverInput::GenerateTrainingSequence()
{
	//based on the size of the problem estimate the number of tries
	int ntry = 10*npoint*nduration;
	ts.SetSizeAll(ndim, npoint, nduration);
	ts.SetDefaultStartingPoint();
	ts.SelectBestSampling(ntry);
}

void CSolverInput::PrepareSequenceVectorForACMInputArray()
{
	//vsequence is the array to be passed to MATLAB engine
	int i, j, k, m, n;
	int jstart;
	int ndim_all = vbvaried.size();
	int* piall2sel;	//index mapping from all to selected [ndim_all]
	int** ppx;		//pointer to the LHS ppx, the integer sample points
	double* px;		//parameter value [ndim]
	double* px_all;	//initial or default values for all parameters [ndim_all]
	double* pdx;	//interval between two neighboring points [ndim]
	double* plower;	//lower value [ndim]
	double* pupper;	//upper value [ndim]
	piall2sel = new int [ndim_all];
	px = new double [ndim];
	px_all = new double [ndim_all];
	pdx = new double [ndim];
	plower = new double [ndim];
	pupper = new double [ndim];
	vsequence.clear();
	//assign piall2sel
	j = 0;
	for (i=0; i<ndim_all; i++)
	{
		piall2sel[i] = -1;
		px_all[i] = vxdefault[i];
		if (vbvaried[i])
			piall2sel[i] = j++;
	}
	j = 0;
	for (i=0; i<ndim_all; i++)
	{
		if (vbvaried[i])
		{
			px[j] = vxdefault[i];
			plower[j] = vxlower[i];
			pupper[j] = vxupper[i];
			j++;
		}
	}
	//evenly spaced distance
	for (i=0; i<ndim; i++)
		pdx[i] = (pupper[i]-plower[i])/(double)(npoint-1);
	CLHS* plhs = ts.GetSampleList();
	//start to prepare sequence array
	nstep = 0;
	//first point is the steady state point
	for (n=0; n<duration0; n++)
	{
		for (m=0; m<ndim_all; m++)
		{
			if (piall2sel[m]==-1)
				vsequence.push_back(px_all[m]);
			else
				vsequence.push_back(px[piall2sel[m]]);
		}
		nstep++;
	}
	//now start loop for each duration, each point, and each time step
	for (i=0; i<nduration; i++)
	{
		ppx = plhs[i].GetLHSPoints();
		for (j=1; j<npoint; j++)	//skip the first point, making the SetxxxStartingPoint() in CTrainingSequence irrelavent
		{
			for (k=0; k<ndim; k++)
			{
				px[k] = ppx[j][k]*pdx[k] + plower[k];
				for (n=0; n<vduration[i]; n++)
				{
					for (m=0; m<ndim_all; m++)
					{
						if (piall2sel[m]==-1)
							vsequence.push_back(px_all[m]);
						else
							vsequence.push_back(px[piall2sel[m]]);
					}
					nstep++;
				}
			}
		}
	}
	//write reverse order
	if (ireverse)
	{
		for (i=nduration-1; i>=0; i--)
		{
			ppx = plhs[i].GetLHSPoints();
			if (i==nduration-1)
				jstart = npoint-2;
			else
				jstart = npoint-1;
			for (j=jstart; j>0; j--)	//excluding the first point
			{
				for (k=0; k<ndim; k++)
				{
					px[k] = ppx[j][k]*pdx[k] + plower[k];
					for (n=0; n<vduration[i]; n++)
					{
						for (m=0; m<ndim_all; m++)
						{
							if (piall2sel[m]==-1)
								vsequence.push_back(px_all[m]);
							else
								vsequence.push_back(px[piall2sel[m]]);
						}
						nstep++;
					}
				}
			}
		}
	}
	delete [] piall2sel;
	delete [] px;
	delete [] px_all;
	delete [] pdx;
	delete [] plower;
	delete [] pupper;
}
