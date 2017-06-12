//Simplex.cpp
#include <cmath>
#include "CCSI.h"
#include "Simplex.h"

CSimplex::CSimplex()
{
	nvar = 2;
	nite_max = 100;		//origional value is 150
	cref = 1;
	cexp = 2;
	ccon = 0.5;
	cshr = 0.5;
	ftolr = 0.0002;		//original value is 0.0001
	ftola = 0;
	psum = NULL;
	pnew = NULL;
	psave = NULL;
	pmax = NULL;
	pmin = NULL;
	pps = NULL;
	pobjfunc = NULL;			//calling program take care of memory allocation and deletion
}

CSimplex::~CSimplex()
{
	DeleteMemory();
}

void CSimplex::AllocateMemory()
{
	DeleteMemory();
	psum = new double [nvar];
	pnew = new double [nvar+1];
	psave = new double [nvar+1];
	pmax = new double [nvar];
	pmin = new double [nvar];
	pps = new double* [nvar+1];
	for (int i=0; i<=nvar; i++)
		pps[i] = new double [nvar+1];
}

void CSimplex::DeleteMemory()
{
	if (psum!=NULL)
	{
		delete [] psum;
		psum = NULL;
	}
	if (pnew!=NULL)
	{
		delete [] pnew;
		pnew = NULL;
	}
	if (psave!=NULL)
	{
		delete [] psave;
		psave = NULL;
	}
	if (pmax!=NULL)
	{
		delete [] pmax;
		pmax = NULL;
	}
	if (pmin!=NULL)
	{
		delete [] pmin;
		pmin = NULL;
	}
	if (pps!=NULL)
	{
		for (int i=0; i<=nvar; i++)
			delete [] pps[i];
		delete [] pps;
		pps = NULL;
	}
}

void CSimplex::InitSimplex(double* p0, double* plen, double* pmx, double* pmn)
{
	//p0 is the first point and plen is the offset length in each direction
	//nvar elements in both p0 and plen
	int i, j;
	for (i=0; i<nvar; i++)
	{
		pps[0][i] = p0[i];
		pmax[i] = pmx[i];
		pmin[i] = pmn[i];
	}
	for (j=1; j<=nvar; j++)
	{
		for (i=0; i<nvar; i++)
			pps[j][i] = p0[i];
		pps[j][j-1] += plen[j-1];
		if (pps[j][j-1]>pmax[j-1])
			pps[j][j-1] = pmax[j-1];
		if (pps[j][j-1]<pmin[j-1])
			pps[j][j-1] = pmin[j-1];
	}
	for (j=0; j<=nvar; j++)
		CalcObjectiveFunction(pps[j]);
	CalcPsum();
}

void CSimplex::CalcPsum()
{
	int i, j;
	for (i=0; i<nvar; i++)
	{
		psum[i] = 0;
		for (j=0; j<=nvar; j++)
			psum[i] += pps[j][i];
	}
}

void CSimplex::SortSimplex()
{
	//bubble sort the simplex, form lowest to highest
	int i, j;
	double* ptmp;
	for (i=0; i<nvar; i++)
	{
		for (j=i+1; j<=nvar; j++)
		{
			if (pps[j][nvar]<pps[i][nvar])
			{
				ptmp = pps[j];
				pps[j] = pps[i];
				pps[i] = ptmp;
			}
		}
	}
}

void CSimplex::CalcNewPoint(double coef)
{
	int i;
	double cnew = (coef+1)/nvar;
	double cnew1 = cnew + coef;
	for (i=0; i<nvar; i++)
	{
		pnew[i] = cnew*psum[i] - cnew1*pps[nvar][i];
		//check if inside limit, currently hard wired
		if (pnew[i]<pmin[i])
			pnew[i] = pmin[i];
		if (pnew[i]>pmax[i])
			pnew[i] = pmax[i];
	}
}

void CSimplex::ShrinkSimplex()
{
	int i, j;
	for (i=1; i<=nvar; i++)
	{
		for (j=0; j<nvar; j++)
			pps[i][j] = pps[0][j] + cshr*(pps[i][j]-pps[0][j]);
		CalcObjectiveFunction(pps[i]);
	}
}

int CSimplex::Optimize()
{
	//return 0 if converges with nite_max
	//otherwise return number of iterations performed
	int i;
	int nite = 0;			//iteration count
	double dx;				//difference of input
	double dx_max;			//maximum relative error for input
	double ferra;			//absolute error of objective function
	double ferrr;			//relative error of objective function
	double fref;			//objective function evaluated at reflected point
	double fexp;			//objective function evaluated at expension point
	double fcon;			//objective function evaluated at contraction point
	double* ptmp;
	do
	{
		SortSimplex();
		ferra = fabs(pps[nvar][nvar]-pps[0][nvar]);
		ferrr = ferra/(fabs(pps[0][nvar])+TINY);
		//also check the input data variation
		dx_max = 0;
		for (i=0; i<nvar; i++)
		{
			dx = fabs(pps[nvar][i] - pps[0][i]);
			if (dx>0)
				dx = fabs(dx/pps[0][i]);
			else
				dx = 0;
			if (dx>dx_max)
				dx_max = dx;
		}
		if (ferrr<ftolr || ferra<ftola || dx_max<ftolr)
		{
			CalcObjectiveFunction(pps[0]);
			return nite;
		}
		nite++;
		//reflection
		CalcNewPoint(cref);
		fref = CalcObjectiveFunction(pnew);
		if (fref<pps[nvar-1][nvar] && fref>pps[0][nvar])	//swap reflection point with worst point
		{
			//update psum
			for (i=0; i<nvar; i++)
				psum[i] += pnew[i] - pps[nvar][i];
			ptmp = pnew;
			pnew = pps[nvar];
			pps[nvar] = ptmp;
		}
		else if (fref<pps[0][nvar])		//expansion
		{
			//save the reflection point
			ptmp = psave;
			psave = pnew;
			pnew = ptmp;
			CalcNewPoint(cexp);
			fexp = CalcObjectiveFunction(pnew);
			if (fexp<fref)		//swap expansion point with worst point
			{
				//update psum
				for (i=0; i<nvar; i++)
					psum[i] += pnew[i] - pps[nvar][i];
				ptmp = pnew;
				pnew = pps[nvar];
				pps[nvar] = ptmp;
			}
			else				//swap reflection point with worst point
			{
				//update psum
				for (i=0; i<nvar; i++)
					psum[i] += psave[i] - pps[nvar][i];
				ptmp = psave;
				psave = pps[nvar];
				pps[nvar] = ptmp;
			}
		}
		else		//contraction
		{
			CalcNewPoint(-ccon);
			fcon = CalcObjectiveFunction(pnew);
			if (fcon<pps[nvar][nvar])		//swap contraction point with worst point
			{
				//update psum
				for (i=0; i<nvar; i++)
					psum[i] += pnew[i] - pps[nvar][i];
				ptmp = pnew;
				pnew = pps[nvar];
				pps[nvar] = ptmp;
			}
			else			//shrinking
			{
				ShrinkSimplex();
				CalcPsum();
			}
		}
	}while (nite<nite_max);
	//make sure the best input parameters are used
	CalcObjectiveFunction(pps[0]);
	return nite;
}

double CSimplex::CalcObjectiveFunction(double* pvar)
{
	//assign the result to the last element in pvar and also return it
	double fun = 0;
	fun = pobjfunc->CalcObjectiveFunction(pvar);
	//assign objective function value to last element
	pvar[nvar] = fun;
	return fun;
}