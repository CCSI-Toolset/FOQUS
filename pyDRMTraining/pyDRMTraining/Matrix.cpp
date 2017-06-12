// Matrix.cpp: implementation of the CMatrix class.
//
//////////////////////////////////////////////////////////////////////
#include <cmath>
#include <cfloat>
#include "Matrix.h"

#if defined WIN32 || defined WIN64
#define HYPOTFUNC _hypot
#else
#define HYPOTFUNC hypot
#endif

//////////////////////////////////////////////////////////////////////
// Construction/Destruction
//////////////////////////////////////////////////////////////////////

CMatrix::CMatrix()
{
	//ppa is not allocated in this constructor
	nrow = 2;
	ncol = 2;
	ppa = NULL;
}

CMatrix::CMatrix(int nr, int nc)
{
	//ppa will be allocated by this constructor
	nrow = nr;
	ncol = nc;
	ppa = NULL;
	AllocateMemory();
}

CMatrix::CMatrix(int nr, int nc, T_REAL** pp)
{
	//pp should be allocated correctly by calling function
	nrow = nr;
	ncol = nc;
	ppa = pp;
}

CMatrix::~CMatrix()
{
	DeleteMemory();
}

CMatrix::CMatrix(const CMatrix &t)
{
	//copy constructor
	int i, j;
	nrow = t.nrow;
	ncol = t.ncol;
	ppa = NULL;
	if (t.ppa==NULL)
		return;
	AllocateMemory();
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
			ppa[i][j] = t.ppa[i][j];
	}
}

CMatrix& CMatrix::operator=(const CMatrix& t)
{
	if (this==&t)
		return *this;
	int i, j;
	DeleteMemory();
	nrow = t.nrow;
	ncol = t.ncol;
	if (t.ppa!=NULL)
	{
		AllocateMemory();
		for (i=0; i<nrow; i++)
		{
			for (j=0; j<ncol; j++)
				ppa[i][j] = t.ppa[i][j];
		}
	}
	return *this;
}

void CMatrix::AllocateMemory()
{
	int i;
	DeleteMemory();			//delete memory first
	ppa = new T_REAL* [nrow];
	for (i=0; i<nrow; i++)
		ppa[i] = new T_REAL [ncol];
}

void CMatrix::DeleteMemory()
{
	int i;
	if (ppa!=NULL)
	{
		for (i=0; i<nrow; i++)
			delete [] ppa[i];
		delete [] ppa;
		ppa = NULL;
	}
}

void CMatrix::SetAllElementsTo(T_REAL x)
{
	int i, j;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
			ppa[i][j] = x;
	}
}

void CMatrix::Transpose(CMatrix* t)
{
	//return the transpose of current matrix to matrix t and keep the current matrix unchanged
	//matrix t should be allocated by calling function
	int i, j;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
			t->ppa[j][i] = ppa[i][j];
	}
}

int CMatrix::LUDecompose(int* pindex)
{
	//pindex array should be allocated by calling function
	//return 0 if no error
	if (nrow!=ncol)		//not square matrix
		return 1;
	int i, j, k;
	int imax;
	T_REAL big, dum, sum, temp;
	T_REAL* pvv;				//implicit scaling of each row
	pvv = new T_REAL [nrow];
	for (i=0; i<nrow; i++)
	{
		big = 0;
		for (j=0; j<ncol; j++)
		{
			if (temp=fabs(ppa[i][j])>big)
				big = temp;
		}
		if (big==0)		//singular matrix
			return 2;
		pvv[i] = 1/big;
	}
	for (j=0; j<ncol; j++)
	{
		for (i=0; i<j; i++)
		{
			sum = ppa[i][j];
			for (k=0; k<i; k++)
				sum -= ppa[i][k]*ppa[k][j];
			ppa[i][j] = sum;
		}
		big = 0;
		for (i=j; i<nrow; i++)
		{
			sum = ppa[i][j];
			for (k=0; k<j; k++)
				sum -= ppa[i][k]*ppa[k][j];
			ppa[i][j] = sum;
			if (dum=pvv[i]*fabs(sum)>=big)
			{
				big = dum;
				imax = i;
			}
		}
		if (j!=imax)
		{
			for (k=0; k<nrow; k++)
			{
				dum = ppa[imax][k];
				ppa[imax][k] = ppa[j][k];
				ppa[j][k] = dum;
			}
			pvv[imax] = pvv[j];
		}
		pindex[j] = imax;
		if (ppa[j][j]==0)
			ppa[j][j] = TINY;
		if (j!=ncol-1)
		{
			dum = 1/ppa[j][j];
			for (i=j+1; i<nrow; i++)
				ppa[i][j] *= dum;
		}
	}
	delete [] pvv;
	return 0;
}

void CMatrix::LUBackSubstitute(int* pindex, T_REAL* pb)
{
	//LUDecompose() should have been called
	//pindex array should be allocated and is returned by LUDecompose()
	//pb is the vector on the right hand side of equation as input
	//pb will be returned as solution vector
	//current LU decomposed matrix and pindex will not be altered by this function
	int i, j;
	int ii, ip;
	T_REAL sum;
	ii = -1;
	for (i=0; i<nrow; i++)
	{
		ip = pindex[i];
		sum = pb[ip];
		pb[ip] = pb[i];
		if (ii>=0)
		{
			for (j=ii; j<=i-1; j++)
				sum -= ppa[i][j]*pb[j];
		}
		else
		{
			if (sum)
				ii = i;
		}
		pb[i] = sum;
	}
	for (i=nrow-1; i>=0; i--)
	{
		sum = pb[i];
		for (j=i+1; j<nrow; j++)
			sum -= ppa[i][j]*pb[j];
		pb[i] = sum/ppa[i][i];
	}
}

