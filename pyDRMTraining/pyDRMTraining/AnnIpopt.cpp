// Copyright (C) 2005, 2006 International Business Machines and others.
// All Rights Reserved.
// This code is published under the Eclipse Public License.
//
// $Id: hs071_nlp.cpp 2005 2011-06-06 12:55:16Z stefan $
//
// Authors:  Carl Laird, Andreas Waechter     IBM    2005-08-16
#include "AnnIpopt.h"

#include <cassert>
#include <iostream>

using namespace Ipopt;

// constructor
CAnnIpopt::CAnnIpopt()
{
	icount = 0;
	pann = NULL;
	pdc = NULL;
}

//destructor
CAnnIpopt::~CAnnIpopt()
{
}

// returns the size of the problem
bool CAnnIpopt::get_nlp_info(Index& n, Index& m, Index& nnz_jac_g,
                             Index& nnz_h_lag, IndexStyleEnum& index_style)
{
  // size of x vector is the number of weights or connections
  n = pann->GetNumberOfWeights();

  // no constraints
  m = 0;

  // no constraint jacobian
  nnz_jac_g = 0;

  // the hessian is dense and has n^2
  // only need the lower left corner (since it is symmetric)
  nnz_h_lag = pann->GetHessianNonzeroCount();

  // use the C style indexing (0-based)
  index_style = TNLP::C_STYLE;

  return true;
}

// returns the variable bounds
bool CAnnIpopt::get_bounds_info(Index n, Number* x_l, Number* x_u,
                                Index m, Number* g_l, Number* g_u)
{
  // here, the n and m we gave IPOPT in get_nlp_info are passed back to us.
  // If desired, we could assert to make sure they are what we think they are.

  // the variables have lower bounds
  for (Index i=0; i<n; i++) {
    x_l[i] = -10;
  }

  // the variables have upper bounds
  for (Index i=0; i<n; i++) {
    x_u[i] = 10;
  }

  // the first constraint g1 has a lower bound of 25
  //g_l[0] = 25;
  // the first constraint g1 has NO upper bound, here we set it to 2e19.
  // Ipopt interprets any number greater than nlp_upper_bound_inf as
  // infinity. The default value of nlp_upper_bound_inf and nlp_lower_bound_inf
  // is 1e19 and can be changed through ipopt options.
  //g_u[0] = 2e19;

  // the second constraint g2 is an equality constraint, so we set the
  // upper and lower bound to the same value
  //g_l[1] = g_u[1] = 40.0;

  return true;
}

// returns the initial point for the problem
bool CAnnIpopt::get_starting_point(Index n, bool init_x, Number* x,
                                   bool init_z, Number* z_L, Number* z_U,
                                   Index m, bool init_lambda,
                                   Number* lambda)
{
  // Here, we assume we only have starting values for x, if you code
  // your own NLP, you can provide starting values for the dual variables
  // if you wish
  assert(init_x == true);
  assert(init_z == false);
  assert(init_lambda == false);

  // initialize to the given starting point
  pann->InitWeightsForIpopt(x);

  return true;
}

// returns the value of the objective function
bool CAnnIpopt::eval_f(Index n, const Number* x, bool new_x, Number& obj_value)
{
  obj_value = pann->CalcBatchErrorUsingGivenWeights(x, pdc);

  return true;
}

// return the gradient of the objective function grad_{x} f(x)
bool CAnnIpopt::eval_grad_f(Index n, const Number* x, bool new_x, Number* grad_f)
{
	pann->CalcBatchGradientUsingGivenWeights(x, pdc, grad_f);
	return true;
}

// return the value of the constraints: g(x)
bool CAnnIpopt::eval_g(Index n, const Number* x, bool new_x, Index m, Number* g)
{

  //g[0] = x[0] * x[1] * x[2] * x[3];
  //g[1] = x[0]*x[0] + x[1]*x[1] + x[2]*x[2] + x[3]*x[3];

  return true;
}

// return the structure or values of the jacobian
bool CAnnIpopt::eval_jac_g(Index n, const Number* x, bool new_x,
                           Index m, Index nele_jac, Index* iRow, Index *jCol,
                           Number* values)
{
  /*
  if (values == NULL) {
    // return the structure of the jacobian

    // this particular jacobian is dense
    iRow[0] = 0;
    jCol[0] = 0;
    iRow[1] = 0;
    jCol[1] = 1;
    iRow[2] = 0;
    jCol[2] = 2;
    iRow[3] = 0;
    jCol[3] = 3;
    iRow[4] = 1;
    jCol[4] = 0;
    iRow[5] = 1;
    jCol[5] = 1;
    iRow[6] = 1;
    jCol[6] = 2;
    iRow[7] = 1;
    jCol[7] = 3;
  }
  else {
    // return the values of the jacobian of the constraints

    values[0] = x[1]*x[2]*x[3]; // 0,0
    values[1] = x[0]*x[2]*x[3]; // 0,1
    values[2] = x[0]*x[1]*x[3]; // 0,2
    values[3] = x[0]*x[1]*x[2]; // 0,3

    values[4] = 2*x[0]; // 1,0
    values[5] = 2*x[1]; // 1,1
    values[6] = 2*x[2]; // 1,2
    values[7] = 2*x[3]; // 1,3
  }
  */
  return true;
}

//return the structure or values of the hessian
bool CAnnIpopt::eval_h(Index n, const Number* x, bool new_x,
                       Number obj_factor, Index m, const Number* lambda,
                       bool new_lambda, Index nele_hess, Index* iRow,
                       Index* jCol, Number* values)
{
  if (values == NULL) {
    // return the structure. This is a symmetric matrix, fill the lower left
    // triangle only.

    // the hessian for this problem is actually dense except the output layer
	  pann->GetHessianNonzeroIndices(iRow, jCol);
  }
  else {
    // return the values. This is a symmetric matrix, fill the lower left
    // triangle only

    // fill the objective portion
	  pann->CalcBatchHessianUsingGivenWeights(x, pdc, values);
	  for (int i=0; i<nele_hess; i++)
		values[i] *= obj_factor;
	  
	  //count number of calls
	  icount++;
	  if (icount%100==0)
	  {
		  //write batch error to log string
		  printf("Average Error at Iteration %d = %lg\n",icount,pann->GetBatchError()/pdc->npair);
	  }

    // add the portion for the first constraint
	/*
    values[1] += lambda[0] * (x[2] * x[3]); // 1,0

    values[3] += lambda[0] * (x[1] * x[3]); // 2,0
    values[4] += lambda[0] * (x[0] * x[3]); // 2,1

    values[6] += lambda[0] * (x[1] * x[2]); // 3,0
    values[7] += lambda[0] * (x[0] * x[2]); // 3,1
    values[8] += lambda[0] * (x[0] * x[1]); // 3,2

    // add the portion for the second constraint
    values[0] += lambda[1] * 2; // 0,0

    values[2] += lambda[1] * 2; // 1,1

    values[5] += lambda[1] * 2; // 2,2

    values[9] += lambda[1] * 2; // 3,3
	*/
  }

  return true;
}

void CAnnIpopt::finalize_solution(SolverReturn status,
                                  Index n, const Number* x, const Number* z_L, const Number* z_U,
                                  Index m, const Number* g, const Number* lambda,
                                  Number obj_value,
				  const IpoptData* ip_data,
				  IpoptCalculatedQuantities* ip_cq)
{
  // here is where we would store the solution to variables, or write to a file, etc
  // so we could use the solution.
	double* px = pann->GetWeightPointer();
	for (Index i=0; i<n; i++)
		px[i] = x[i];
	printf("Objective value is %lg.\n",obj_value);
}
