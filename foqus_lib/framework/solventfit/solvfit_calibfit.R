suppressPackageStartupMessages(library(abind))
suppressPackageStartupMessages(library(methods))             # required for is() when invoked using Rscript
source('solvfit_emulfit.R')  # "interactive" must be set to 0 in that file

###############################################################
# SOLVENTFIT CALIBRATION FITTING
###############################################################

SolventFit_calib=function(Ninp,Npar,Nout,Xs,Ys,expdat,model.func=NULL,
                          incl.em=T,burnin.em=0,nmcmc.em=10000,thinby.em=1,nterms.em=25,order.em=2,priorprob.em=0.5,Ngrid.em=500,
                          incl.ptmass=F,priorsfile=NULL,initsfile=NULL,burnin.cal=0,nmcmc.cal=10000,thinby.cal=1,
                          incl.disc=T,nterms.disc=25,order.disc=2,Ngrid.disc=500,oldcalib=NULL,adaptcov=T){
                          	
 ##########################################
### Use old restart 
##########################################	
if (!is.null(oldcalib)){
    
    calibinputs=oldcalib$inputs;
	
#update initial values
	nsamps=nrow(oldcalib$calibout$chain$theta);		
	calibinputs$inits$theta=trans.pred(oldcalib$calibout$chain$theta[nsamps-1,1:Npar,drop=F],calibinputs$ctrl1$mod$thlim);
	calibinputs$inits$dummy=oldcalib$calibout$chain$dummy[nsamps-1,,drop=F];
	calibinputs$inits$pars=oldcalib$calibout$chain$pars[nsamps-1,,drop=F];
	calibinputs$inits$sigma=as.matrix(oldcalib$calibout$chain$sigma[nsamps-1,,,drop=F]);
	calibinputs$inits$BigCov$theta=oldcalib$calibout$BigCovtheta;

	 if (incl.disc) {calibinputs$inits$disc=oldcalib$calibout$chain$disc[nsamps-1,,,drop=F];}
	
	calibinputs$ctrl1$niter=nmcmc.cal;  calibinputs$ctrl1$thinby=thinby.cal;
	calibinputs$ctrl1$adapt$yes=0;

	out1=MCMC1(zvec=calibinputs$zvec,priors=calibinputs$priors,inits=calibinputs$inits,ctrl1=calibinputs$ctrl1,eval1=calibinputs$eval1,fileVar=calibinputs$fileVar);	

	out1$frontend.disc=calibinputs$ctrl1$disc$frontend;
	if (calibinputs$ctrl1$mod$incl.em) {out1$betamatem=calibinputs$ctrl1$mod$betamat;}

	return(list(emulout=oldcalib$emulout,calibout=out1,inputs=calibinputs));   
    }  
    
 #########################################
  ### Put in hack if Ninp=0
  #########################################	
  #if (Ninp==0){
  #	expdat=cbind(matrix(0.5,nrow(expdat),1),expdat);
  #	Xs=cbind(matrix(-999.999,nrow(Xs),1),Xs);
  #	Ninp=1;
  #}    

 #########################################
  ### Set up data matrices and other stuff 
  #########################################	
  ymatraw=as.matrix(expdat[,(1:Nout)+Ninp,drop=F]);

  # get input matrix for discrepancy     
  Xmat.discraw=as.matrix(expdat[,1:Ninp,drop=F]);                          	
  if (Ninp==0) Xmat.discraw=matrix(0,nrow(expdat),0); 
  
  ########################################
  ### Set up limits, initial points and priors 
  ########################################
  
  initsout=getdefaults(Npar,Nout,incl.ptmass,adaptcov);
  inits=initsout$inits; priors=initsout$priors; ctrl1=initsout$ctrl1;
  if (incl.em){
  	inits$Xlim=trans.input(Xs)$lim; inits$Ylim=trans.output(Ys)$lim;
  }	
  if (!incl.em){
  	priorsmatrnew=as.matrix(read.table(priorsfile));
  	inits$Xlim=t(priorsmatrnew[4:5,1:Npar,drop=F]);
  	if (!is.null(model.func$thlim)) {inits$Xlim[1,]=(model.func$thlim);}
  	#R.j=(inits$Xlim[,2]-inits$Xlim[,1])/0.8;
  	#min.j=(inits$Xlim[,1]+inits$Xlim[,2]-R.j)/2;
  	inits$Xlim[,2]=(inits$Xlim[,2]-inits$Xlim[,1]);
  	inits$Xlim=rbind(trans.input(Xmat.discraw)$lim,inits$Xlim);
  	inits$Ylim=trans.output(ymatraw)$lim;
  }	
    ctrl1$mod$thlim=inits$Xlim[(1:Npar)+Ninp,,drop=F];
  	ctrl1$mod$Y.lim=inits$Ylim;
  	
  	#fix inits$Xlim if Ninp=0;
  
    ####################################
  ### Set up discrepancy
  ####################################
  Xmat.disc=Xmat.discraw; 
  if (Ninp>0){
  	Xmat.disc=trans.pred(Xmat=Xmat.disc,X.lim=inits$Xlim[1:Ninp,,drop=F]);
  }
  ctrl1$disc$Xmat=Xmat.discraw;  
  if (incl.disc){
    ctrl1$disc$N.eig=rep(nterms.disc,order.disc);
    ctrl1$disc$inclmat$incl=matrix(0,1,0); ctrl1$disc$inclmat$neig=0; #correct for the zero input case
    if (Ninp>0) ctrl1$disc$inclmat=get.inclmat(numvar=ncol(Xmat.discraw),N.eig=ctrl1$disc$N.eig);
    inits$disc=array(0,c(1+sum(ctrl1$disc$inclmat$neig),Nout));
    ctrl1$disc$N.grid=Ngrid.disc;   ctrl1$disc$max.ord=c(25,8,6,4);
    ctrl1$disc$frontend=MCMCfrontend(Xs=Xmat.discraw,Ys=ymatraw,N.grid=ctrl1$disc$N.grid,N.eig=ctrl1$disc$N.eig,max.ord=ctrl1$disc$max.ord,X.lim=inits$Xlim[1:Ninp,,drop=F],Y.lim=inits$Ylim,inclmat=ctrl1$disc$inclmat);
   
     ## prior for coefficient covariance matrix Lambda
     priors$disc$Lambda$nu=4; priors$disc$Lambda$mu=1*diag(rep(1,Nout),nrow=Nout);
  }   

########################################################################
### Do the emulation if required and set up model#####
########################################################################
	#setwd(foldx);
	emulout=0; 
	if (incl.em)
	{	
		#emulout=SolventFit_emul(Ninp,Npar,Nout,foldx,modoutfile,burnin=0,nmcmc=nmcmc.em,nterms=nterms.em,thinby=thinby.em,order=order.em,priorprob=0.5,N.grid=Ngrid.em);						
		emulout=SolventFit_emul(Xs,Ys,burnin=burnin.em,nmcmc=nmcmc.em,nterms=nterms.em,thinby=thinby.em,order=order.em,priorprob=0.5,N.grid=Ngrid.em,X.lim=inits$Xlim,Y.lim=inits$Ylim);
		
        ymat=trans.output(Ymat=ymatraw,Y.lim=inits$Ylim)$trans;
		
		ctrl1$mod$frontend=emulout$frontend;
		ctrl1$mod$Xsinput=Xmat.disc;
		ctrl1$mod$ord1inp=array(0,dim=c(nrow(Xmat.disc),0,0));
		if (Ninp>0) ctrl1$mod$ord1inp=get1ordinp(Xsinput=Xmat.disc,frontend=emulout$frontend);
		betamatr.raw=emulout$postdist$beta;
		ctrl1$mod$betamat=betamatr.raw[nmcmc.em-15*(1:50),,,drop=F];
		#pars=list(); pars$theta=default.trans;
		#aa=modelfunc(pars=pars,ctrl1,fileVar,type=1)
	}
	if (!incl.em) 
	{
		ctrl1$mod$name=model.func$name;
		ctrl1$mod$inputs$Xmat=matrix(0,nrow=nrow(Xmat.discraw),ncol=Ninp+Npar);
		ctrl1$mod$inputs$Xmat[,1:Ninp]=Xmat.discraw;
		if (!is.null(model.func$other)) ctrl1$mod$inputs$other=model.func$other;
		ctrl1$mod$Ninp=Ninp; ctrl1$mod$Npar=Npar;
		ymat=trans.output(Ymat=ymatraw,Y.lim=inits$Ylim)$trans;
		#Xmat.disc=trans.input(Xmat=Xmat.discraw,X.lim=ctrl1$disc$frontend$X.trans$lim)$trans;		
		}
	ctrl1$mod$incl.em=incl.em;  #set parameters to determine whether emulator should be run	
####################################
### Update initial points and priors ###
####################################
	if (!is.null(initsfile)){
	 	initsmatrnew=as.matrix(read.table(initsfile));
	 	inits=setupinits(initsmatrnew,inits,incl.ptmass,ctrl1$mod$thlim,inits$Ylim);
	 	}
	if (!is.null(priorsfile)){
		priorsmatrnew=as.matrix(read.table(priorsfile));
		priors=setuppriors(priorsmatrnew,priors,incl.ptmass,ctrl1$mod$thlim,inits$Ylim);
		}
	inits$sigma=diag(inits$sigma,nrow=length(inits$sigma));
    #update fixed variables
    inits$theta[priors$theta$type==0]=priors$theta$pribds$a1[priors$theta$type==0];
	inits$samplevec$theta[priors$theta$type==0]=0;

  eval1=list(); eval1$theta=1; eval1$pars=0; eval1$disc=incl.disc;
  ctrl1$kk=c(5000,5000,5000);
  ctrl1$niter=nmcmc.cal;  ctrl1$thinby=thinby.cal; ctrl1$burnin=burnin.cal; ctrl1$nprint=1e15;
  ctrl1$incl.em=incl.em;
  
  # output files
  outfile=list();
  foldx='./'
  outfile$theta='solvfit_thetaout.txt';
  outfile$pars='solvfit_parsout.txt';
  outfile$disc='solvfit_discout.txt';
  
  fileVar=list();  fileVar$outfile=outfile; fileVar$fold1=foldx;
  calibinputs=list(zvec=ymat,priors=priors,inits=inits,ctrl1=ctrl1,eval1=eval1,fileVar=fileVar);
  
  print("Start Calibration MCMC");
  out1=MCMC1(zvec=ymat,priors=priors,inits=inits,ctrl1=ctrl1,eval1=eval1,fileVar=fileVar);	
  print("Finish Calibration MCMC");
  out1$frontend.disc=ctrl1$disc$frontend;
  if (incl.em) {out1$betamatem=ctrl1$mod$betamat;}
  
  #account for burn-in
  
  return(list(emulout=emulout,calibout=out1,inputs=calibinputs));
  
}