int CMatrix::LUInverse(CMatrix* pinv)
{
	//pinv is the returned inverse matrix and should be allocated by calling function
	//current matrix will not be altered by this function
	if (nrow!=ncol)		//not square matrix
		return 1;
	int i, j;
	int* pindex = new int [nrow];
	CMatrix mlu(*this);	//copy current matrix
	int ierr = mlu.LUDecompose(pindex);
	T_REAL** ppa_inv = pinv->ppa;
	if (ierr)
	{
		delete [] pindex;
		return ierr;
	}
	T_REAL* pcol = new T_REAL [nrow];
	for (j=0; j<ncol; j++)
	{
		for (i=0; i<nrow; i++)
			pcol[i] = 0;
		pcol[j] = 1;
		mlu.LUBackSubstitute(pindex,pcol);
		for (i=0; i<nrow; i++)
			ppa_inv[i][j] = pcol[i];
	}
	delete [] pindex;
	delete [] pcol;
	return 0;
}

T_REAL CMatrix::LUDeterminant()
{
	if (nrow!=ncol)
		return 0;
	int i;
	T_REAL det = 1;
	//calculate deterninant based on LU decomposition
	CMatrix mlu(*this);	//copy current matrix
	int* pindex = new int [nrow];
	if (mlu.LUDecompose(pindex))
	{
		delete [] pindex;
		return 0;
	}
	for (i=0; i<nrow; i++)
		det *= mlu.ppa[i][i];
	delete [] pindex;
	return det;
}

bool CMatrix::CholeskyDecompose(CMatrix* c)
{
	//return true if the matrix is positive definite
	bool bpd = true;
	int i, j, k;
	T_REAL d;
	T_REAL s;
	T_REAL* prowj;
	T_REAL* prowk;
	T_REAL** ppac = c->ppa;
	//first set everything to zero
	for (j=0; j<nrow; j++)
	{
		for (k=0; k<nrow; k++)
			ppac[j][k] = 0;
	}
	for (j=0; j<nrow; j++)
	{
		prowj = ppac[j];
		d = 0;
		for (k=0; k<j; k++)
		{
			prowk = ppac[k];
			s = 0;
			for (i=0; i<k; i++)
				s += prowk[i]*prowj[i];
			s = (ppa[j][k] - s)/ppac[k][k];
			prowj[k] = s;
			d += s*s;
			bpd = bpd && (ppa[k][j]==ppa[j][k]);
		}
		d = ppa[j][j] - d;
		bpd = bpd && (d>0);
		if (d<=0)		//not positive definite, leave all the remaining elements to zero
		{
			printf("Cholesky L matrix diagonal element squared is %lg at row %d\n",d,j+1);
			return false;
		}
		ppac[j][j] = sqrt(d);
	}
	return bpd;
}

void CMatrix::QRDecompose(CMatrix* q, CMatrix* r)
{
	//decompose a mxn matrix with m>=n
	if (nrow<ncol)
		return;
	int i, j, k;
	T_REAL nrm;
	T_REAL s;
	CMatrix qr(nrow,ncol);
	T_REAL** QR = qr.ppa;
    T_REAL* Rdiag = new T_REAL [ncol];
	//make a copy of current matrix
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
			QR[i][j] = ppa[i][j];
	}
      for (k = 0; k < ncol; k++)
	  {
         // Compute 2-norm of k-th column without under/overflow.
         nrm = 0;
         for (i = k; i < nrow; i++)
            nrm = HYPOTFUNC(nrm,QR[i][k]);
         if (nrm != 0.0)
		 {
            // Form k-th Householder vector.
            if (QR[k][k] < 0)
               nrm = -nrm;
            for (i = k; i < nrow; i++)
               QR[i][k] /= nrm;
            QR[k][k] += 1.0;
            // Apply transformation to remaining columns.
            for (j = k+1; j < ncol; j++)
			{
               s = 0.0; 
               for (i = k; i < nrow; i++)
                  s += QR[i][k]*QR[i][j];
               s = -s/QR[k][k];
               for (i = k; i < nrow; i++)
                  QR[i][j] += s*QR[i][k];
            }
         }
         Rdiag[k] = -nrm;
      }
	  //obtain Q matrix
      T_REAL** Q = q->ppa;
      for (k = ncol-1; k >= 0; k--)
	  {
         for (i = 0; i < nrow; i++)
            Q[i][k] = 0.0;
         Q[k][k] = 1.0;
         for (j = k; j < ncol; j++)
		 {
            if (QR[k][k] != 0)
			{
               s = 0.0;
               for (i = k; i < nrow; i++)
                  s += QR[i][k]*Q[i][j];
               s = -s/QR[k][k];
               for (i = k; i < nrow; i++)
                  Q[i][j] += s*QR[i][k];
            }
         }
      }
	  //obtain R matrix
      T_REAL** R = r->ppa;
      for (i = 0; i < ncol; i++)
	  {
         for (j = 0; j < ncol; j++)
		 {
            if (i < j)
               R[i][j] = QR[i][j];
            else if (i == j)
               R[i][j] = Rdiag[i];
            else
               R[i][j] = 0.0;
         }
      }
	  delete [] Rdiag;
}

