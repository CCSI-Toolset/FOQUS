// Matrix.h: interface for the CMatrix class.
//
//////////////////////////////////////////////////////////////////////
#ifndef __MATRIX_H__
#define __MATRIX_H__

#include "CCSI.h"

class CMatrix
{
public:
	int nrow;			//number of rows
	int ncol;			//number of columns
	T_REAL** ppa;		//2-D array of float or double, column major

public:
	CMatrix();
	CMatrix(int nr, int nc);
	CMatrix(int nr, int nc, T_REAL** pp);
	virtual ~CMatrix();
	CMatrix(const CMatrix &t);
	CMatrix& operator=(const CMatrix& t);
	void SetDimensions(int irow, int icol) {nrow=irow; ncol=icol;}
	void AllocateMemory();
	void DeleteMemory();
	void SetAllElementsTo(T_REAL x);
	void SetElementTo(int i, int j, T_REAL x) {ppa[i][j] = x;}
	void Transpose(CMatrix* t);
	int LUDecompose(int* pindex);
	void LUBackSubstitute(int* pindex, T_REAL* pb);
	int LUInverse(CMatrix* pinv);
	T_REAL LUDeterminant();
	bool CholeskyDecompose(CMatrix* c);
	void QRDecompose(CMatrix* q, CMatrix* r);
	int SingularValueDecomposition(bool wantu, bool wantv, CMatrix* mu, CMatrix* mv, T_REAL* s);
	int LMatrixInverse(CMatrix* pinv);
	int LMatrixSolveVector(T_REAL* pb, T_REAL* px);
	int LMatrixSolveMatrix(CMatrix* b, CMatrix* x);
	int UMatrixSolveMatrix(CMatrix* b, CMatrix* x);
	void MultiplyBySelfTransposeOnRight(CMatrix* pprod);
	void MultiplyBySelfTransposeOnLeft(CMatrix* pprod);
	void MultiplyByMatrixOnRight(CMatrix* pright, CMatrix* pprod);
	void MultiplyByMatrixOnLeft(CMatrix* pleft, CMatrix* pprod);
	void TransposeMultiplyByMatrixOnRight(CMatrix* pright, CMatrix* pprod);
	void TransposeMultiplyByMatrixOnLeft(CMatrix* pleft, CMatrix* pprod);
	void MultiplyByVectorOnRight(T_REAL* pv, T_REAL* pvp);
	void MultiplyByVectorOnLeft(T_REAL* pv, T_REAL* pvp);
	void TransposeMultiplyByVectorOnRight(T_REAL* pv, T_REAL* pvp);
	void AddMatrix(CMatrix* pm, CMatrix* ps);
	void SubtractMatrix(CMatrix* pm, CMatrix* pd);
	void SetAsIdentity();
	bool IsIdenticalTo(CMatrix* pm);
	int GaussianEliminationWithRowPivoting(T_REAL* pb, T_REAL* px);
	int GaussianEliminationWithFullPivoting(T_REAL* pb, T_REAL* px);
	void SolveGrammianMatrix(CMatrix* pa, CMatrix* pb, CMatrix* pc);
	void SolveOriginalGrammianMatrix(CMatrix* pa, CMatrix* pb);
	void SolveOriginalGrammianMatrixByHalf(CMatrix* pa, CMatrix* pb);
	void WriteText(FILE* pf);
	void ReadText(FILE* pf);
	bool CheckElements();
};

#endif