########################
# Support functions
########################

MCMC1=function(zvec,priors,inits,ctrl1,eval1,fileVar)
{
	#print(ctrl1$adapt$yes);	
	#source("solvfit_emul_func_1.R",local=T);
	Ninp=ncol(ctrl1$disc$Xmat); Npar=length(inits$theta); Nout=ncol(zvec);
	len1=list(); chain=list(); pars=list(); acc=list();
	len1$theta=length(inits$theta); len1$pars=length(inits$pars);  len1$disc=length(inits$disc);
	len=len1$theta+len1$pars+len1$disc;	
	chain$theta=matrix(0,ctrl1$niter/ctrl1$thinby,len1$theta+2);
	#thetaraw=backtrans.input(Xmat=inits$theta,X.lim=ctrl1$mod$thlim);
	thetaraw=inits$theta;
	#chain$theta[1,]=c(thetaraw,inits$sigma,0,0);
	chain$theta[1,]=c(thetaraw,0,0); 
	chain$dummy=matrix(0,ctrl1$niter/ctrl1$thinby,len1$theta);
	chain$dummy[1,]=c(inits$dummy);
	chain$pars=matrix(0,ctrl1$niter/ctrl1$thinby,len1$pars);
	chain$sigma=array(0,c(ctrl1$niter/ctrl1$thinby,Nout,Nout));
	#chain$sigma[1,,]=diag(inits$sigma,nrow=length(inits$sigma));	
	chain$sigma[1,,]=inits$sigma; 
	#for convienience initialize temporary variables 
  	pars$theta=inits$theta;  pars$pars=inits$pars;  pars$disc=inits$disc; pars$sigma=inits$sigma; 
  	pars$dummy=inits$dummy;  #pars$sigma=diag(inits$sigma,nrow=length(inits$sigma));
  	nprint=ctrl1$nprint; #how often to write to file
  	adapt=ctrl1$adapt;
	
	#compute initial likelihood
	loglikinit=list();  loglikinit$yvec=matrix(0,nrow(zvec),ncol(zvec)); loglikinit$resids=zvec;
	#sigmapost1=priors$sigma$a1+nrow(zvec)/2; sigmapost2=priors$sigma$a2+sum(loglikinit$resids^2)/2;
	loglik=getlikl(pars,zvec,ctrl1,fileVar,loglikinit);
	BigCovtheta=inits$BigCov$theta; #BigCovpars=inits$BigCov$pars;
	#BigCovdisc=inits$BigCov$disc;
	
	chain$theta[1,len1$theta+1]=loglik$lik; chain$theta[1,len1$theta+1]=sum((zvec-loglik$yvec)^2);
	acc$theta=vector("numeric",length=len1$theta+1); acc$pars=vector("numeric",length=len1$pars);
	acc$varupd=acc$theta;   acc$covupd=acc$theta;
	
	#conpute constant, StateVar objects
	const=list(); StateVar=list(); 
	
    const$ctrl1=ctrl1; const$fileVar=fileVar;  const$kk=ctrl1$kk; #const$stand=ctrl1$stand;
    StateVar$savedMHden=loglik$lik; StateVar$togg=0; StateVar$acc=acc;
    #StateVar$BigCovpars=BigCovpars;
    	if (eval1$disc) 
	{	
		X.disc=ctrl1$disc$frontend$X.em;
		
		#initialize posterior sample chains
		chain$disc=array(0,c(ctrl1$niter/ctrl1$thinby+1,ncol(X.disc),Nout));
		chain$Lambda=array(1,c(ctrl1$niter/ctrl1$thinby+1,ncol(X.disc),Nout,Nout));
		#initial values for beta, Lambda, Sigma from priors
		#pars$disc=as.matrix(chain$disc[1,]);
		pars$disc=as.matrix(chain$disc[1,,]);
		pars$Lambda=array(1,c(ncol(X.disc),Nout,Nout));
		Lambdainit=riwish(priors$disc$Lambda$nu,priors$disc$Lambda$mu);	
		if (ncol(X.disc)==1) pars$disc=matrix(pars$disc,1,Nout);
		fits=X.disc%*%pars$disc;		
		for (ii in 1:ncol(X.disc)){
			pars$Lambda[ii,,]=Lambdainit;
			chain$Lambda[1,ii,,]=Lambdainit;
		}			
	}
	#initialize thincounter
	thincounter=0; chaincounter=1; 
	for (mcmcit in 2:ctrl1$niter+1){
		if (eval1$theta)
		{c(pars$theta,pars$dummy,StateVar,loglik):=comptheta(pars,zvec,StateVar,const,loglik,priors$theta,inits$samplevec,BigCovtheta);}
		if (eval1$pars)
		{c(pars$pars,StateVar,loglik):=comppars(pars,zvec,StateVar,const,loglik,priors$pars,inits$samplevec,BigCovpars);}
		if (eval1$disc)
		{c(pars$disc,pars$Lambda,StateVar,loglik):=compdisc(pars,StateVar,const,loglik,priors$disc);}	
		acc=StateVar$acc;
		#update sigma
		#c(pars$sigma,loglik):=updatesigmaold(loglik,priors$sigma);
		c(pars$sigma,loglik):=updatesigmacalib(loglik,priors$sigma)
        StateVar$togg=0; 
		#update the chain of samples when appropriate
       	thincounter=thincounter+1;
      	if (thincounter==ctrl1$thinby)
      	{
        	chaincounter=chaincounter+1; thincounter=0;
        	if (eval1$theta){
        		#backtransform pars$theta
        		#thetaraw=backtrans.input(Xmat=pars$theta,X.lim=ctrl1$mod$thlim);
        		#chain$theta[chaincounter,]=c(pars$theta,pars$sigma,loglik$lik,sum((zvec-loglik$yvec)^2));
        		chain$theta[chaincounter,]=c(pars$theta,loglik$lik,sum((zvec-loglik$yvec)^2));
        		chain$dummy[chaincounter,]=pars$dummy;
        		}
        	if (eval1$pars){chain$pars[chaincounter,]=pars$pars;}
        	if (eval1$disc){chain$disc[chaincounter,,]=pars$disc;}
        	#print(dim(chain$sigma));
        	chain$sigma[chaincounter,,]=pars$sigma;
        	
        	if (chaincounter%%100==0){
                print(chaincounter); #print(chain$theta[(1:100)+chaincounter-100,1:len1$theta]);
                #print(pars$theta);
            }
        	if (adapt$yes)
        		{c(BigCovtheta,StateVar$acc):=adaptsamp1(chaincounter,adapt,StateVar$acc,inits$samplevec,chain,len1$theta,BigCovtheta);}
        	if (chaincounter%%nprint==0){
        		chtemp=chaincounter/nprint;
        		if (eval1$theta){write.table(chain$theta[nprint*(chtemp-1)+(1:nprint),],fileVar$outfile$theta,col.names=F,row.names=F,append=T);}
        		if (eval1$pars){write.table(chain$pars[nprint*(chtemp-1)+(1:nprint),],fileVar$outfile$pars,col.names=F,row.names=F,append=T);}
        		if (eval1$disc){write.table(chain$disc[nprint*(chtemp-1)+(1:nprint),],fileVar$outfile$disc,col.names=F,row.names=F,append=T);}
			}	
      }	
	}
	#backtransform pars$theta
	#print((chain$theta[,4:6]))
    chain$theta[,1:len1$theta]=backtrans.input(Xmat=chain$theta[,1:len1$theta,drop=F],X.lim=ctrl1$mod$thlim);
    
	return(list(chain=chain,acc=acc,BigCovtheta=BigCovtheta));
}

