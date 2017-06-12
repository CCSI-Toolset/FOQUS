//LHS.h

#ifndef __LHS_H__
#define __LHS_H__

class CLHS
{
private:
	int	ndim;				//number of dimension
	int npoint;				//number of points
	int** ppx;				//LSH samples
	void DeleteSampleArray();

public:
	CLHS();
	CLHS(int nd, int np);
	virtual ~CLHS();
	CLHS(const CLHS &t);
	CLHS& operator=(const CLHS& t);
	void AllocateSampleArray();
	void SetDimension(int n);
	void SetNumberOfPoints(int n);
	void SimpleSampling();
	void GivenFirstSampling(int* p1st);
	int GetDimension() {return ndim;}
	int GetNumberOfPoints() {return npoint;}
	int** GetLHSPoints() {return ppx;}
	double CalcQualityPhi(double p);
};

#endif