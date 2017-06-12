//LaguerreStateSpace.cpp
#include <math.h>
#include "LaguerreStateSpace.h"

CLaguerreStateSpace::CLaguerreStateSpace(void)
{
	nstate = 6;
	nstate2 = 6;
	a = 0.5;
	a2 = 0.96;
	ndelay = 0;
	ipole2 = 0;
}

CLaguerreStateSpace::~CLaguerreStateSpace(void)
{
}

void CLaguerreStateSpace::CreateUnbalancedStateSpace()
{
	//realization based on Page 66 of Zhou et al., 1996 given low-pass and all-pass matrices
	//delay A, B, C, D as 0, 1, 1, 0
	//low-pass A, B, C, D as a, 1, sqrt(beta), 0
	//all-pass A, B, C, D as a, sqrt(beta), sqrt(beta), -a
	//if ipole2 is true, combine two Laguerre Matrices to form a single one
	int nstate1;	//1st Laguerre state size
	//check if number of delay is too large
	if (ipole2)
	{
		nstate1 = nstate - nstate2;		
		if (nstate1<ndelay+1)
		{
			printf("State-space order is less than number of delays plus 1 for the 1st Laguerre pole!\n");
			return;
		}
		if (nstate2<ndelay+1)
		{
			printf("State-space order is less than number of delays plus 1 for the 2nd Laguerre pole!\n");
			return;
		}
	}
	else
	{
		nstate1 = nstate;
		if (nstate<ndelay+1)
		{
			printf("State-space order is less than number of delays plus 1 !\n");
			return;
		}
	}
	int i, j;
	int iall_pass;				//0-based all-pass index
	double sqrt_beta = sqrt(1-a*a);
	double sqrt_beta2;
	double**  ppa2 = NULL;			//A matrix
	double* pb2 = NULL;				//B matrix
	double* pc2 = NULL;				//C matrix
	if (ipole2)
	{
		sqrt_beta2 = sqrt(1-a2*a2);
		ppa2 = new double* [nstate2];
		for (i=0; i<nstate2; i++)
			ppa2[i] = new double [nstate2];
		pb2 = new double [nstate2];
		pc2 = new double [nstate2];
	}
	//set matrices for the 1st pole
	//D matrix is always zero (scalar) based on the above realization scheme
	//assign B matrix, all but the first element is zero
	pb[0] = 1;
	for (i=1; i<nstate1; i++)
		pb[i] = 0;
	//assign A and C matrices
	//first set upper right elements excluding diagonal in A to zero
	for (i=0; i<nstate1; i++)
	{
		for (j=i+1; j<nstate1; j++)
			ppa[i][j] = 0;
	}
	if (ndelay)
	{
		//A matrix, first row always zero
		for (j=0; j<ndelay; j++)
			ppa[0][j] = 0;
		//A matrix, the other rows
		for (i=1; i<ndelay; i++)
		{
			for (j=0; j<ndelay; j++)
			{
				if (j==i-1)
					ppa[i][j] = 1;
				else
					ppa[i][j] = 0;
			}
		}
		//C matrix
		for (j=0; j<ndelay-1; j++)
			pc[j] = 0;
		pc[ndelay-1] = 1;		//this will be overwritten later when applying low-pass and all-pass terms
		//apply low-pass to A and C matrices
		ppa[ndelay][ndelay] = a;
		for (j=0; j<ndelay; j++)
			ppa[ndelay][j] = pc[j];
		//apply D1C2
		pc[ndelay-1] = 0;
		pc[ndelay] = sqrt_beta;
	}
	else	//no delay, set as low-pass matrix
	{
		ppa[0][0] = a;
		pc[0] = sqrt_beta;
	}
	//at this point the size of A matrix is (ndelay+1) by (ndelay+1)
	iall_pass = 0;
	for (i=ndelay+1; i<nstate1; i++)
	{
		//A matrix
		ppa[i][i] = a;
		for (j=0; j<i; j++)
			ppa[i][j] = sqrt_beta*pc[j];
		//C matrix
		pc[i] = sqrt_beta;
		for (j=0; j<i; j++)
			pc[j] *= -a;
		iall_pass++;
	}

	//assign matrices for the second pole and then the combined matrices if ipole2 is true
	if (ipole2)
	{
		pb2[0] = 1;
		for (i=1; i<nstate2; i++)
			pb2[i] = 0;
		//assign A and C matrices
		//first set upper right elements excluding diagonal in A to zero
		for (i=0; i<nstate2; i++)
		{
			for (j=i+1; j<nstate2; j++)
				ppa2[i][j] = 0;
		}
		//avoid second pole delay, otherwise it causes chelosky of Q fails
		//set as low-pass matrix
		ppa2[0][0] = a2;
		pc2[0] = sqrt_beta2;
		//at this point the size of A matrix is 1 by 1
		iall_pass = 0;
		for (i=1; i<nstate2; i++)
		{
			//A matrix
			ppa2[i][i] = a2;
			for (j=0; j<i; j++)
				ppa2[i][j] = sqrt_beta2*pc2[j];
			//C matrix
			pc2[i] = sqrt_beta2;
			for (j=0; j<i; j++)
				pc2[j] *= -a2;
			iall_pass++;
		}
		//combine the two sets of matrices
		//combine A
		for (i=0; i<nstate1; i++)
		{
			for (j=0; j<nstate2; j++)
				ppa[i][nstate1+j] = 0;
		}
		for (i=0; i<nstate2; i++)
		{
			for (j=0; j<nstate1; j++)
				ppa[nstate1+i][j] = 0;
			for (j=0; j<nstate2; j++)
				ppa[nstate1+i][nstate1+j] = ppa2[i][j];
		}
		//combine B and C
		for (i=0; i<nstate2; i++)
		{
			pb[nstate1+i] = pb2[i];
			pc[nstate1+i] = pc2[i];
		}
		//delete memory
		
		for (i=0; i<nstate2; i++)
			delete [] ppa2[i];
		delete [] ppa2;
		delete [] pb2;
		delete [] pc2;
	}
}