updatesigmaold=function(loglik,priors){
	sigmapost1=priors$a1+nrow(loglik$yvec)/2;
    sigmapost2=priors$a2+sum(loglik$resids^2)/2;
    Sigmanew=1/rgamma(1,sigmapost1,sigmapost2);
    #update likelihood
    loglik$lik=-0.5*length(loglik$yvec)*(log(2*pi)+log(Sigmanew))-sum((loglik$resids)^2)/(2*Sigmanew);
	return(list(Sigmanew,loglik));
}

updatesigmacalib=function(loglik,priors){
	  N=nrow(loglik$resids); C=ncol(loglik$resids);
	  Sigma=array(1,c(C,C));
	  # compute Sigma
	  PSigma=t(loglik$resids)%*%loglik$resids+priors$mu; 
	  nu=N+priors$nu;
	  Sigmanew=as.matrix(riwish(nu,PSigma));
	  #logdens=log(diwish(Sigma,priors1$nu,priors1$mu));	
	  loglik$lik=-0.5*N*C*log(2*pi)-0.5*N*determinant(Sigmanew)$modulus[1];
    for (jj in 1:N)
      	loglik$lik=loglik$lik-0.5*t(loglik$resids[jj,])%*%solve(Sigmanew)%*%(loglik$resids[jj,]);
	  
	  return(list(Sigmanew,loglik));
}

