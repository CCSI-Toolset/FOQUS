//TrainSequence.cpp
#include <stdlib.h>
#include <math.h>
#include "TrainSequence.h"

CTrainSequence::CTrainSequence()
{
	ndim = 2;
	npoint = 2;
	pistart = NULL;
	plhs = NULL;
}

CTrainSequence::CTrainSequence(int ndi, int np, int ndu)
{
	ndim = ndi;
	npoint = np;
	nduration = ndu;
	pistart = NULL;
	plhs = NULL;
	AllocateArray();
}

CTrainSequence::~CTrainSequence()
{
	DeleteArray();
}

CTrainSequence::CTrainSequence(const CTrainSequence &t)
{
	int i;
	ndim = t.ndim;
	npoint = t.npoint;
	nduration = t.nduration;
	pistart = NULL;
	plhs = NULL;
	if (t.pistart==NULL || t.plhs==NULL)
		return;
	AllocateArray();
	for (i=0; i<ndim; i++)
		pistart[i] = t.pistart[i];
	for (i=0; i<nduration; i++)
		plhs[i] = t.plhs[i];
}

CTrainSequence& CTrainSequence::operator=(const CTrainSequence& t)
{
	if (this==&t)
		return *this;
	int i;
	DeleteArray();
	ndim = t.ndim;
	npoint = t.npoint;
	nduration = t.nduration;
	if (t.pistart!=NULL && t.plhs!=NULL)
	{
		AllocateArray();
		for (i=0; i<ndim; i++)
			pistart[i] = t.pistart[i];
		for (i=0; i<nduration; i++)
			plhs[i] = t.plhs[i];
	}
	return *this;
}

void CTrainSequence::CopySamples(CTrainSequence& t)
{
	//t should have the same nduration, npoint and ndim
	//assume all arrays has been allocated
	for (int i=0; i<nduration; i++)
		plhs[i] = t.plhs[i];
}

void CTrainSequence::AllocateArray()
{
	int i;
	DeleteArray();
	pistart = new int [ndim];
	//set default starting point at the mid point
	for (i=0; i<ndim; i++)
		pistart[i] = npoint/2;
	plhs = new CLHS [nduration];
	for (i=0; i<nduration; i++)
	{
		plhs[i].SetDimension(ndim);
		plhs[i].SetNumberOfPoints(npoint);
		plhs[i].AllocateSampleArray();
	}
}

void CTrainSequence::DeleteArray()
{
	if (pistart!=NULL)
	{
		delete [] pistart;
		pistart = NULL;
	}
	if (plhs!=NULL)
	{
		delete [] plhs;
		plhs = NULL;
	}
}

void CTrainSequence::SetDimension(int n)
{
	DeleteArray();
	ndim = n;
}

void CTrainSequence::SetNumberOfPoints(int n)
{
	DeleteArray();
	npoint = n;
}

void CTrainSequence::SetNumberOfDurations(int n)
{
	DeleteArray();
	nduration = n;
}

void CTrainSequence::SetSizeAll(int ndi, int np, int ndu)
{
	DeleteArray();
	ndim = ndi;
	npoint = np;
	nduration = ndu;
	AllocateArray();
}

void CTrainSequence::SetDefaultStartingPoint()
{
	int i;
	for (i=0; i<ndim; i++)
		pistart[i] = npoint/2;
}

void CTrainSequence::SetRandomStartingPoint()
{
	int i;
	for (i=0; i<ndim; i++)
		pistart[i] = rand()%npoint;
}

void CTrainSequence::SetStartingPoint(int* pi)
{
	int i, j;
	for (i=0; i<ndim; i++)
	{
		j = pi[i];
		if (j<0)
			j = 0;
		if (j>=npoint)
			j = npoint - 1;
		pistart[i] = j;
	}
}

void CTrainSequence::SimpleSampling()
{
	//assume the plhs array has been allocated
	//assume the pistart array has been allocated and assigned using either midpoint or random method
	int i;
	int** ppx;
	int* p1st = pistart;
	for (i=0; i<nduration; i++)
	{
		plhs[i].GivenFirstSampling(p1st);
		ppx = plhs[i].GetLHSPoints();
		p1st = ppx[npoint-1];
	}
}

void CTrainSequence::SelectBestSampling(int n)
{
	//try n times and select the best based on the quality phi
	int i;
	double phi;
	double phi_min;
	double p = 50;
	CTrainSequence ts(ndim,npoint,nduration);
	ts.SetStartingPoint(pistart);
	SimpleSampling();
	phi = CalcQualityPhi(p);
	phi_min = phi;
	for (i=0; i<n; i++)
	{
		ts.SimpleSampling();
		phi = ts.CalcQualityPhi(p);
		if (phi<phi_min)
		{
			phi_min = phi;
			CopySamples(ts);
		}
	}
}

void CTrainSequence::GetTrainSequence(int** ppx)
{
	//ppx has to be allocated by the calling function
	//size of ppx at least nduration*(npoint-1)+1 rows by ndim columns
	int i, j, k;
	int ipt;		//point index
	int** ppx_lhs;	//ppx in plhs[i];
	//get the starting point
	ppx_lhs = plhs[0].GetLHSPoints();
	for (k=0; k<ndim; k++)
			ppx[0][k] = ppx_lhs[0][k];
	//add points for each duration and skip the first point in each duration
	ipt = 1;
	for (i=0; i<nduration; i++)
	{
		ppx_lhs = plhs[i].GetLHSPoints();
		for (j=1; j<npoint; j++)
		{
			for (k=0; k<ndim; k++)
				ppx[ipt][k] = ppx_lhs[j][k];
			ipt++;
		}
	}
}

double CTrainSequence::CalcQualityPhi(double p)
{
	//usually p = 50;
	int i, j, k;
	int npt = nduration*(npoint-1) + 1;
	double phi = 0;
	double dis;
	double sum;
	int** ppxgrp;	//contains all points
	ppxgrp = new int* [npt];
	for (i=0; i<npt; i++)
		ppxgrp[i] = new int [ndim];
	GetTrainSequence(ppxgrp);
	//calc phi
	for (i=0; i<npt-1; i++)
	{
		for (j=i+1; j<npt; j++)
		{
			sum = 0;
			for (k=0; k<ndim; k++)
			{
				dis = (double)(ppxgrp[i][k] - ppxgrp[j][k]);
				if (dis<0)
					dis = -dis;
				sum += dis;
			}
			if (sum>0)
				phi += pow(1/sum,p);
			else
				phi += 1e10;
		}
	}
	phi = pow(phi,1/p);
	//delete local memory
	for (i=0; i<npt; i++)
		delete [] ppxgrp[i];
	delete [] ppxgrp;
	return phi;
}
