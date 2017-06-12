//DABNetInput.cpp
#include "DABNetInput.h"

CDabnetInput::CDabnetInput()
{
	ipredict_opt = 1;
	itrain_lag_opt = 0;
	itrain_red_opt = 0;
	iscale_lag_opt = 1;		//It seems that scaling state variable makes error lower and without flatting out with weight/sigma used for balanced realization
	iscale_red_opt = 1;
	nmax_iter_ipopt_lag = 3000;
	nmax_iter_ipopt_red = 6000;
	nmax_iter_bp_lag = 5000;
	nmax_iter_bp_red = 10000;
	weight_init = 0.01;
}

CDabnetInput::~CDabnetInput()
{
}

CDabnetInput::CDabnetInput(const CDabnetInput &t)
{
	ipredict_opt = t.ipredict_opt;
	itrain_lag_opt = t.itrain_lag_opt;
	itrain_red_opt = t.itrain_red_opt;
	iscale_lag_opt = t.iscale_lag_opt;
	iscale_red_opt = t.iscale_red_opt;
	nmax_iter_ipopt_lag = t.nmax_iter_ipopt_lag;
	nmax_iter_ipopt_red = t.nmax_iter_ipopt_red;
	nmax_iter_bp_lag = t.nmax_iter_bp_lag;
	nmax_iter_bp_red = t.nmax_iter_bp_red;
	weight_init = t.weight_init;
}

CDabnetInput& CDabnetInput::operator=(const CDabnetInput& t)
{
	if (this==&t)
		return *this;
	ipredict_opt = t.ipredict_opt;
	itrain_lag_opt = t.itrain_lag_opt;
	itrain_red_opt = t.itrain_red_opt;
	iscale_lag_opt = t.iscale_lag_opt;
	iscale_red_opt = t.iscale_red_opt;
	nmax_iter_ipopt_lag = t.nmax_iter_ipopt_lag;
	nmax_iter_ipopt_red = t.nmax_iter_ipopt_red;
	nmax_iter_bp_lag = t.nmax_iter_bp_lag;
	nmax_iter_bp_red = t.nmax_iter_bp_red;
	weight_init = t.weight_init;
	return *this;
}