#do the adaptive sampling
adaptsamp1=function(chaincounter,adapt,acc,samplevec,chain,len.theta,BigCovtheta)
{
    p1=max(samplevec$theta); 
    for (step1 in 1:p1){
		indicvec=which(samplevec$theta==step1);
    	if((chaincounter%%adapt$var$size==0) & (chaincounter<=adapt$var$size*adapt$var$num) & length(indicvec)>0) {
        				adtemp=chaincounter/adapt$var$size;
        				accdiff=(acc$theta[indicvec]-acc$varupd[indicvec])/adapt$var$size;  acc$varupd[indicvec]=acc$theta[indicvec];  
        				idx.adapt=adapt$var$size*(adtemp-1)+(1:adapt$var$size);
        				BigCovtheta[indicvec,indicvec]=adaptvar(chain,idx.adapt,indicvec,BigCovtheta[indicvec,indicvec],adapt$var$tune,accdiff[1]);
        			}
        if((chaincounter%%adapt$cov$size==0) & (chaincounter<=adapt$cov$size*adapt$cov$num) & length(indicvec)>0) {	
        				adtemp=chaincounter/adapt$cov$size;
        				accdiff=(acc$theta[indicvec]-acc$covupd[indicvec])/adapt$cov$size;  acc$covupd[indicvec]=acc$theta[indicvec]; 
        				idx.adapt=adapt$cov$size*(adtemp-1)+(1:adapt$cov$size);
        				BigCovtheta[indicvec,indicvec]=adaptcov(chain,idx.adapt,indicvec,BigCovtheta[indicvec,indicvec],accdiff[1]);
        				#print(accdiff);
        				#print(10000*BigCovtheta);
        			}	
	}
	
	return(list(BigCovtheta,acc))
}

#adaptive sampling
adaptcov=function(chain,idx.adapt,indicvec,Covold,accprop)
{
	th1=chain$theta[idx.adapt,indicvec];  du1=chain$dummy[idx.adapt,indicvec];
	Covnew=Covold;
	if (accprop>0){
		Covnew=cov(th1);
		Covnew=Covnew*(2.38^2/length(indicvec));  ## (2.38^2/#dimen)
		#print(c(indicvec,accprop));
		#print(Covnew); print(indicvec);
	}
	temp1=try(chol(Covnew));
	if(class(temp1)=="try-error") {Covnew=Covold; #print(Covnew); print(indicvec); 
		} 
	
	return(Covnew);	
}

adaptvar=function(chain,idx.adapt,indicvec,Covold,tune1,accprop)
{
	th1=chain$theta[idx.adapt,indicvec];  du1=chain$dummy[idx.adapt,indicvec];
	Covnew=Covold;
	for (ii in 1:length(indicvec)){
			if (accprop[ii]<0.2){
				#Covnew[ii,ii]=Covold[ii,ii]/tune1$down;
				Covnew[ii,]=Covnew[ii,]/sqrt(tune1$down);
				Covnew[,ii]=Covnew[,ii]/sqrt(tune1$down);	
			}	
			if (accprop[ii]>0.9){
				Covnew[ii,]=Covnew[ii,]*tune1$up;
				Covnew[,ii]=Covnew[,ii]*tune1$up;	
			}		
		}
	return(Covnew);	
}

#MH sampling for thetas
# [theta,StateVar,loglik]
comptheta=function(pars,zvec,StateVar,const,loglik,priors1,samplevec,Bigcovmat)
{
    theta=pars$theta;  dummy=pars$dummy;  p1=max(samplevec$theta); 
    proppars=pars;
    propdens1=list();
    for (step1 in 1:p1)
    {
        proptheta=theta;  propdummy=dummy; loglikprop=loglik; logprob=-Inf;
        indicvec=which(samplevec$theta==step1);  #finds the parameters that need to be varied in this step
       #obtain proposed value
        currtheta=proptheta[indicvec]; currdummy=propdummy[indicvec];
        propcovmat=as.matrix(Bigcovmat[indicvec,indicvec]);
        flagprop=(const$kk[1]%in%indicvec);
        #if (!flagprop)
        	if(1==1)
        	{c(proptheta[indicvec],propdummy[indicvec],propdens1):=propos(currtheta,currdummy,propcovmat,samplevec,priors1,flagprop,indicvec);}
        #if (step1==1) {print(proptheta[indicvec]);}
        #if (flagprop) { propdens1$num=0; propdens1$den=0;}
        #compute likelihood
        if (all(proptheta>priors1$pribds$a1 & proptheta<priors1$pribds$a2))
        {
       		proppars$theta=proptheta; proppars$dummy=propdummy; 
        	loglikprop=getlikl(proppars,zvec,const$ctrl1,const$fileVar,loglik);     
        	if (prod(loglikprop$flag)==0) {proptheta=theta;  propdummy=dummy; loglikprop=loglik;}
			logMHnum=loglikprop$lik;
			#if parameter has not been updated, use previous value for propden
        	if (StateVar$togg) 
        		{logMHden=StateVar$savedMHden;}
         	if (!StateVar$togg) 
            	{logMHden=loglik$lik; StateVar$savedMHden=logMHden; StateVar$togg=1;}  	 	
        	#add in proposal component    	
            logMHnum=logMHnum+propdens1$num;  logMHden=logMHden+propdens1$den; 
        	#add in priors
       		pridens1=prieval(currtheta,proptheta[indicvec],currdummy,propdummy[indicvec],priors1,indicvec,const$ctrl1);
        	logMHnum=logMHnum+pridens1$num;  logMHden=logMHden+pridens1$den;
        	logprob=logMHnum-logMHden;
        	#print(c(step1,pridens1$num,pridens1$den));
        #debugging tool
        	if (flagprop) {
        	#	if (1==1) {	
                #print(c(theta[const$kk[1]],proptheta[const$kk[1]]));
                print(c(theta,proptheta))
                print(c(logMHnum,logMHden,logprob));
                print(c(propdens1$num,propdens1$den));
                print(c(sum((loglik$resids-loglikprop$resids)^2),sum((loglik$yvec-loglikprop$yvec)^2)));
            }   
		}
        # accept/reject step
        if (logprob>=log(runif(1))) {
        	theta=proptheta;  dummy=propdummy;
            StateVar$acc$theta[indicvec]=StateVar$acc$theta[indicvec]+1;
           	StateVar$togg=0;
			loglik=loglikprop;   
        }	
    }
    return(list(theta,dummy,StateVar,loglik));
}

#likelihood
getlikl=function(pars,zvec,ctrl1,fileVar,loglikold) {
    loglik=list();
    flagout=1;
    c(loglik$yvec,loglik$flag):=modelfunc(pars,ctrl1,fileVar);
    loglik$resids=loglikold$resids-loglik$yvec+loglikold$yvec;
    #loglik$lik=-0.5*length(loglik$yvec)*(log(2*pi)+log(pars$sigma))-sum(loglik$resids^2)/(2*pars$sigma); #univariate likelihood
    #[pars$theta,sum(loglik$likvec.^2),loglik$lik];
    #multivariate likelihood
    N=nrow(loglik$resids); C=ncol(loglik$resids);
    	loglik$lik=-0.5*N*C*log(2*pi)-0.5*N*determinant(pars$sigma)$modulus[1];
    for (jj in 1:N)
      	loglik$lik=loglik$lik-0.5*t(loglik$resids[jj,])%*%solve(pars$sigma)%*%(loglik$resids[jj,]);
    
    return(loglik);
}	

