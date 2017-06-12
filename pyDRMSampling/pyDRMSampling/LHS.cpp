//LHS.cpp
#include <stdlib.h>
#include "LHS.h"
#include <math.h>

CLHS::CLHS()
{
	ndim = 2;
	npoint = 2;
	ppx = NULL;
}

CLHS::CLHS(int nd, int np)
{
	ndim = nd;
	npoint = np;
	ppx = NULL;
	AllocateSampleArray();
}

CLHS::~CLHS()
{
	DeleteSampleArray();
}

CLHS::CLHS(const CLHS &t)
{
	int i, j;
	ndim = t.ndim;
	npoint = t.npoint;
	ppx = NULL;
	if (t.ppx==NULL)
		return;
	AllocateSampleArray();
	for (i=0; i<npoint; i++)
	{
		for (j=0; j<ndim; j++)
			ppx[i][j] = t.ppx[i][j];
	}
}

CLHS& CLHS::operator=(const CLHS& t)
{
	if (this==&t)
		return *this;
	int i, j;
	DeleteSampleArray();
	ndim = t.ndim;
	npoint = t.npoint;
	if (t.ppx!=NULL)
	{
		AllocateSampleArray();
		for (i=0; i<npoint; i++)
		{
			for (j=0; j<ndim; j++)
				ppx[i][j] = t.ppx[i][j];
		}
	}
	return *this;
}

void CLHS::AllocateSampleArray()
{
	DeleteSampleArray();
	ppx = new int* [npoint];
	for (int i=0; i<npoint; i++)
		ppx[i] = new int [ndim];
}

void CLHS::DeleteSampleArray()
{
	if (ppx!=NULL)
	{
		for (int i=0; i<npoint; i++)
			delete [] ppx[i];
		delete [] ppx;
		ppx = NULL;
	}
}

void CLHS::SetDimension(int n)
{
	DeleteSampleArray();
	ndim = n;
}

void CLHS::SetNumberOfPoints(int n)
{
	DeleteSampleArray();
	npoint = n;
}

void CLHS::SimpleSampling()
{
	//ppx has npoint rows and ndim columns
	int i, j;
	int isel;
	int** ppleft = new int* [ndim];		//left over points
	for (i=0; i<ndim; i++)
	{
		ppleft[i] = new int [npoint];
		for (j=0; j<npoint; j++)
			ppleft[i][j] = j;
	}
	for (i=0; i<npoint; i++)
	{
		for (j=0; j<ndim; j++)
		{
			isel = rand()%(npoint-i);
			ppx[i][j] = ppleft[j][isel];
			//replace the removed point in ppleft[j] by the last unselected point
			ppleft[j][isel] = ppleft[j][npoint-i-1];
		}
	}
	for (i=0; i<ndim; i++)
		delete [] ppleft[i];
	delete [] ppleft;
}

void CLHS::GivenFirstSampling(int* p1st)
{
	//ppx has npoint rows and ndim columns
	//p1st contains the first sample
	int i, j;
	int isel;
	int** ppleft = new int* [ndim];		//left over points
	for (i=0; i<ndim; i++)
	{
		ppleft[i] = new int [npoint];
		for (j=0; j<npoint; j++)
			ppleft[i][j] = j;
	}
	//assign the 1st point
	for (j=0; j<ndim; j++)
	{
		isel = p1st[j];
		ppx[0][j] = isel;
		//replace the removed point in ppleft[j] by the last unselected point
		ppleft[j][isel] = ppleft[j][npoint-1];
	}
	for (i=1; i<npoint; i++)
	{
		for (j=0; j<ndim; j++)
		{
			isel = rand()%(npoint-i);
			ppx[i][j] = ppleft[j][isel];
			//replace the removed point in ppleft[j] by the last unselected point
			ppleft[j][isel] = ppleft[j][npoint-i-1];
		}
	}
	for (i=0; i<ndim; i++)
		delete [] ppleft[i];
	delete [] ppleft;
}

double CLHS::CalcQualityPhi(double p)
{
	int i, j, k;
	double phi = 0;
	double dis;
	double sum;
	for (i=0; i<npoint-1; i++)
	{
		for (j=i+1; j<npoint; j++)
		{
			sum = 0;
			for (k=0; k<ndim; k++)
			{
				dis = (double)(ppx[i][k] - ppx[j][k]);
				if (dis<0)
					dis = -dis;
				sum += dis;
			}
			phi += pow(1/sum,p);
		}
	}
	phi = pow(phi,1/p);
	return phi;
}
