//Simplex.h
//Nelder-Mead method
#ifndef __SIMPLEX_H__
#define __SIMPLEX_H__

#include "ObjectiveFunction.h"

class CSimplex
{
private:
	int nvar;				//number of input variables
	int nite_max;			//maximum number of iterations allowed
	double   cref;			//reflection coefficient
	double   cexp;			//expansion coefficient
	double   ccon;			//contraction coefficient
	double   cshr;			//shrinking coefficient
	double   ftolr;			//relative error of objective function for convergence
	double   ftola;			//absolute error of objective function for convergence
	double*  psum;			//sum of all simplex points, for base face centriod calculation, nvar elements
	double*  pnew;			//new point vector, nvar+1 elements
	double*  psave;			//saved point vector, nvar+1 elements
	double*  pmax;			//array of maximum allowed values
	double*  pmin;			//array of minimum allowed values
	double** pps;			//simplex with nvar+1 vectors, each vector has nvar+1 element with last element as objective function

	CObjectiveFunction* pobjfunc;	//pointer to an objective function object

	void DeleteMemory();	//memory cleanup handled by destructor
	
public:
	CSimplex();
	virtual ~CSimplex();
	void AllocateMemory();
	void SetNvar(int n) {nvar = n; nite_max=n*50;}
	void SetObjectiveFunctionPointer(CObjectiveFunction* pof) {pobjfunc=pof;}
	void InitSimplex(double* p0, double* plen, double* pmx, double* pmn);
	void CalcPsum();
	void SortSimplex();
	void CalcNewPoint(double coef);
	void ShrinkSimplex();
	int Optimize();
	double CalcObjectiveFunction(double* pvar);
};

#endif