### operator function to write to multiple outputs
':=' <- function(lhs, rhs) {
  frame <- parent.frame()
  lhs <- as.list(substitute(lhs))
  if (length(lhs) > 1)
    lhs <- lhs[-1]
  if (length(lhs) == 1) {
    do.call(`=`, list(lhs[[1]], rhs), envir=frame)
    return(invisible(NULL)) 
  }
  if (is.function(rhs) || is(rhs, 'formula'))
    rhs <- list(rhs)
  if (length(lhs) > length(rhs))
    rhs <- c(rhs, rep(list(NULL), length(lhs) - length(rhs)))
  for (i in 1:length(lhs))
    do.call(`=`, list(lhs[[i]], rhs[[i]]), envir=frame)
  return(invisible(NULL)) 
}

### spike and slab proposal
propos=function(currtheta,currdummy,Cov,samplevec,priors1,flagkk,indvec1){
  togg=0; #togg indicates the transition 
  propth=currtheta; propdu=currdummy;  
  proplik=list(); proplik$num=0; proplik$den=0;
  
  # first update dummy variables
  alphavec=samplevec$prop$prob[indvec1]/dnorm(0)*dnorm((propth-samplevec$prop$def[indvec1])/samplevec$prop$range[indvec1]);
  if (!flagkk) {propdu=(alphavec<runif(length(indvec1)));} # propdummy is not-default, while alphavec denotes prob of getting to default 
  
  indvec2a=which(currdummy==1);  # find which parameters are not at default
  indvec2b=which(propdu==1);     # find which parameters are not at default for new proposal
  
  # obtain proposal value of theta
  def1=samplevec$prop$def[indvec1];   # default values 
  pribds1=priors1$pribds$a1[indvec1]; pribds2=priors1$pribds$a2[indvec1];
  
  if (length(indvec2b)>0){
    if (!flagkk){
      propth[-indvec2b]=def1[-indvec2b];
      propth[indvec2b]=propos1(currtheta[indvec2b],as.matrix(Cov[indvec2b,indvec2b]),pribds1[indvec2b],pribds2[indvec2b],flagkk);
    }
    proplik$den=proplik$den+sum(log(alphavec[-indvec2b]))+sum(log(1-alphavec[indvec2b]));#+mvndens(propth[indvec2b],currtheta[indvec2b],Cov[indvec2b,indvec2b]);	
  }
  if (length(indvec2b)==0){
    if (!flagkk) {propth=def1;}
    proplik$den=proplik$den+sum(log(alphavec));
  }
  if (length(indvec2a)>0)
  {proplik$num=sum(log(alphavec[-indvec2a]))+sum(log(1-alphavec[indvec2a]));#+mvndens(currtheta[indvec2a],propth[indvec2a],Cov[indvec2a,indvec2a]);
  }
  if (length(indvec2a)==0)
  {proplik$num=proplik$num+sum(log(alphavec));}	
  #print(c(length(indvec2a),sum(log(alphavec[-indvec2a])),sum(log(1-alphavec[indvec2a])),mvndens(propth[indvec2a],currtheta[indvec2a],Cov[indvec2a,indvec2a])));			
  return(list(propth,propdu,proplik));
}

propos1=function(currval,Cov,pribds1,pribds2,flagkk)
{				
    prop=currval; 
    if (!flagkk) {
        ind1=1:nrow(Cov);
        ind1=ind1[(diag(Cov)>0)];
        prop[ind1]=mvrnorm(1,currval[ind1],Cov[ind1,ind1]);
       if (sum((prop<pribds1)||(prop>pribds2))) prop=currval;  
    }
	return(prop);
}

### spike slab prior
#if transf is false, then you need to back transfer parameters to original scale
prieval=function(oldth1,newth1,olddum,newdum,priors1,indvec1,ctrl1,transf=FALSE)	{
 
  oldth=oldth1; newth=newth1;
  if (!transf){
  	oldth=backtrans.input(Xmat=oldth,X.lim=ctrl1$mod$thlim);
  	newth=backtrans.input(Xmat=newth,X.lim=ctrl1$mod$thlim);
  }
   
  # extract priors for relevant parameters
  priors2=list();
  priors2$prob=priors1$prob[indvec1]; priors2$def=priors1$def[indvec1];
  priors2$a1=priors1$a1[indvec1]; priors2$a2=priors1$a2[indvec1];
  priors2$type=priors1$type[indvec1];
  
  indvec2a=which(olddum==1);  # find which parameters are not at default
  indvec2b=which(newdum==1);  # find which parameters are not at default for new proposal
  priout=list();
  # put in point mass priors for parameters at default
  if (length(indvec2a)>0){priout$den=sum(log(priors2$prob[-indvec2a]))+sum(log(1-priors2$prob[indvec2a]));}
  if (length(indvec2a)==0){priout$den=sum(log(priors2$prob));}	
  if (length(indvec2b)>0){priout$num=sum(log(priors2$prob[-indvec2b]))+sum(log(1-priors2$prob[indvec2b]));}
  if (length(indvec2b)==0){priout$num=sum(log(priors2$prob));}		
  
  for (ii in indvec2a){
    priout$den=priout$den+prieval1(priors2$type[ii],oldth[ii],c(priors2$a1[ii],priors2$a2[ii]));		
  }
  for (ii in indvec2b){
    priout$num=priout$num+prieval1(priors2$type[ii],newth[ii],c(priors2$a1[ii],priors2$a2[ii]));		
  }
  return(priout);
}

### priors
## type=1 implies a log normal prior, type=2 implies a IG prior
prieval1=function(type,val1,pripars){			
  prival=0;
  if (type==0){prival=-Inf}
  if (type==1){prival=-0.5*log(pripars[2])-0.5*(val1-pripars[1])^2/pripars[2];} # normal
  if (type==2){prival=-(pripars[1]+1)*log(val1)-pripars[2]/val1;}               # inverse gamma
  if (type==3){prival=log(val1)-(log(val1)-pripars[1])^2/(2*pripars[2]^2);}     # lognormal
  if ((type==4) && (val1<pripars[1] || val1>pripars[2])){prival=-Inf;}          # uniform
  if (type==5){prival=(pripars[1]-1)*log(val1)-pripars[2]*val1;} 				# gamma	
  return(prival);
} 		

### log multivariate normal density
mvndens=function(x1,mean,Cov){
  Cov=as.matrix(Cov);
  k=length(x1);
  dens=-k/2*log(2*pi)-1/2*determinant(Cov)$modulus-1/2*t(x1-mean)%*%solve(Cov)%*%(x1-mean);
  return(dens);
}

### obtain probability for jump using multivariate normal
alphaprob=function(val1,def,range,prob1){
  prob2=prob1/dnorm(0)*dnorm(x=val1,mean=def,sd=range);
  return(prob2);
}

