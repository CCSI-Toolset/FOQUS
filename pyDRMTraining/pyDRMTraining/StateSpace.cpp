//StateSpace.cpp
#include <math.h>
#include "StateSpace.h"
#include "Matrix.h"

CStateSpace::CStateSpace(void)
{
	nstate = 2;
	ppa = NULL;
	pb = NULL;
	pc = NULL;
	px = NULL;
}

CStateSpace::~CStateSpace(void)
{
	DeleteMemory();
}

void CStateSpace::AllocateMemory()
{
	int i;
	DeleteMemory();
	ppa = new double* [nstate];
	for (i=0; i<nstate; i++)
		ppa[i] = new double [nstate];
	pb = new double [nstate];
	pc = new double [nstate];
	px = new double [nstate];
}

void CStateSpace::DeleteMemory()
{
	int i;
	if (ppa!=NULL)
	{
		for (i=0; i<nstate; i++)
			delete [] ppa[i];
		delete [] ppa;
		ppa = NULL;
	}
	if (pb!=NULL)
	{
		delete [] pb;
		pb = NULL;
	}
	if (pc!=NULL)
	{
		delete [] pc;
		pc = NULL;
	}
	if (px!=NULL)
	{
		delete [] px;
		px = NULL;
	}
}

void CStateSpace::InitStateVectorToSteadyState(double u)
{
	//obtain steady-state state vector by solving (A-I)x = -Bu, assuming converging A,B matrices
	int i, j;
	CMatrix m(nstate,nstate);
	double* pbu = new double [nstate];
	double** ppm = m.ppa;
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			ppm[i][j] = ppa[i][j];
		ppm[i][i] -= 1;
	}
	for (i=0; i<nstate; i++)
		pbu[i] = -u*pb[i];
	m.GaussianEliminationWithFullPivoting(pbu,px);
	delete [] pbu;
}

void CStateSpace::CalcNextStateVector(double u)
{
	int i, j;
	double sum;
	double* px_new = new double [nstate];
	for (i=0; i<nstate; i++)
	{
		sum = 0;
		for (j=0; j<nstate; j++)
			sum += ppa[i][j]*px[j];
		px_new[i] = sum + u*pb[i];
	}
	for (i=0; i<nstate; i++)
		px[i] = px_new[i];
	delete [] px_new;
}

double CStateSpace::CalcOutput()
{
	int i;
	double y = 0;
	for (i=0; i<nstate; i++)
		y += pc[i]*px[i];
	return y;
}

void CStateSpace::WriteStateSpaceMatrices(FILE* pf)
{
	int i, j;
	fprintf(pf,"%d\t//number of states\n",nstate);
	fprintf(pf,"//A matrix\n");
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			fprintf(pf,"%lg\t",ppa[i][j]);
		fprintf(pf,"\n");
	}
	fprintf(pf,"//B matrix\n");
	for (i=0; i<nstate; i++)
		fprintf(pf,"%lg\t",pb[i]);
	fprintf(pf,"\n");
}

void CStateSpace::ReadStateSpaceMatrices(FILE* pf)
{
	int i, j;
	DeleteMemory();
	fscanf(pf,"%d",&nstate);
	AllocateMemory();
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			fscanf(pf,"%lg",&ppa[i][j]);
	}
	for (i=0; i<nstate; i++)
		fscanf(pf,"%lg",&pb[i]);
}

PyObject* CStateSpace::GetStateSpaceAsTuple()
{
	int i, j, k;
	int nsize = 1 + (nstate + 1)*nstate;
	PyObject* obj_result = PyTuple_New(nsize);
	k = 0;
	PyTuple_SetItem(obj_result, k++, Py_BuildValue("i", nstate));
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			PyTuple_SetItem(obj_result, k++, Py_BuildValue("d", ppa[i][j]));
	}
	for (i=0; i<nstate; i++)
		PyTuple_SetItem(obj_result, k++, Py_BuildValue("d", pb[i]));
	return obj_result;
}