int CMatrix::SingularValueDecomposition(bool wantu, bool wantv, CMatrix* mu, CMatrix* mv, T_REAL* s)
{
	//For an m-by-n matrix A with m >= n, the singular value decomposition is
	//an m-by-n orthogonal matrix U, an n-by-n diagonal matrix S, and
	//an n-by-n orthogonal matrix V so that A = U*S*V'.
	//Note that based on math theory, U should be m x m, and S is m x n if m<n
	//Converted from LINPACK code.
	//wantu: true if matrix U needs to be returned
	//wantv: true if matrix V needs to be returned
	//ma: matrix A, input matrix m by n(m>=n)
	//mu: matrix U, output matrix m by n
	//mv: matrix V, output matrix n by n
	//s: single value array (diagonal terms), n elements
	int i, j, k;
	int m = nrow;
	int n = ncol;
    //check if m>=n
	if (m<n)
		return 1;
	T_REAL** A = ppa;
	T_REAL** U = mu->ppa;
	T_REAL** V = mv->ppa;
	//initialize U, V
	if (wantu)		//U has to be initialized, otherwise it will not work
	{
		for (i=0; i<m; i++)
		{
			for (j=0; j<n; j++)
				U[i][j] = 0;
		}
	}
	if (wantv)
	{
		for (i=0; i<n; i++)
		{
			for (j=0; j<n; j++)
				V[i][j] = 0;
		}
	}
	int nu = m < n ? m : n;		//this should return n since m>=n
	T_REAL* e = new T_REAL [n];
	T_REAL* work = new T_REAL [m];
	// Reduce A to bidiagonal form, storing the diagonal elements
	// in s and the super-diagonal elements in e.
	int nct = (m-1)<n ? (m-1) : n;
	int nrt = (n-2)<m ? (n-2) : m;
	if (nrt<0) nrt = 0;
	int max_nct_nrt = nct>nrt ? nct : nrt;
	for (k = 0; k < max_nct_nrt; k++)
	{
         if (k < nct)
		 {
            // Compute the transformation for the k-th column and
            // place the k-th diagonal in s[k].
            // Compute 2-norm of k-th column without under/overflow.
            s[k] = 0;
            for (i = k; i < m; i++)
               s[k] = HYPOTFUNC(s[k],A[i][k]);
            if (s[k] != 0.0)
			{
               if (A[k][k] < 0.0)
                  s[k] = -s[k];
               for (i = k; i < m; i++)
                  A[i][k] /= s[k];
               A[k][k] += 1.0;
            }
            s[k] = -s[k];
         }
         for (j = k+1; j < n; j++)
		 {
            if ((k < nct) & (s[k] != 0.0))
			{
			   // Apply the transformation.
               T_REAL t = 0;
               for (i = k; i < m; i++)
                  t += A[i][k]*A[i][j];
               t = -t/A[k][k];
               for (i = k; i < m; i++)
                  A[i][j] += t*A[i][k];
            }
            // Place the k-th row of A into e for the
            // subsequent calculation of the row transformation.
            e[j] = A[k][j];
         }
         if (wantu && (k < nct))
		 {
            // Place the transformation in U for subsequent back
            // multiplication.
            for (i = k; i < m; i++)
               U[i][k] = A[i][k];
         }
         if (k < nrt)
		 {
            // Compute the k-th row transformation and place the
            // k-th super-diagonal in e[k].
            // Compute 2-norm without under/overflow.
            e[k] = 0;
            for (i = k+1; i < n; i++)
               e[k] = HYPOTFUNC(e[k],e[i]);
            if (e[k] != 0.0)
			{
               if (e[k+1] < 0.0)
                  e[k] = -e[k];
               for (i = k+1; i < n; i++)
                  e[i] /= e[k];
               e[k+1] += 1.0;
            }
            e[k] = -e[k];
            if ((k+1 < m) & (e[k] != 0.0))
			{
               // Apply the transformation.
               for (i = k+1; i < m; i++)
                  work[i] = 0.0;
               for (j = k+1; j < n; j++)
			   {
                  for (i = k+1; i < m; i++)
                     work[i] += e[j]*A[i][j];
               }
               for (j = k+1; j < n; j++)
			   {
                  T_REAL t = -e[j]/e[k+1];
                  for (i = k+1; i < m; i++)
                     A[i][j] += t*work[i];
               }
            }
            if (wantv)
			{
               // Place the transformation in V for subsequent
               // back multiplication.
               for (i = k+1; i < n; i++)
                  V[i][k] = e[i];
            }
         }
      }

      // Set up the final bidiagonal matrix or order p.
	  int p = n < m+1 ? n : (m+1);
      if (nct < n)
         s[nct] = A[nct][nct];
      if (m < p)
         s[p-1] = 0.0;
      if (nrt+1 < p)
         e[nrt] = A[nrt][p-1];
      e[p-1] = 0.0;

      // If required, generate U.
      if (wantu)
	  {
         for (j = nct; j < nu; j++)
		 {
            for (i = 0; i < m; i++)
               U[i][j] = 0.0;
            U[j][j] = 1.0;
         }
         for (k = nct-1; k >= 0; k--)
		 {
            if (s[k] != 0.0)
			{
               for (j = k+1; j < nu; j++)
			   {
                  T_REAL t = 0;
                  for (i = k; i < m; i++)
                     t += U[i][k]*U[i][j];
                  t = -t/U[k][k];
                  for (i = k; i < m; i++)
                     U[i][j] += t*U[i][k];
               }
               for (i = k; i < m; i++ )
                  U[i][k] = -U[i][k];
               U[k][k] = 1.0 + U[k][k];
               for (i = 0; i < k-1; i++)
                  U[i][k] = 0.0;
            }
			else
			{
               for (i = 0; i < m; i++)
                  U[i][k] = 0.0;
               U[k][k] = 1.0;
            }
         }
      }

      // If required, generate V.
      if (wantv)
	  {
         for (k = n-1; k >= 0; k--)
		 {
            if ((k < nrt) & (e[k] != 0.0))
			{
               for (j = k+1; j < nu; j++)
			   {
                  T_REAL t = 0;
                  for (i = k+1; i < n; i++)
                     t += V[i][k]*V[i][j];
                  t = -t/V[k+1][k];
                  for (i = k+1; i < n; i++)
                     V[i][j] += t*V[i][k];
               }
            }
            for (i = 0; i < n; i++)
               V[i][k] = 0.0;
            V[k][k] = 1.0;
         }
      }

      // Main iteration loop for the singular values.
      int pp = p-1;
      int iter = 0;
      T_REAL eps = pow(2.0,-52.0);
      T_REAL tiny = pow(2.0,-966.0);
      while (p > 0)
	  {
         int kase;
         // Here is where a test for too many iterations would go.
         // This section of the program inspects for
         // negligible elements in the s and e arrays.  On
         // completion the variables kase and k are set as follows.
         // kase = 1     if s(p) and e[k-1] are negligible and k<p
         // kase = 2     if s(k) is negligible and k<p
         // kase = 3     if e[k-1] is negligible, k<p, and
         //              s(k), ..., s(p) are not negligible (qr step).
         // kase = 4     if e(p-1) is negligible (convergence).
         for (k = p-2; k >= -1; k--)
		 {
            if (k == -1)
               break;
            if (fabs(e[k]) <= tiny + eps*(fabs(s[k]) + fabs(s[k+1])))
			{
               e[k] = 0.0;
               break;
            }
         }
         if (k == p-2)
            kase = 4;
         else
		 {
            int ks;
            for (ks = p-1; ks >= k; ks--)
			{
               if (ks == k)
                  break;
               T_REAL t = (ks != p ? fabs(e[ks]) : 0.) + (ks != k+1 ? fabs(e[ks-1]) : 0.);
               if (fabs(s[ks]) <= tiny + eps*t)
			   {
                  s[ks] = 0.0;
                  break;
               }
            }
            if (ks == k)
               kase = 3;
            else if (ks == p-1)
               kase = 1;
            else
			{
               kase = 2;
               k = ks;
            }
         }
         k++;

         // Perform the task indicated by kase.
         switch (kase)
		 {
            // Deflate negligible s(p).
            case 1:
			{
               T_REAL f = e[p-2];
               e[p-2] = 0.0;
               for (j = p-2; j >= k; j--)
			   {
                  T_REAL t = HYPOTFUNC(s[j],f);
                  T_REAL cs = s[j]/t;
                  T_REAL sn = f/t;
                  s[j] = t;
                  if (j != k)
				  {
                     f = -sn*e[j-1];
                     e[j-1] = cs*e[j-1];
                  }
                  if (wantv)
				  {
                     for (i = 0; i < n; i++)
					 {
                        t = cs*V[i][j] + sn*V[i][p-1];
                        V[i][p-1] = -sn*V[i][j] + cs*V[i][p-1];
                        V[i][j] = t;
                     }
                  }
               }
            }
            break;

            // Split at negligible s(k).
            case 2:
			{
               T_REAL f = e[k-1];
               e[k-1] = 0.0;
               for (j = k; j < p; j++)
			   {
                  T_REAL t = HYPOTFUNC(s[j],f);
                  T_REAL cs = s[j]/t;
                  T_REAL sn = f/t;
                  s[j] = t;
                  f = -sn*e[j];
                  e[j] = cs*e[j];
                  if (wantu)
				  {
                     for (i = 0; i < m; i++)
					 {
                        t = cs*U[i][j] + sn*U[i][k-1];
                        U[i][k-1] = -sn*U[i][j] + cs*U[i][k-1];
                        U[i][j] = t;
                     }
                  }
               }
            }
            break;

            // Perform one qr step.
            case 3:
			{
               // Calculate the shift.
			   T_REAL scale = fabs(s[p-1]);
			   scale = fabs(s[p-2]) > scale ? fabs(s[p-2]) : scale;
			   scale = fabs(e[p-2]) > scale ? fabs(e[p-2]) : scale;
			   scale = fabs(s[k]) > scale ? fabs(s[k]) : scale;
			   scale = fabs(e[k]) > scale ? fabs(e[k]) : scale;
               T_REAL sp = s[p-1]/scale;
               T_REAL spm1 = s[p-2]/scale;
               T_REAL epm1 = e[p-2]/scale;
               T_REAL sk = s[k]/scale;
               T_REAL ek = e[k]/scale;
               T_REAL b = ((spm1 + sp)*(spm1 - sp) + epm1*epm1)/2.0;
               T_REAL c = (sp*epm1)*(sp*epm1);
               T_REAL shift = 0.0;
               if ((b != 0.0) | (c != 0.0))
			   {
                  shift = sqrt(b*b + c);
                  if (b < 0.0)
                     shift = -shift;
                  shift = c/(b + shift);
               }
               T_REAL f = (sk + sp)*(sk - sp) + shift;
               T_REAL g = sk*ek;
   
               // Chase zeros.
               for (j = k; j < p-1; j++)
			   {
                  T_REAL t = HYPOTFUNC(f,g);
                  T_REAL cs = f/t;
                  T_REAL sn = g/t;
                  if (j != k)
                     e[j-1] = t;
                  f = cs*s[j] + sn*e[j];
                  e[j] = cs*e[j] - sn*s[j];
                  g = sn*s[j+1];
                  s[j+1] = cs*s[j+1];
                  if (wantv)
				  {
                     for (i = 0; i < n; i++)
					 {
                        t = cs*V[i][j] + sn*V[i][j+1];
                        V[i][j+1] = -sn*V[i][j] + cs*V[i][j+1];
                        V[i][j] = t;
                     }
                  }
                  t = HYPOTFUNC(f,g);
                  cs = f/t;
                  sn = g/t;
                  s[j] = t;
                  f = cs*e[j] + sn*s[j+1];
                  s[j+1] = -sn*e[j] + cs*s[j+1];
                  g = sn*e[j+1];
                  e[j+1] = cs*e[j+1];
                  if (wantu && (j < m-1))
				  {
                     for (i = 0; i < m; i++)
					 {
                        t = cs*U[i][j] + sn*U[i][j+1];
                        U[i][j+1] = -sn*U[i][j] + cs*U[i][j+1];
                        U[i][j] = t;
                     }
                  }
               }
               e[p-2] = f;
               iter = iter + 1;
            }
            break;

            // Convergence.
            case 4:
			{
               // Make the singular values positive.
               if (s[k] <= 0.0)
			   {
                  s[k] = (s[k] < 0.0 ? -s[k] : 0.0);
                  if (wantv)
				  {
                     for (i = 0; i <= pp; i++)
                        V[i][k] = -V[i][k];
                  }
               }
   
               // Order the singular values.
               while (k < pp)
			   {
                  if (s[k] >= s[k+1])
                     break;
                  T_REAL t = s[k];
                  s[k] = s[k+1];
                  s[k+1] = t;
                  if (wantv && (k < n-1))
				  {
                     for (i = 0; i < n; i++)
					 {
                        t = V[i][k+1];
						V[i][k+1] = V[i][k];
						V[i][k] = t;
					 }
                  }
                  if (wantu && (k < m-1))
				  {
                     for (i = 0; i < m; i++)
					 {
                        t = U[i][k+1];
						U[i][k+1] = U[i][k];
						U[i][k] = t;
					 }
                  }
                  k++;
               }
               iter = 0;
               p--;
            }
            break;
         }
      }
	  delete [] e;
	  delete [] work;
	  return 0;
}