#get output from the emulator...
modelfunc=function(pars,ctrl1,fileVar,type=1)
{
	theta=pars$theta;
	if (ctrl1$mod$incl.em){
		modout=modelfunc2(theta=pars$theta,beta=ctrl1$mod$betamat,frontend=ctrl1$mod$frontend,ord1.inp=ctrl1$mod$ord1inp);
		yout=modout$yout;
	}
	if (!ctrl1$mod$incl.em)
	{
		Ninp=ctrl1$mod$Ninp; Npar=ctrl1$mod$Npar;
		FUN1=match.fun(ctrl1$mod$name);
		thetaraw=backtrans.input(Xmat=theta,X.lim=ctrl1$mod$thlim);
		ctrl1$mod$inputs$Xmat[,(1:Npar)+Ninp]=matrix(1,nrow(ctrl1$mod$inputs$Xmat),1)%x%thetaraw;
		modout=FUN1(ctrl1$mod$inputs);
		yout=modout$yout;
		if(nrow(ctrl1$mod$Y.lim)>1) yout=t(yout);
		yout=trans.output(Ymat=yout,Y.lim=ctrl1$mod$Y.lim)$trans;
	}		
	flag=modout$flag;
	return(list(as.matrix(yout),flag));
}

modelfunc2=function(theta,beta,frontend,ord1.inp,transf=FALSE,N.grid=500){
	
	N.eig=frontend$N.eig;
	#if (transf) {X.lim=frontend$X.trans$lim; Y.lim=frontend$Y.trans$lim;} 
	intermat=frontend$intermat;  Phi=frontend$Phi; 
	t.grid=seq(0,1,length=N.grid);
	N.inp=dim(ord1.inp)[3]; N.par=length(theta); P=N.inp+N.par;
	M=dim(ord1.inp)[1]; C=dim(beta)[3];
	if (transf){
	theta=trans.pred(theta,X.lim[1:N.par,]);
	}
	firstordmat=array(NA,c(M,N.eig[1],N.par));  #array of first order basis functions
	
	#compute all first order functions
	for (ii in 1:N.par){
		temp1=get.main.X(theta[ii],N.eig[1],Phi,t.grid)
		firstordmat[,,ii]=t(as.matrix(replicate(M,temp1[1,])));			
	}
	
	if (N.inp>0) firstordmat=abind(ord1.inp,firstordmat,along=3);
	#compute full BSS-Anova design matrix by computing interactions
	X.pred=get.all.basis(firstordmat,intermat,M);
	preds=array(0,c(M,dim(beta)[1],C));
	meanpred=matrix(0,M,C);
	for (jj in 1:C){
		nbeta=t(as.matrix(beta[,,jj]));
		preds[,,jj]=X.pred%*%nbeta;
		#if (transf) {preds[,jj]=apply(preds[,jj],2,backtrans.output,Y.lim[jj,,drop=F]);}	
		meanpred[,jj]=apply(preds[,,jj,drop=F],1,mean);
	}
	return(list(preds=preds,yout=meanpred,flag=1))		
}

compdisc=function(pars,StateVar,const,loglik,priors1,BigCovdisc=0){
  
  frontend=const$ctrl1$disc$frontend; y.trans=frontend$Y.trans$trans;
  inclmat=frontend$inclmat; intermat=frontend$intermat; X.disc=frontend$X.em; Xsm.disc=frontend$Xsm;
  betatemp=updatebeta(pars$disc,loglik$resids,pars$Lambda,as.matrix(pars$sigma),inclmat,Xsm.disc,y.trans,X.disc,intermat);
  residstemp=betatemp$resids; 
  Lambdatemp=updatelambda(pars$disc,priors1$Lambda,inclmat,Xsm.disc,intermat);
  
  # log-likelihood
  logliktemp=betatemp$logdens+Lambdatemp$logdens;
  loglik$resids=betatemp$resids;	
  
  return(list(betatemp$beta,Lambdatemp$Lambda,StateVar,loglik));
}

### set up initial values and priors from file
getdefaults=function(Npar,Nout=1,incl.ptmass=F,adaptcov=T){
  # initial points
  inits=list();
  inits$theta=rep(0.51,Npar);
  inits$dummy=rep(1,Npar);
  inits$pars=c();
  inits$disc=c();
  inits$sigma=rep(0.05,Nout);
  inits$BigCov$theta=diag(rep(0.05,Npar)^2,nrow=Npar);
  inits$samplevec$theta=rep(1,Npar);
  inits$samplevec$pars=c();
  inits$samplevec$disc=c();
  inits$samplevec$prop$prob=rep(0,Npar);
  inits$samplevec$prop$def=rep(0,Npar);
  inits$samplevec$prop$range=rep(0.1,Npar);
  
  # priors
  priors=list();
  priors$theta$a1=rep(0,Npar);
  priors$theta$a2=rep(1,Npar);
  priors$theta$type=rep(4,Npar);
  priors$theta$pribds$a1=rep(0,Npar); priors$theta$pribds$a2=rep(1,Npar);
  priors$theta$pm=rep(0,Npar);
  priors$theta$prob=rep(0,Npar);
  priors$theta$def=rep(0.5,Npar);

  priors$sigma$a1=rep(2,Nout); priors$sigma$a2=rep(0.03,Nout);
  priors$sigma$type=rep(2,Nout);
  priors$sigma$pribds$a1=rep(0,Nout); priors$sigma$pribds$a2=rep(Inf,Nout);
  
  priors$sigma$nu=4;  priors$sigma$mu=2*diag(priors$sigma$a2,nrow=Nout)
  if (incl.ptmass){
    inits$dummy=rep(0,Npar);
    priors$theta$pm=rep(1,Npar);
  }
  
  # control variables and evaluation variables
  ctrl1=list();  
  # adaptive proposal information
  ctrl1$adapt$yes=1;  ctrl1$adapt$cov$size=200;  ctrl1$adapt$cov$num=25;  # block size and block number
  ctrl1$adapt$var$size=100; ctrl1$adapt$var$num=0; ctrl1$adapt$var$tune$up=5; ctrl1$adapt$var$tune$down=5;
  
  if(!adaptcov) {ctrl1$adapt$yes=0;}
  
  return(list(inits=inits,priors=priors,ctrl1=ctrl1));
}

