//SolverInput.h

// Usage of this class
// 1. Create a new class and provide pinput_list_all array
// 2. Call EnableReverse() to set ireverse
// 3. Call SetDimension() to set ndim
// 4. Call SetNumberOfPoints() to set npoint
// 5. Call SetNumberOfDurations() to set nduration
// 6. Call SetInitialDuration() to set duration0 (default is 5), could skip if default is used
// 7. Assign public members of vduration, vbvaried, vxdefault, vxlower, vxupper vectors, optionally call CheckVariedInputDimension()
// 8. Call GenerateTrainingSequence() which calls ts.SetSizeAll(ndim, npoint, nduration), ts.SetDefaultStartingPoint(), and ts.SelectBestSampling(ntry)
// 9. Call PrepareSequenceVectorForACMInputArray()
// 10. The sampling result is vsequence
//
#ifndef __SOLVERINPUT_H__
#define __SOLVERINPUT_H__

#include <vector>
#include "TrainSequence.h"

class CSolverInput
{
private:
	int ireverse;									//add reverse order points, 1 if true
	int	ndim;										//number of dimension
	int npoint;										//number of points
	int nduration;									//number of durations
	int duration0;									//initial condition duration in term of number of samplings
	int nstep;										//number of time steps in the training sequence
	CTrainSequence ts;								//train sequence
public:
	std::vector<int> vduration;						//duration in term of number of samplings, size = nduration
	std::vector<bool> vbvaried;						//bvaried vector
	std::vector<double> vxdefault;					//xdefault vector
	std::vector<double> vxlower;						//xlower vector
	std::vector<double> vxupper;						//xupper vector
	std::vector<double> vsequence;					//vector represnting 2-D input sequence array, to be used by MATLAB for ACM

public:
	CSolverInput();
	virtual ~CSolverInput();
	void EnableReverse(int i) {ireverse = i;}
	void SetDimension(int n) {ndim = n;}
	void SetNumberOfPoints(int n) {npoint = n;}
	void SetNumberOfDurations(int n) {nduration = n;}
	void SetInitialDuration(int n) {duration0 = n;}
	bool CheckVariedInputDimension();
	int GetReverseFlag() {return ireverse;}
	int GetDimension() {return ndim;}
	int GetNumberOfPoints() {return npoint;}
	int GetNumberOfDurations() {return nduration;}
	int GetInitialDuration() {return duration0;}
	int GetNumberOfTrainingSteps() {return nstep;}
	void GenerateTrainingSequence();
	void PrepareSequenceVectorForACMInputArray();
};

#endif