int CMatrix::LMatrixInverse(CMatrix* pinv)
{
	if (nrow!=ncol)		//not square matrix
		return 1;
	if (pinv->nrow!=nrow)
		return 1;
	if (pinv->ncol!=ncol)
		return 1;
	int i, j, k;
	T_REAL sum;
	T_REAL** ppa_inv = pinv->ppa;
	T_REAL* pcol = new T_REAL [ncol];
	//check if L is singular
	for (i=0; i<nrow; i++)
	{
		if (ppa[i][i]==0)		//singular
			return 2;
	}
	for (j=0; j<ncol; j++)
	{
		for (i=0; i<nrow; i++)
			pcol[i] = 0;
		pcol[j] = 1;
		//back substitution
		for (i=0; i<nrow; i++)
		{
			sum = pcol[i];
			for (k=0; k<i; k++)
				sum -= ppa[i][k]*ppa_inv[k][j];
			ppa_inv[i][j] = sum/ppa[i][i];
		}
	}
	delete [] pcol;
	return 0;
}

int CMatrix::LMatrixSolveVector(T_REAL* pb, T_REAL* px)
{
	//solver Lx = b where L is a lower triangle matrix and b is the right size vector
	if (nrow!=ncol)		//not square matrix
		return 1;
	int i, k;
	T_REAL sum;
	//back substitution
	for (i=0; i<nrow; i++)
	{
		if (ppa[i][i]==0)		//singular
			return 2;
		sum = pb[i];
		for (k=0; k<i; k++)
			sum -= ppa[i][k]*px[k];
		px[i] = sum/ppa[i][i];
	}
	return 0;
}