setupinits=function(initsmatrnew,inits,incl.ptmass=F,Xlim,Ylim)
{
	#initsmatrnew=as.matrix(read.table(initsfile));
	Nout=nrow(Ylim); Npar=nrow(Xlim);
	initsmpar=initsmatrnew[,1:Npar,drop=F];
	initsmpar[c(1,5),]=trans.pred(initsmpar[c(1,5),,drop=F],Xlim);
	initsmpar[c(6),]=initsmpar[c(6),,drop=F]/Xlim[,2];
	#if (incl.ptmass){initsmpar[c(5,6),]=trans.pred(initsmpar[c(5,6),,drop=F],Xlim);}
	initsmatr=matrix(c(inits$theta,inits$dummy,inits$samplevec$theta,inits$samplevec$prop$prob,inits$samplevec$prop$def,inits$samplevec$prop$range),6,Npar,byrow=T);
	initsmatr[!is.na(initsmpar)]=initsmpar[!is.na(initsmpar)];
	#initial points
	inits$theta=initsmatr[1,];
	inits$samplevec$theta=initsmatr[2,];
	
	if (incl.ptmass) {
		inits$dummy=initsmatr[3,];
		inits$samplevec$prop$prob=initsmatr[4,];
		inits$samplevec$prop$def=initsmatr[5,];
		inits$samplevec$prop$range=initsmatr[6,];  #range parameters for changing proposal
	}
	
	initsmsigma=initsmatrnew[1,(1:Nout)+Npar,drop=F];
	initsmsigma=initsmsigma/Ylim[,2];
	inits$sigma[!is.na(initsmsigma)]=initsmsigma[!is.na(initsmsigma)];
	
	return(inits);
}

setuppriors=function(priorsmatrnew,priors,incl.ptmass=F,Xlim,Ylim)
{
	#priorsmatrnew=as.matrix(read.table(priorsfile));
	Npar=nrow(Xlim); Nout=nrow(Ylim);
	priorsmpar=priorsmatrnew[,1:Npar,drop=F];
	#priorsmpar[c(2,3,4,5,8),]=trans.pred(priorsmpar[c(2,3,4,5,8),,drop=F],Xlim);
	#if (incl.ptmass){priorsmpar[c(8),]=trans.pred(priorsmpar[c(8),,drop=F],Xlim);}
	priorsmatr=matrix(c(priors$theta$type,priors$theta$a1,priors$theta$a2,priors$theta$pribds$a1,priors$theta$pribds$a2,priors$theta$pm,priors$theta$prob,priors$theta$def),nrow(priorsmpar),Npar,byrow=T);
	priorsmatr[!is.na(priorsmpar)]=priorsmpar[!is.na(priorsmpar)];
	priors$theta$type=priorsmatr[1,];
	priors$theta$a1=priorsmatr[2,];
	priors$theta$a2=priorsmatr[3,];
	priors$theta$pribds$a1=sapply(priorsmatr[4,],max,0);  
	priors$theta$pribds$a2=sapply(priorsmatr[5,],min,1);

	if (incl.ptmass){
		priors$theta$pm=priorsmatr[6,];
		priors$theta$prob=priorsmatr[7,];  #probabilities of point mass
		priors$theta$def=priorsmatr[8,];  #point mass values
	}
	#update priors for sigma
    if (ncol(priorsmatrnew)>Npar){
        priorsmsigma=priorsmatrnew[1:5,(1:Nout)+Npar,drop=F];
        priorsmsigma[3,]=priorsmsigma[3,]/Ylim[,2];
        prisigmatr=matrix(c(priors$sigma$type,priors$sigma$a1,priors$sigma$a2,priors$sigma$pribds$a1,priors$sigma$pribds$a2),nrow(priorsmsigma),Nout,byrow=T);

        prisigmatr[!is.na(priorsmsigma)]=priorsmsigma[!is.na(priorsmsigma)];
	
        priors$sigma$a1=prisigmatr[2,]; priors$sigma$a2=prisigmatr[3,];
        priors$sigma$type=prisigmatr[1,];
        priors$sigma$pribds$a1=prisigmatr[4,]; priors$sigma$pribds$a2=prisigmatr[5,];
  	
        priors$sigma$nu=2*mean(priors$sigma$a1);  priors$sigma$mu=2*diag(priors$sigma$a2,nrow=Nout);
	}
	#if (!is.na(priorsmatrnew[1,Npar+1])) priors$sigma$a1=priorsmatr[1,Npar+1];	
	#if (!is.na(priorsmatrnew[2,Npar+1])) priors$sigma$a2=priorsmatr[1,Npar+1];
	
	return(priors);	
}

get1ordinp=function(Xsinput,frontend,transf=FALSE,N.grid=500){
  
  N.eig=frontend$N.eig;
  if (transf) {X.lim=frontend$X.trans$lim; Y.lim=frontend$Y.trans$lim;} 
  Phi=frontend$Phi;  t.grid=seq(0,1,length=N.grid);
  
  N.inp=ncol(Xsinput); M=nrow(Xsinput); C=dim(beta)[3];
  if (transf){theta=trans.pred(theta,X.lim[1:N.par,,drop=F]);5}
  firstordmat=array(NA,c(M,N.eig[1],N.inp));  # array of first order basis functions
  
  # compute all first order functions
  for (ii in 1:N.inp){
    firstordmat[,,ii]=get.main.X(Xsinput[,ii],N.eig[1],Phi,t.grid);			
  }
  return(firstordmat);	
}

### transform inputs to [0,1]
trans.input=function(Xmat,X.lim=NULL){
  transmat=Xmat;
  inplim=matrix(NA,ncol(Xmat),2);
  
  for(j in 1:ncol(Xmat)){
    R.j=(max(Xmat[,j])-min(Xmat[,j]))/0.8; min.j=(max(Xmat[,j])+min(Xmat[,j])-R.j)/2;
    if (!is.null(X.lim)) {
      R.j=(X.lim[j,2]-X.lim[j,1])/0.8; min.j=(X.lim[j,2]+X.lim[j,1]-R.j)/2;
    }
    transmat[,j]=(transmat[,j]-min.j)/R.j;
    if (R.j==0) {transmat[,j]=0.5;}
    inplim[j,]=c(min.j,R.j);	
  }
  return(list(trans=as.matrix(transmat),lim=inplim));
}

### transform outputs to zero mean and variance 1
trans.output=function(Ymat,Y.lim=NULL){
  transmat=Ymat;
  outlim=matrix(NA,ncol(Ymat),2);
  for (j in 1:ncol(Ymat)){
    Y.mean=mean(transmat[,j]); Y.sd=sd(transmat[,j]);
    if (!is.null(Y.lim)){
      Y.mean=Y.lim[j,1]; Y.sd=Y.lim[j,2];	
    }
    transmat[,j]=(transmat[,j]-Y.mean)/Y.sd;
    outlim[j,]=c(Y.mean,Y.sd);	
  }
  return(list(trans=as.matrix(transmat),lim=outlim));
}

# transform inputs to [0,1]
trans.pred=function(Xmat,X.lim){
	transmat=Xmat;
	if (is.null(ncol(transmat)))
    transmat=matrix(transmat,nrow=length(transmat)/nrow(X.lim),ncol=nrow(X.lim));
	
	for(j in 1:nrow(X.lim)){
 		R.j=X.lim[j,2];	min.j=X.lim[j,1];
		transmat[,j]=(transmat[,j]-min.j)/R.j;
        if (R.j==0) {transmat[,j]=0.5;}
    }
    return(as.matrix(transmat));
}