void CLaguerreStateSpace::PrepareWeightMatrix(int nneuron, double** ppweight, double* psigma, int iscale)
{
	//consider the normalization by standard deviation
	int i, j;
	mweight.SetDimensions(nneuron, nstate);
	mweight.AllocateMemory();
	if (iscale)
	{
		for (i=0; i<nneuron; i++)
		{
			for (j=0; j<nstate; j++)
				mweight.SetElementTo(i,j,ppweight[i][j]/psigma[j]);
		}
	}
	else
	{
		for (i=0; i<nneuron; i++)
		{
			for (j=0; j<nstate; j++)
				mweight.SetElementTo(i,j,ppweight[i][j]);
		}
	}
}

void CLaguerreStateSpace::RealizeBalancedStateSpace(CStateSpace* pss)
{
	//given the weight matrix of neural network, reduce the state space through balanced realization based on Lyapunov equation
	//pw is W1j hat (nw by mj in Larry's paper). However, we decide to map state variables directly to output. Therefore weights does not to multiply by C matrix
	//pss is the returned reduced state space model
	int i, j;
	int nstate_tc;							//number of states after truncation
	double** ppa_matrix;					//ppa pointer to a matrix
	double** ppa_ss;						//ppa pointer to a state space A
	double* psv = new double [nstate];		//singular value of Hankel matrix
	double* psv_sqrt = new double [nstate];	//sqrt(psv)
	CMatrix am(nstate,nstate,ppa);			//A matrix, need to avoid ppa being deleted
	CMatrix amt(nstate,nstate);				//transpose of A matrix
	CMatrix pm(nstate,nstate);				//observability Grammian
	CMatrix qm(nstate,nstate);				//controllability Grammian
	CMatrix wwm(nstate,nstate);				//[W1j]'[W1j]
	CMatrix bbm(nstate,nstate);				//[bj][bj]'
	CMatrix rhsm(nstate,nstate);			//right hand side matrix of Lyapunov equations, also as temporary matrix
	CMatrix pmc(nstate,nstate);				//pm = pmc(pmc)'  pmc is Cholesky decomposition of pm
	CMatrix qmc(nstate,nstate);				//qm = qmc(qmc)'  qmc is Cholesky decomposition of qm
	CMatrix hm(nstate,nstate);				//Hankel matrix
	CMatrix um(nstate,nstate);				//U in singular value decomposition of USV'
	CMatrix vm(nstate,nstate);				//V in singular value decomposition
	CMatrix tm(nstate,nstate);				//T matrix, which is sv^(-1/2)U'pmc', used to calculate A(balanced)=TAT^(-1), C(balanced)=CR
	CMatrix tmi(nstate,nstate);				//inverse of T, which is qmcVsv^(-1/2), used to calculate B(balanced)=TB and C(balanced)=CT^(-1)
	CMatrix abm(nstate,nstate);				//balanced A matrix
	//calculate amt
	am.Transpose(&amt);
	mweight.MultiplyBySelfTransposeOnLeft(&wwm);
	//calculate bbm based on pb
	ppa_matrix = bbm.ppa;
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			ppa_matrix[i][j] = pb[i]*pb[j];
	}
	//solve observability Grammian P:  P - A'PA = W'W
	pm.SolveOriginalGrammianMatrixByHalf(&am,&wwm);
	//solve controllability Grammian Q: Q-AQA' = BB'
	qm.SolveOriginalGrammianMatrixByHalf(&amt,&bbm);
	//Cholesky decomposition
	if (!pm.CholeskyDecompose(&pmc))
	{
		printf("Chelosky decomposition failed. Gramian matrix P is not symmetric positive definite\n");
		FILE* pf=fopen("matrix_p.txt","w");
		fprintf(pf,"Matrix A\n");
		am.WriteText(pf);
		fprintf(pf,"Grammian P\n");
		pm.WriteText(pf);
		fprintf(pf,"Cholesky P\n");
		pmc.WriteText(pf);
		fprintf(pf,"Weight matrix\n");
		wwm.WriteText(pf);
		fclose(pf);
	}
	if (!qm.CholeskyDecompose(&qmc))
	{
		printf("Chelosky decomposition failed. Gramian matrix Q is not symmetric positive definite\n");
		FILE* pf=fopen("matrix_q.txt","w");
		fprintf(pf,"Matrix A'\n");
		amt.WriteText(pf);
		fprintf(pf,"Grammian Q\n");
		qm.WriteText(pf);
		fprintf(pf,"Cholesky Q\n");
		qmc.WriteText(pf);
		fprintf(pf,"BB' matrix\n");
		bbm.WriteText(pf);
		fclose(pf);
	}
	//use rhsm to save pmc'
	pmc.Transpose(&rhsm);
	rhsm.MultiplyByMatrixOnRight(&qmc,&hm);
	hm.SingularValueDecomposition(true,true,&um,&vm,psv);
	//write Hankel singular values to message line
	printf("Hankel singular values are [");
	for (i=0; i<nstate; i++)
	{
		if (i<nstate-1)
			printf("%lg ",psv[i]);
		else
			printf("%lg].\n",psv[i]);
	}
	for (i=0; i<nstate; i++)
		psv_sqrt[i] = sqrt(psv[i]);
	//T inverse matrix
	qmc.MultiplyByMatrixOnRight(&vm,&tmi);
	ppa_matrix = tmi.ppa;
	//multiply diagonal matrix sv^(-1/2) on right
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			ppa_matrix[i][j] /= psv_sqrt[j];
	}
	//T matrix
	pmc.MultiplyByMatrixOnRight(&um,&rhsm);
	rhsm.Transpose(&tm);
	//multiply diagonal matrix sv^(-1/2) on left
	ppa_matrix = tm.ppa;
	for (i=0; i<nstate; i++)
	{
		for (j=0; j<nstate; j++)
			ppa_matrix[i][j] /= psv_sqrt[i];
	}

	/* debug: calculate balanced Grammians to see if they are diagonal
	CMatrix qmbar(nstate,nstate);
	CMatrix pmbar(nstate,nstate);
	tmi.Transpose(&rhsm);
	pm.MultiplyByMatrixOnLeft(&rhsm,&qmbar);
	qmbar.MultiplyByMatrixOnRight(&tmi,&pmbar);
	tm.Transpose(&qmbar);
	qm.MultiplyByMatrixOnRight(&qmbar,&rhsm);
	rhsm.MultiplyByMatrixOnLeft(&tm,&qmbar);
	*/

	//calculate balanced A
	am.MultiplyByMatrixOnLeft(&tm,&rhsm);
	rhsm.MultiplyByMatrixOnRight(&tmi,&abm);
	//truncate the singular values
	for (i=1; i<nstate; i++)
	{
		if (psv[i]*10<psv[i-1])
			break;
	}
	nstate_tc = i;
	pss->nstate = nstate_tc;
	pss->AllocateMemory();
	//assign balanced and truncated A in reduced state space
	ppa_matrix = abm.ppa;
	ppa_ss = pss->ppa;
	for (i=0; i<nstate_tc; i++)
	{
		for (j=0; j<nstate_tc; j++)
			ppa_ss[i][j] = ppa_matrix[i][j];
	}
	//assign balanced and truncated B in reduced state space
	tm.MultiplyByVectorOnRight(pb,psv);
	for (i=0; i<nstate_tc; i++)
		pss->pb[i] = psv[i];
	//assign balanced and truncated C in reduced state space
	tmi.MultiplyByVectorOnLeft(pc,psv);
	for (i=0; i<nstate_tc; i++)
		pss->pc[i] = psv[i];
	//set am.ppa to NULL to avoid being deleted
	am.ppa = NULL;
	delete [] psv;
	delete [] psv_sqrt;
}