int CMatrix::LMatrixSolveMatrix(CMatrix* b, CMatrix* x)
{
	if (nrow!=ncol)		//not square matrix
		return 1;
	if (b->nrow!=ncol)
		return 1;
	if (x->nrow!=ncol)
		return 1;
	if (b->ncol!=x->ncol)
		return 1;
	int i, j, k;
	int nc = b->ncol;
	T_REAL sum;
	T_REAL** ppa_b = b->ppa;
	T_REAL** ppa_x = x->ppa;
	//check if L is singular
	for (i=0; i<nrow; i++)
	{
		if (ppa[i][i]==0)		//singular
			return 2;
	}
	for (j=0; j<nc; j++)
	{
		//back substitution
		for (i=0; i<nrow; i++)
		{
			sum = ppa_b[i][j];
			for (k=0; k<i; k++)
				sum -= ppa[i][k]*ppa_x[k][j];
			ppa_x[i][j] = sum/ppa[i][i];
		}
	}
	return 0;
}

int CMatrix::UMatrixSolveMatrix(CMatrix* b, CMatrix* x)
{
	if (nrow!=ncol)		//not square matrix
		return 1;
	if (b->nrow!=ncol)
		return 1;
	if (x->nrow!=ncol)
		return 1;
	if (b->ncol!=x->ncol)
		return 1;
	int i, j, k;
	int nc = b->ncol;
	T_REAL sum;
	T_REAL** ppa_b = b->ppa;
	T_REAL** ppa_x = x->ppa;
	//check if L is singular
	for (i=0; i<nrow; i++)
	{
		if (ppa[i][i]==0)		//singular
			return 2;
	}
	for (j=0; j<nc; j++)
	{
		//back substitution
		for (i=nrow-1; i>=0; i--)
		{
			sum = ppa_b[i][j];
			for (k=i+1; k<ncol; k++)
				sum -= ppa[i][k]*ppa_x[k][j];
			ppa_x[i][j] = sum/ppa[i][i];
		}
	}
	return 0;
}

void CMatrix::MultiplyBySelfTransposeOnRight(CMatrix* pprod)
{
	//pprod is the pointer to product matrix MxM^T, assume it has been allocated
	if (pprod->nrow!=nrow)
		return;
	if (pprod->ncol!=nrow)
		return;
	int i, j, k;
	T_REAL** ppap = pprod->ppa;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<nrow; j++)
		{
			ppap[i][j] = 0;
			for (k=0; k<ncol; k++)
				ppap[i][j] += ppa[i][k]*ppa[j][k];
		}
	}
}

void CMatrix::MultiplyBySelfTransposeOnLeft(CMatrix* pprod)
{
	//pprod is the pointer to product matrix M^TxM, assume it has been allocated
	if (pprod->nrow!=ncol)
		return;
	if (pprod->ncol!=ncol)
		return;
	int i, j, k;
	T_REAL** ppap = pprod->ppa;
	for (i=0; i<ncol; i++)
	{
		for (j=0; j<ncol; j++)
		{
			ppap[i][j] = 0;
			for (k=0; k<nrow; k++)
				ppap[i][j] += ppa[k][i]*ppa[k][j];
		}
	}
}

void CMatrix::MultiplyByMatrixOnRight(CMatrix* pright, CMatrix* pprod)
{
	//assume pright and pprod have been allocated
	//pright matrix should have ncol rows
	if (pright->nrow!=ncol)
		return;
	if (pprod->nrow!=nrow)
		return;
	if (pprod->ncol!=pright->ncol)
		return;
	int i, j, k;
	int nc = pright->ncol;
	T_REAL** ppar = pright->ppa;
	T_REAL** ppap = pprod->ppa;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<nc; j++)
		{
			ppap[i][j] = 0;
			for (k=0; k<ncol; k++)
				ppap[i][j] += ppa[i][k]*ppar[k][j];
		}
	}
}

void CMatrix::MultiplyByMatrixOnLeft(CMatrix* pleft, CMatrix* pprod)
{
	//assume pleft and pprod have been allocated
	//pleft matrix should have nrow columns
	if (pleft->ncol!=nrow)
		return;
	if (pprod->nrow!=pleft->nrow)
		return;
	if (pprod->ncol!=ncol)
		return;
	int i, j, k;
	int nr = pleft->nrow;
	T_REAL** ppal = pleft->ppa;
	T_REAL** ppap = pprod->ppa;
	for (i=0; i<nr; i++)
	{
		for (j=0; j<ncol; j++)
		{
			ppap[i][j] = 0;
			for (k=0; k<nrow; k++)
				ppap[i][j] += ppal[i][k]*ppa[k][j];
		}
	}
}