### transform inputs back to original scale
backtrans.input=function(Xmat,X.lim){
  transmat=Xmat;
  if (is.null(ncol(transmat)))
    transmat=matrix(transmat,nrow=length(transmat)/nrow(X.lim),ncol=nrow(X.lim));
  
  for(j in 1:nrow(X.lim)){
    R.j=X.lim[j,2];	 min.j=X.lim[j,1];
    transmat[,j]=(transmat[,j]*R.j+min.j);
  }
  return(as.matrix(transmat));
}

#actual model for Morris function

#form of inputs are [t,par1,..,park]
morrisfunc=function(inps)
{
	
	s=(sum(inps[-1])-1.5)/1.5;
	fx=(1+sign(s)*(abs(s))^0.3)/2
	
	#output=fx*(-log(1-inps[1]));
	output=fx*inps[1]^2*5;
	return(output)
}

morrisfuncmult=function(inps)
{
	
	s=(sum(inps[-1])-1.5)/1.5;
	fx=(1+sign(s)*(abs(s))^0.3)/2
	
	#output=fx*(-log(1-inps[1]));
	out1=fx*inps[1]^2*5;
	out2=inps[1]^1.2*out1^0.7+3*inps[3];
	out3=fx^2-prod(inps)^1.1;
	output=c(out1,out2,out3)
	
	return(output)
}

morrisfuncbig=function(inps1)
{
	#print(inps1$Xmat)
	yout=apply(inps1$Xmat,1,morrisfunc);
	return(list(yout=as.matrix(yout),flag=1));	
}

morrisfuncmultbig=function(inps1)
{
	#print(inps1$Xmat)
	yout=apply(inps1$Xmat,1,morrisfuncmult);
	return(list(yout=as.matrix(yout),flag=1));	
}

# ======================================================================
# ======================================================================
args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned

interactive=1;

if (interactive){

nx.design <- args[1]     # number of design inputs
nx.var <- args[2]        # number of variable inputs
nx.out <- args[3]
nx.design = as.numeric(nx.design)
nx.var = as.numeric(nx.var)
nx.out = as.numeric(nx.out)

xfile <- args[4]        # training input
yfile <- args[5]        # training output (ground truth)
rdsfile <- args[6]      # trained model will save to R binary
expfile <- args[7]      # experimental data
priorsfile <- args[8]   # prior distribution on inputs
initsfile <- args[9]   # initial values on inputs
if (initsfile=="NULL") initsfile=NULL;
disc <- args[10]         # boolean indicating whether discrepancy should be included
writepost <- args[11]    # boolean indicating whether to save posterior samples
writedisc <- args[12]   # boolean indicating whether to save discrepancy samples
disc = as.numeric(disc)
writepost = as.numeric(writepost)
writedisc = as.numeric(writedisc)
if (!disc) {writedisc=FALSE;}   # nothing to write in this case

# parse emulator parameters
bte = args[13]          # vector containing...
                        #   B: burn-in (toss out this many iterations from beginning)
                        #   T: total number of MCMC iterations
                        #   E: how often to record (keep every e-th sample)
nterms <- args[14]      # number of basis functions to use in K-L expansion
                        #   for each BSSANOVA component
order <- args[15]       # order of interaction terms for BSS-ANOVA
s = strsplit(bte,'[^[:digit:]]')   # split string at non-digits
s = as.numeric(unlist(s))          # convert strings to numeric ('' becomes NA)
s = unique(s[!is.na(s)])           # remove NA and duplicates
bte.em = s
nterms.em = as.numeric(nterms)
order.em = as.numeric(order)

# parse calibration parameters
bte = args[16]          # vector containing...
                        #   B: burn-in (toss out this many iterations from beginning)
                        #   T: total number of MCMC iterations
                        #   E: how often to record (keep every e-th sample)
s = strsplit(bte,'[^[:digit:]]')   # split string at non-digits
s = as.numeric(unlist(s))          # convert strings to numeric ('' becomes NA)
s = unique(s[!is.na(s)])           # remove NA and duplicates
bte.cal = s

# parse discrepancy parameters
nterms <- args[17]       # number of basis functions to use in K-L expansion
                         #   for each BSSANOVA component
order <- args[18]        # order of interaction terms for BSS-ANOVA
nterms.disc = as.numeric(nterms)
order.disc = as.numeric(order);

#control variables for using emulator, pt mass priors, or restart
incl.ptmass <- args[19]     # boolean indicating whether point mass priors should be included
incl.em <- args[20]         # boolean indicating whether emulator should be included
model.func <-args[21]

incl.ptmass = as.numeric(incl.ptmass)
incl.em = as.numeric(incl.em)

if (incl.em) model.func=NULL;
#if(!incl.em) {model.func="morrisfuncbig"} # specify model if emulator is not used

#restart capability
oldcalibname <- args[22]  		#name of previous rds file used for restart purposes.  NULL means no restart

#read RDS file
if (oldcalibname=="NULL") oldcalib=NULL;
if (oldcalibname!="NULL") {
	oldcalib=readRDS(oldcalibname)
	#print(attributes(oldcalib));
} 

# read files
X = read.table(xfile, sep=',', header=TRUE)
nx = ncol(X)
X = as.matrix(X[,1:nx,drop=F])
Y = read.table(yfile, sep=',', header=TRUE)
ny = ncol(Y)
Y = as.matrix(Y[,1:ny,drop=F])
E = read.table(expfile, sep=',', header=TRUE)
ne = ncol(E)
E = as.matrix(E[,1:ne,drop=F])

model <- SolventFit_calib(nx.design, nx.var, ny, X, Y, E, priorsfile=priorsfile,initsfile=initsfile,
                          burnin.em=bte.em[1], nmcmc.em=bte.em[2], thinby.em=bte.em[3],
                          nterms.em=nterms.em, order.em=order.em,
                          burnin.cal=bte.cal[1], nmcmc.cal=bte.cal[2], thinby.cal=bte.cal[3],
                          incl.disc=disc, nterms.disc=nterms.disc, order.disc=order.disc,
                          incl.ptmass=incl.ptmass,incl.em=incl.em,model.func=model.func,oldcalib=oldcalib)
saveRDS(model, rdsfile)

if (writepost){
   samples <- model$calibout$chain$theta[,c(1:nx.var),drop=F]  # omit irrelevant columns
   samples <- samples[-nrow(samples),,drop=F]           # omit last row
   outfile = 'post.samples'
   write.table(samples, file=outfile, sep=' ', row.names=FALSE, col.names=FALSE, quote=FALSE)
}

if (writedisc){
   samples <- model$calibout$chain$disc
   outfile = 'disc.samples'
   write.table(samples, file=outfile, sep=' ', row.names=FALSE, col.names=FALSE, quote=FALSE)
}

}