void CMatrix::TransposeMultiplyByMatrixOnRight(CMatrix* pright, CMatrix* pprod)
{
	//assume pright and pprod have been allocated
	//pright matrix should have nrow rows
	if (pright->nrow!=nrow)
		return;
	if (pprod->nrow!=ncol)
		return;
	if (pprod->ncol!=pright->ncol)
		return;
	int i, j, k;
	int nc = pright->ncol;
	T_REAL** ppar = pright->ppa;
	T_REAL** ppap = pprod->ppa;
	for (i=0; i<ncol; i++)
	{
		for (j=0; j<nc; j++)
		{
			ppap[i][j] = 0;
			for (k=0; k<nrow; k++)
				ppap[i][j] += ppa[k][i]*ppar[k][j];
		}
	}
}

void CMatrix::TransposeMultiplyByMatrixOnLeft(CMatrix* pleft, CMatrix* pprod)
{
	//assume pleft and pprod have been allocated
	//pleft matrix should have ncol columns
	if (pleft->ncol!=ncol)
		return;
	if (pprod->nrow!=pleft->nrow)
		return;
	if (pprod->ncol!=nrow)
		return;
	int i, j, k;
	int nr = pleft->nrow;
	T_REAL** ppal = pleft->ppa;
	T_REAL** ppap = pprod->ppa;
	for (i=0; i<nr; i++)
	{
		for (j=0; j<nrow; j++)
		{
			ppap[i][j] = 0;
			for (k=0; k<ncol; k++)
				ppap[i][j] += ppal[i][k]*ppa[j][k];
		}
	}
}

void CMatrix::MultiplyByVectorOnRight(T_REAL* pv, T_REAL* pvp)
{
	//pvp is the pointer to product vector MxV
	int i, j;
	for (i=0; i<nrow; i++)
	{
		pvp[i] = 0;
		for (j=0; j<ncol; j++)
			pvp[i] += ppa[i][j]*pv[j];
	}
}

void CMatrix::MultiplyByVectorOnLeft(T_REAL* pv, T_REAL* pvp)
{
	//pvp is the pointer to product vector VxM
	int i, j;
	for (j=0; j<ncol; j++)
	{
		pvp[j] = 0;
		for (i=0; i<nrow; i++)
			pvp[j] += pv[i]*ppa[i][j];
	}
}

void CMatrix::TransposeMultiplyByVectorOnRight(T_REAL* pv, T_REAL* pvp)
{
	//pvp is the pointer to product vector M^TxV
	int i, j;
	for (i=0; i<ncol; i++)
	{
		pvp[i] = 0;
		for (j=0; j<nrow; j++)
			pvp[i] += ppa[j][i]*pv[j];
	}
}

void CMatrix::AddMatrix(CMatrix* pm, CMatrix* ps)
{
	if (pm->nrow!=nrow)
		return;
	if (ps->nrow!=nrow)
		return;
	if (pm->ncol!=ncol)
		return;
	if (ps->ncol!=ncol)
		return;
	int i, j;
	T_REAL** ppa_m = pm->ppa;
	T_REAL** ppa_s = ps->ppa;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
			ppa_s[i][j] = ppa[i][j] + ppa_m[i][j];
	}
}

void CMatrix::SubtractMatrix(CMatrix* pm, CMatrix* pd)
{
	if (pm->nrow!=nrow)
		return;
	if (pd->nrow!=nrow)
		return;
	if (pm->ncol!=ncol)
		return;
	if (pd->ncol!=ncol)
		return;
	int i, j;
	T_REAL** ppa_m = pm->ppa;
	T_REAL** ppa_d = pd->ppa;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
			ppa_d[i][j] = ppa[i][j] - ppa_m[i][j];
	}
}

void CMatrix::SetAsIdentity()
{
	if (nrow!=ncol)
		return;
	int i, j;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
		{
			if (i==j)
				ppa[i][j] = 1;
			else
				ppa[i][j] = 0;
		}
	}
}

bool CMatrix::IsIdenticalTo(CMatrix* pm)
{
	T_REAL** ppa_m = pm->ppa;
	if (pm->nrow!=nrow)
		return false;
	if (pm->ncol!=ncol)
		return false;
	int i, j;
	T_REAL xmin = ppa[0][0];		//minimum element
	T_REAL xmax = xmin;				//maximum element
	T_REAL err;
	T_REAL err2 = 0;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
		{
			err = ppa_m[i][j] - ppa[i][j];
			err2 += err*err;
			if (ppa[i][j]<xmin)
				xmin = ppa[i][j];
			if (ppa[i][j]>xmax)
				xmax = ppa[i][j];
		}
	}
	err = xmax - xmin;
	if (err>0)
		err2 /= err;
	err2 /= nrow*ncol;
	return err2<1e-6;
}

int CMatrix::GaussianEliminationWithRowPivoting(T_REAL* pb, T_REAL* px)
{
	//solve the linear system of equations with row pivoting only
	//if ncol>nrow, or the number of independent eqns < nrow, px[] set to zero for last few variables
	//return 1 if rank < nrow
	bool brank = false;			//true if rank<nrow
	int i, j, k;
	int imax;
	T_REAL aijabs;
	T_REAL aijmax;
	T_REAL aswap;
	T_REAL fac;
	for (i=0; i<nrow; i++)
	{
		imax = i;
		aijmax = fabs(ppa[i][i]);
		for (k=i+1; k<nrow; k++)
		{
			aijabs = fabs(ppa[k][i]);
			if (aijabs > aijmax)
			{
				imax = k;
				aijmax = aijabs;
			}
		}
		if (aijmax==0)		//rank < nrow
		{
			brank = true;
			break;
		}
		if (imax!=i)	//swap
		{
			for (j=i; j<ncol; j++)
			{
				aswap = ppa[i][j];
				ppa[i][j] = ppa[imax][j];
				ppa[imax][j] = aswap;
			}
			aswap = pb[i];
			pb[i] = pb[imax];
			pb[imax] = aswap;
		}
		//elimimation
		for (k=i+1; k<nrow; k++)
		{
			fac = ppa[k][i]/ppa[i][i];
			for (j=i; j<ncol; j++)
				ppa[k][j] -= fac*ppa[i][j];
			pb[k] -= fac*pb[i];
		}
	}
	//set px[] to zero from i to ncol
	for (k=i; k<ncol; k++)
		px[k] = 0;
	//back substitution
	for (k=i-1; k>=0; k--)
	{
		aswap = 0;
		for (j=k+1; j<ncol; j++)
		{
			aswap += ppa[k][j]*px[j];
		}
		px[k] = (pb[k]-aswap)/ppa[k][k];
	}
	if (brank)
		return 1;
	return 0;
}

int CMatrix::GaussianEliminationWithFullPivoting(T_REAL* pb, T_REAL* px)
{
	//solve the linear system of equations with column pivoting and row pivoting it necessary
	//pb is the right hand side with nrow elements
	//px is the solution with ncol elements
	//applicable for a system with nrow<=ncol (equal or more unknows than equations)
	//for under-specified system, set leftover xi to zero
	//return number of those leftover xi's
	bool bfound;						//true if found a non-zero aij
	int i, j, k;
	int jmax;							//column index with maximum absolute value of aij
	int* pic2o = new int [ncol];		//mapping current index of px to previous index of px
	T_REAL* py = new T_REAL [ncol];		//current solution with column swapped
	T_REAL aijmax;						//maximum absolute value of aij
	T_REAL aijabs;						//absolute value of aij
	T_REAL aswap;						//aij for swap
	T_REAL fac;							//factor applied to a row for elimination
	for (i=0; i<ncol; i++)
		pic2o[i] = i;
	for (i=0; i<nrow; i++)
	{
		//column pivoting
		aijmax = fabs(ppa[i][i]);
		jmax = i;
		for (j=i+1; j<ncol; j++)
		{
			aijabs = fabs(ppa[i][j]);
			if (aijabs>aijmax)
			{
				aijmax = aijabs;
				jmax = j;
			}
		}
		if (aijmax<TINY)	//all aij close to zero, do row pivoting
		{
			bfound = false;
			for (k=i+1; k<nrow; k++)
			{
				for (j=i; j<ncol; j++)
				{
					if (fabs(ppa[k][j])>TINY)
					{
						bfound = true;
						break;
					}
				}
				if (bfound)
					break;
			}
			if (bfound)		//swap between row i and row k
			{
				for (j=i; j<ncol; j++)
				{
					aswap = ppa[i][j];
					ppa[i][j] = ppa[k][j];
					ppa[k][j] = aswap;
				}
				aswap = pb[i];
				pb[i] = pb[k];
				pb[k] = pb[i];
				//do column pivoting again
				aijmax = fabs(ppa[i][i]);
				jmax = i;
				for (j=i+1; j<ncol; j++)
				{
					aijabs = fabs(ppa[i][j]);
					if (aijabs>aijmax)
					{
						aijmax = aijabs;
						jmax = j;
					}
				}
			}
			else			//number of independent eqns < nrow
				break;
		}
		if (jmax!=i)		//swap between column i and column jmax
		{
			j = pic2o[i];
			pic2o[i] = pic2o[jmax];
			pic2o[jmax] = j;
			for (k=0; k<nrow; k++)
			{
				aswap = ppa[k][i];
				ppa[k][i] = ppa[k][jmax];
				ppa[k][jmax] = aswap;
			}
		}
		//do elimination
		for (k=i+1; k<nrow; k++)
		{
			fac = ppa[k][i]/ppa[i][i];
			for (j=i; j<ncol; j++)
				ppa[k][j] -= fac*ppa[i][j];
			pb[k] -= fac*pb[i];
		}
	}
	//set py from i to ncol
	for (k=i; k<ncol; k++)
		py[k] = 0;
	for (k=i-1; k>=0; k--)
	{
		aswap = 0;
		for (j=k+1; j<ncol; j++)
		{
			aswap += ppa[k][j]*py[j];
		}
		py[k] = (pb[k]-aswap)/ppa[k][k];
	}
	//convert from py to px
	for (j=0; j<ncol; j++)
		px[pic2o[j]] = py[j];
	delete [] pic2o;
	delete [] py;
	if (i<nrow)		//rank < nrow
	{
//		std::cout << "rank < nrow\n";
		for (k=i; k<nrow; k++)
		{
			if (fabs(pb[k])>TINY)
			{
//				std::cout << "Invalid right hand side\n";
				return 1;
			}
		}
	}
	return 0;
}

void CMatrix::SolveGrammianMatrix(CMatrix* pa, CMatrix* pb, CMatrix* pc)
{
	//Solve AX - XB = C  where pa=A, pb=B, pc=C, px=X
	//all matrices are of the square matrices of the same size (nrow==ncol)
	//X is the solution of this matrix
	if (nrow!=ncol)
		return;
	int i, j, k, n;
	int nx = nrow*nrow;		//number of unknowns to be solved
	T_REAL** ppa_a = pa->ppa;
	T_REAL** ppa_b = pb->ppa;
	T_REAL** ppa_c = pc->ppa;
	T_REAL* px = new T_REAL [nx];		//solution of exploded equations
	T_REAL* prhs = new T_REAL [nx];		//right hand side of exploded equations
	CMatrix m(nx,nx);		//matrix of exploded equations
	T_REAL** ppa_m = m.ppa;
	//set prhs and m to zero
	for (i=0; i<nx; i++)
	{
		prhs[i] = 0;
		for (j=0; j<nx; j++)
			ppa_m[i][j] = 0;
	}
	//assign m matrix elements
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<nrow; j++)
		{
			//i row and j column of C or i*nrow+j unknown
			n = i*nrow+j;
			prhs[n] = ppa_c[i][j];
			for (k=0; k<nrow; k++)
			{
				//ppa_a[i][k]*x[k][j]-x[i][k]*ppa_b[k][j] = ppa_c[i][j];
				ppa_m[n][k*nrow+j] += ppa_a[i][k];
				ppa_m[n][i*nrow+k] -= ppa_b[k][j];
			}
		}
	}
	//solve the linear equation
	m.GaussianEliminationWithFullPivoting(prhs,px);
	//map from px to this matrix
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<nrow; j++)
			ppa[i][j] = px[i*nrow+j];
	}
	//delete pointers
	delete [] px;
	delete [] prhs;
}

void CMatrix::SolveOriginalGrammianMatrix(CMatrix* pa, CMatrix* pb)
{
	//Solve X - A'XA = B  or A'XA - X = -B where pa=A, pb=B, px=X
	//all matrices are of the square matrices of the same size (nrow==ncol)
	//X is the solution of this matrix
	if (nrow!=ncol)
		return;
	int i, j, k, l, n, n1;
	int nx = nrow*nrow;		//number of unknowns to be solved
	T_REAL** ppa_a = pa->ppa;
	T_REAL** ppa_b = pb->ppa;
	T_REAL* px = new T_REAL [nx];		//solution of exploded equations
	T_REAL* prhs = new T_REAL [nx];		//right hand side of exploded equations
	CMatrix m(nx,nx);		//matrix of exploded equations
	T_REAL** ppa_m = m.ppa;
	//set prhs and m to zero
	for (i=0; i<nx; i++)
	{
		prhs[i] = 0;
		for (j=0; j<nx; j++)
			ppa_m[i][j] = 0;
	}
	//assign m matrix elements
	//loop through each matrix element
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<nrow; j++)
		{
			//i row and j column of B or i*nrow+j unknown
			n = i*nrow+j;
			prhs[n] = -ppa_b[i][j];
			//calculate exploded equation coefficient, one equation for each n or (i,j) pair
			for (k=0; k<nrow; k++)
			{
				for (l=0; l<nrow; l++)
				{
					n1 = k*nrow+l;
					ppa_m[n][n1] = ppa_a[k][i]*ppa_a[l][j];
				}
			}
			ppa_m[n][n] -= 1;
		}
	}
	//solve the linear equation
	m.GaussianEliminationWithFullPivoting(prhs,px);
	//map from px to this matrix
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<nrow; j++)
			ppa[i][j] = px[i*nrow+j];
	}
	//delete pointers
	delete [] px;
	delete [] prhs;
}

void CMatrix::SolveOriginalGrammianMatrixByHalf(CMatrix* pa, CMatrix* pb)
{
	//Solve X - A'XA = B  or A'XA - X = -B where pa=A, pb=B, px=X
	//all matrices are of the square matrices of the same size (nrow==ncol)
	//X is the solution of this matrix
	if (nrow!=ncol)
		return;
	int i, j, k, l, n, n1;
	int nx = nrow*(1+nrow)/2;		//number of unknowns to be solved
	T_REAL** ppa_a = pa->ppa;
	T_REAL** ppa_b = pb->ppa;
	T_REAL* px = new T_REAL [nx];		//solution of exploded equations
	T_REAL* prhs = new T_REAL [nx];		//right hand side of exploded equations
	CMatrix m(nx,nx);		//matrix of exploded equations
	T_REAL** ppa_m = m.ppa;
	//set prhs and m to zero
	for (i=0; i<nx; i++)
	{
		prhs[i] = 0;
		for (j=0; j<nx; j++)
			ppa_m[i][j] = 0;
	}
	//assign m matrix elements
	//loop through each matrix element
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<=i; j++)
		{
			//i row and j column of B or i*nrow+j unknown
			n = i*(1+i)/2+j;
			prhs[n] = -ppa_b[i][j];
			//calculate exploded equation coefficient, one equation for each n or (i,j) pair
			for (k=0; k<nrow; k++)
			{
				for (l=0; l<=k; l++)
				{
					n1 = k*(1+k)/2+l;
					if (k==l)
						ppa_m[n][n1] = ppa_a[k][i]*ppa_a[l][j];
					else
						ppa_m[n][n1] = ppa_a[k][i]*ppa_a[l][j] + ppa_a[l][i]*ppa_a[k][j];
				}
			}
			ppa_m[n][n] -= 1;
		}
	}
	//solve the linear equation
	m.GaussianEliminationWithFullPivoting(prhs,px);
	//map from px to this matrix
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<=i; j++)
			ppa[i][j] = px[i*(1+i)/2+j];
	}
	//copy to upper right corner
	for (i=0; i<nrow; i++)
	{
		for (j=i+1; j<nrow; j++)
			ppa[i][j] =ppa[j][i];
	}
	//delete pointers
	delete [] px;
	delete [] prhs;
}

void CMatrix::WriteText(FILE* pf)
{
	int i, j;
	int iversion = 0;
	int iallocated;
	if (ppa!=NULL)
		iallocated = 1;
	else
		iallocated = 0;
	fprintf(pf,"%d\t//version number\n",iversion);
	fprintf(pf,"%d\t//number of rows\n",nrow);
	fprintf(pf,"%d\t//number of columns\n",ncol);
	fprintf(pf,"%d\t//0 if empty, 1 if contains elements\n",iallocated);
	if (iallocated)
	{
		for (i=0; i<nrow; i++)
		{
			fprintf(pf,"%lg",ppa[i][0]);
			for (j=1; j<ncol; j++)
				fprintf(pf,"\t%lg",ppa[i][j]);
			fprintf(pf,"\n");
		}
	}
}

void CMatrix::ReadText(FILE* pf)
{
	int i, j;
	int iversion;
	int iallocated;
	char line[500];
	fscanf(pf,"%d",&iversion);
	fgets(line,499,pf);
	fscanf(pf,"%d",&nrow);
	fgets(line,499,pf);
	fscanf(pf,"%d",&ncol);
	fgets(line,499,pf);
	fscanf(pf,"%d",&iallocated);
	fgets(line,499,pf);
	if (iallocated)
	{
		AllocateMemory();
		for (i=0; i<nrow; i++)
		{
			for (j=0; j<ncol; j++)
				fscanf(pf,"%lg",&ppa[i][j]);
		}
	}
}

bool CMatrix::CheckElements()
{
	int i, j;
	for (i=0; i<nrow; i++)
	{
		for (j=0; j<ncol; j++)
		{
			if (!_finite(ppa[i][j]))
				return false;
		}
	}
	return true;
}