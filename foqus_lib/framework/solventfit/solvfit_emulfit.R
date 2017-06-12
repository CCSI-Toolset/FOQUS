suppressPackageStartupMessages(library(MCMCpack))   # required for riwish()

###############################################################
# SOLVENTFIT EMULATOR FITTING
###############################################################
interactive=0;  # set 1 to use as emulator, 0 to port functions

SolventFit_emul=function(Xs,Ys,burnin=0,nmcmc=10000,nterms=25,thinby=1,order=2,priorprob=0.5,N.grid=500,X.lim=NULL,Y.lim=NULL){
  frontend=MCMCfrontend(Xs=Xs,Ys=Ys,N.grid=N.grid,N.eig=rep(nterms,order),max.ord=c(25,8,6,4),X.lim=X.lim,Y.lim=Y.lim);	
  
  ############################################
  ### Specify prior settings for emulation ###
  ############################################
  
  Nout=ncol(Ys); 	
  
  priors=list();
  ## prior for coefficient covariance matrix Lambda
  priors$Lambda$mu=0.25*diag(rep(1,Nout),nrow=Nout); #0.25*c(1);
  priors$Lambda$nu=4;
  ## prior mean for the simulator output error variance Sigma
  priors$Sigma$mu=0.1*diag(rep(1,Nout),nrow=Nout);
  priors$Sigma$nu=10;
  
  ## number of MCMC iterations 
  ## it is set to 500 for illustration, should typically use 10000 or more 
  ctrl1=list();
  ctrl1$N.mcmc=nmcmc;
  # thinning thinby=1 means no thinning, nprint how often to write beta to file, nprint=0 means no write
  ctrl1$thinby=thinby;
  ctrl1$nprint=1e15;	
  
  ans.emul=BSSANOVA.MCMC(frontend=frontend,priors=priors,ctrl1=ctrl1,outfile=outfile,inits1=NULL,X.lim=NULL,inclmat=inclmat1);	
  return(list(postdist=ans.emul,frontend=frontend));
} 

########################
# Support functions
########################

## main BSS-ANOVA emulator MCMC
## INPUTS
##  ys - matrix of model outputs (rows are outputs evaluated at the rows of Xs)
##  Xs - matrix of model input values (e.g., angle and fluid velocity)
##  Ts - matrix of model parameters values
##  X.lim - 2 column matrix each row has limits for the inputs
##  T.lim - 2 column matrix each row has limits for the theta params
##  tpow - a vector of length ncol(y) of transformation powers to use on y
##  pi.theta - function evaluating prior density for theta
##  P.Lambda, v.Lambda - Lambda (emulator magnitude) invgamma prior params
##  P.Gamma, v.Gamma - Gamma (discrepancy magnitude) invgamma prior params
##  P.Ups, v.Ups - Ups (simulator "jitter" error variance) inv-Wishart prior params, P is a positive definite matrix, n is an integer.
##  P.Sigma, v.Sigma - Sigma (observational error variance) inv-Wishart prior params
##  N.mcmc - Total number of MCMC iterations
## OUTPUTS
##  X.em <- matrix of basis functions for emulator
##  beta - posterior sample array of emulator coefs dim [N.mcmc, ncol(X), ncol(y)]
##  Lambda - posterior sample array of dim [N.mcmc, ncomp.em, ncol(y)]
##  Sigma - posterior sample array of dim [N.mcmc, ncol(y), ncol(y)]

BSSANOVA.MCMC=function(frontend,priors,ctrl1,outfile,inits1=NULL,X.lim=NULL,Y.lim=NULL,inclmat=NULL){
  
  ## P is number of inputs and model parameters variables, C is number of outputs, M is the number of model runs
  X.trans=frontend$X.trans; Y.trans=frontend$Y.trans;
  M=nrow(X.trans$trans); P=ncol(X.trans$trans); C=ncol(Y.trans$trans); 
  # initialize control variables
  N.mcmc=ctrl1$N.mcmc; thinby=ctrl1$thinby; nprint=ctrl1$nprint;
  
  inclmat=frontend$inclmat; intermat=frontend$intermat; X.em=frontend$X.em; Xsm=frontend$Xsm;
  
  # initialize posterior sample chains
  beta.mat=array(0,c(N.mcmc/thinby+1, ncol(X.em),C));
  Sigma.mat=array(1,c(N.mcmc/thinby+1,C,C));
  Lambda.mat=array(1,c(N.mcmc/thinby+1,ncol(X.em),C,C));
  loglik.mat=matrix(NA,N.mcmc/thinby+1,2);
  
  # initial values for beta, Lambda, Sigma from priors
  betatemp=list();  Sigmatemp=list(); 
  Lambdatemp=list(); Lambdatemp$Lambda=array(1,c(ncol(X.em),C,C));
  
  if (is.null(inits1)){
    betainit=as.matrix(beta.mat[1,,]);
    Sigmainit=riwish(priors$Sigma$nu,priors$Sigma$mu);
    loglikinit=-1000000000;
    Lambdainit=riwish(priors$Lambda$nu,priors$Lambda$mu);
    for (ii in 1:ncol(X.em)){
      Lambdatemp$Lambda[ii,,]=Lambdainit;
      Lambda.mat[1,ii,,]=Lambdainit;
    }	
  } 
  if (!is.null(inits1)){
    betainit=as.matrix(inits1$beta);
    Sigmainit=inits1$Sigma;
    loglikinit=inits1$loglik;
    Lambdainit=inits1$Lambda;
    
    Lambdatemp$Lambda=Lambdainit;
    Lambda.mat[1,,,]=Lambdainit;	
  } 
  
  betatemp$beta=betainit; beta.mat[1,,]=betainit;
  fits=X.em%*%betatemp$beta;
  residstemp=Y.trans$trans-fits;
  Xsmresids=t(X.em)%*%residstemp;
  Sigmatemp$Sigma=Sigmainit; Sigma.mat[1,,]=Sigmatemp$Sigma;
  loglik.mat[1,]=c(sum(residstemp^2),loglikinit);	
  
  # loop for MCMC
  # initialize thincounter and other control variables
  thincounter=0; chaincounter=1; 
  print("Beginning Emulator MCMC");
  
  for (mcmcit in 2:(N.mcmc+1)){
    betatemp=updatebeta(betatemp$beta,residstemp,Lambdatemp$Lambda,Sigmatemp$Sigma,inclmat,Xsm,Xsmresids,Y.trans$trans,X.em,intermat);
    # compute fits, resids
    residstemp=betatemp$resids; Xsmresids=betatemp$Xsmresids;
    Lambdatemp=updatelambda(betatemp$beta,priors$Lambda,inclmat,Xsm,intermat);
    Sigmatemp=updatesigma(residstemp,priors$Sigma);
    # log-likelihood
    logliktemp=betatemp$logdens+Lambdatemp$logdens+Sigmatemp$logdens;
    logliktempdat=0;
    for (jj in 1:M)
      logliktempdat=logliktempdat-0.5*C*log(2*pi)-0.5*determinant(Sigmatemp$Sigma)$modulus[1]-0.5*t(residstemp[jj,])%*%solve(Sigmatemp$Sigma)%*%(residstemp[jj,]);
    
    logliktemp=logliktemp+logliktempdat;	
    
    # update the chain of samples when appropriate
    thincounter=thincounter+1;
    if (thincounter==thinby){
      chaincounter=chaincounter+1; thincounter=0;
      beta.mat[mcmcit,,]=betatemp$beta;
      Lambda.mat[mcmcit,,,]=Lambdatemp$Lambda;
      Sigma.mat[mcmcit,,]=Sigmatemp$Sigma;
      loglik.mat[mcmcit,]=c(sum(residstemp^2),logliktemp);
      if (chaincounter%%100==0){print(chaincounter); }
      
      if ((nprint>0) && (chaincounter%%nprint==0)){
        chtemp=chaincounter/nprint;
      }	
    }	
    
  }
  return(list(beta=beta.mat,Lambda=Lambda.mat,Sigma=Sigma.mat,loglik=loglik.mat));
}

MCMCfrontend=function(Xs,Ys,N.grid=500,N.eig=c(25,25,25),max.ord=c(25,8,6),X.lim=NULL,Y.lim=NULL,inclmat=NULL) {
  ## P is number of inputs and model parameters variables, C is number of outputs, M is the number of model runs
  P=ncol(Xs); C=ncol(Ys); M=nrow(Xs);
  
  # set up BSS-ANOVA design matrix
  Y.trans=trans.output(Ys);
  if (!is.null(Y.lim)) Y.trans=trans.output(Ymat=Ys,Y.lim=Y.lim);
  t.grid=seq(0,1,length=N.grid);
  Phi=get.bss.basis3(t.grid);  
  if (P>0){
  	X.trans=trans.input(Xs); 
  	if (!is.null(X.lim)) {
  		X.trans$trans=trans.pred(Xmat=Xs,X.lim=X.lim); 
  		X.trans$lim=X.lim;	
  	}
  	if (is.null(inclmat)){
    		inclmat=get.inclmat(P,N.eig);
  	}
  	intermat=get.intermat(t.mat=X,N.eig=N.eig,max.ord=max.ord,inclmat=inclmat);	
  	X.em=get.all.X(t.mat=X.trans$trans,t.grid=t.grid,Phi=Phi,intermat=intermat,P=N.eig,cat.vars=NULL);
  }
  if (P==0){
  	X.trans=list();
  	X.trans$trans=Xs;
  	X.trans$lim=X.lim;
  	inclmat$incl=matrix(0,0,0); inclmat$neig=0;
  	intermat=matrix(0,nrow=1,ncol=2); #Include constant basis function 
  	X.em=matrix(1,nrow(Xs),1); 	
  }

  # compute matrices for use in updating betas once.
	Xsm=gettrXXmatr(X.em,inclmat,intermat);	
	return(list(X.trans=X.trans,Y.trans=Y.trans,inclmat=inclmat,intermat=intermat,X.em=X.em,Xsm=Xsm,Phi=Phi,t.grid=t.grid,N.eig=N.eig));	
}

### Bernoulli polynomials
B1 <- function(x)
  return(x-1/2)
# second Bernoulli polynomial
B2 <- function(x)
  return(x^2-x+1/6)
B4 <- function(x)
  return(x^4-2*x^3+x^2-1/30)

boscocov2.mat <- function(x1, x2 = NULL, sigma2){
  if(is.null(x2)){
    x2 <- x1
  }
  n1 <- length(x1)
  n2 <- length(x2)
  x1.ext <- rep(x1, times = n2)
  x2.ext <- rep(x2, each = n1)
  ans <- sigma2[1]+sigma2[2]*B1(x1.ext)*B1(x2.ext)+sigma2[3]*B2(x1.ext)*B2(x2.ext)-sigma2[4]/24*B4(abs(x1.ext-x2.ext))
  Cov.mat <- matrix(ans, nrow = n1, ncol = n2)
  return(Cov.mat)
}

### create discretized eigenfunctions
get.bss.basis3 <- function(t.grid){
  flag <- 0
  ## some logic to account for a singularity if 0 and 1 are both in t.grid
  if(min(t.grid)==0 && max(t.grid==1)){
    t.grid <- t.grid[-length(t.grid)]
    flag <- 1
  }
  
  N <- length(t.grid)
  Gamma <- boscocov2.mat(t.grid,sigma2=c(0,1,1,1))
  
  ans <- eigen(Gamma)
  lambda <- ans$values
  lambda[lambda<0] <- 0
  X <- ans$vectors
  ## Below I'm attaching the eigenvalue to the function from the get go,
  ## so the coefficients (betas) can all have the same variance.
  Phi <- matrix(sqrt(lambda),N,N,byrow=TRUE)*X
  if(flag)
    Phi <- rbind(Phi,Phi[1,])
  return(Phi)
}

### "evaluate" the eigenfunctions
get.main.X <- function(t,P,Phi,t.grid,mult=1,cat.var=0){
  n <- length(t)
  if(cat.var==0){
    ## for each value of t (in [0,1]), give the linear interpolation of the closest two rows of Phi 
    X=matrix(1,n,P)
    for(i in 1:n){
      lo=max(sum(t[i]>t.grid),1)
      diff.lo=t[i]-t.grid[lo]
      diff.hi=t.grid[lo+1]-t[i]
      w=diff.hi/(diff.lo + diff.hi)
      X[i,1:P] <- w*Phi[lo,1:P]+(1-w)*Phi[lo+1,1:P]
    }
  } else{
    X <- matrix(0,n,cat.var)
    for(j in 1:cat.var)
      X[,j] <- (cat.var-1)/cat.var*(t==j) - 1/cat.var*(t!=j)
  }
  return(X)
}

### pick combinations of sums less than a certain value, return the first numeig of them
## Inputs:
## numeig - number of eigenfunctions needed
## max.ord - maximum total order
## numvar - how many interactions
getsum1=function(numeig,max.ord,numvar){
  combraw=matrix(NA,max.ord^numvar,numvar);
  for (i in 1:numvar)
    combraw[,i]=rep(1:max.ord,each=max.ord^(numvar-i),times=max.ord^(i-1));
  idx1=order(apply(combraw,1,sum));
  combmat=as.matrix(combraw[idx1,]);
  return(as.matrix(combmat[1:numeig,]));    
}

### make inclusion matrix with all possible interactions
### also make neig matrix that specifies # of eigenfunctions for component
get.inclmat=function(numvar,N.eig){
  N.ord=min(numvar,length(N.eig));
  inclmat=list();
  inclmat$incl=matrix(NA,0,N.ord);
  inclmat$neig=matrix(NA,0,1); 
  for (ii in 1:N.ord){
    tempmat=matrix(NA,choose(numvar,ii),N.ord); tempmat[]=-1;
    tempmat[,1:ii]=t(combn(numvar,ii)); 
    inclmat$incl=rbind(inclmat$incl,tempmat);	
    
    neigtemp=matrix(NA,choose(numvar,ii),1);
    neigtemp[,1]=N.eig[ii];
    inclmat$neig=rbind(inclmat$neig,neigtemp);
  }
  return(inclmat);
}

get.lastcol.intermat=function(intermat){
  intermat=floor(intermat);
  nbeta=nrow(intermat);
  codedvals=matrix(0,nbeta,1);
  
  for (ii in 2:nbeta){
    numord=sum(intermat[ii,-1]>0)/2;
    codedvals[ii,1]=1;
    if (numord>1){
      temp1=intermat[ii,-1];
      temp1[(2*(numord-1)+(1:2))]=-1;
      codedvals[ii,1]=which(apply(as.matrix(intermat[1:ii,-1]),1,identical,temp1)==1);
    }
  }
  return(as.matrix(codedvals))	
}

### make interaction matrix
## Inputs:
## t.mat - matrix of inputs (in our case columns are x,p,T,thetas)
## t.grid - the domain grid used for discritizing the basis functions on [0,1]
## Phi - the discretized eigenfunctions from K1 evaluated at each value of t.grid
## P - a 4-vector of how many eigeinfunctions to use for main effect, two-way, and
##     eventually 3-way interactions
## max.ord - the maximum total order (i.e., the sum of order of the baisis functions)
##           allowed in products of basis functions for interactions
## inclmat- optional input of preselected interactions to include, if NULL all interactions are included 
## Outputs:
## intmatr set of interactions that are included
## last column is the link to the index of the component without last term - used for faster computation of multi-order functions

get.intermat=function(t.mat,N.eig,max.ord,inclmat=NULL){	
  if (is.null(inclmat)){
    inclmat=list();
    inclmat=get.inclmat(ncol(t.mat),N.eig);
  }
  n=nrow(inclmat$incl); p=ncol(inclmat$incl);
  intermat=matrix(NA,nrow=1,ncol=2*p+1);
  intermat[1,]=c(0,rep(0,2*p));  #Include constant basis function
  
  for (ii in 1:n){
    numord=sum(inclmat$incl[ii,]>0);  #find the order of interaction
    tempmat2=getsum1(inclmat$neig[ii],max.ord[numord],numord);
    tempmat1=matrix(NA,nrow=inclmat$neig[ii],ncol=2*p+1);
    
    tempmat1[]=-1; tempmat1[,1]=0;	#first column is beta coefficient
    for (jj in 1:numord){
      tempmat1[,2*jj]=inclmat$incl[ii,jj];
      tempmat1[,(2*jj+1)]=tempmat2[,jj];
    }		
    intermat=rbind(intermat,tempmat1);	
  }
  
  # find row numbers of component that doesn't include last term	
  lastcol=get.lastcol.intermat(intermat);
  intermat=cbind(intermat,lastcol);
  return(intermat)
}

get.all.basis=function(firstordmat,intermat,n){
  nbeta=nrow(intermat); ncol=ncol(intermat);
  Xmat=matrix(NA,n,nbeta); Xmat[]=1;
  
  for (ii in 2:nbeta){
    numord=sum(intermat[ii,-c(1,ncol)]>0)/2;
    Xmat[,ii]=Xmat[,intermat[ii,ncol]]*as.matrix(firstordmat[,intermat[ii,2*numord+1],intermat[ii,2*numord]]); 
  }	
  return(as.matrix(Xmat))
}

### set up full BSS-Anova matrix
## This function returns the entire design matrix of basis functions ...
## Inputs:
## t.mat - matrix of inputs (in our case columns are x,p,T,thetas)
## t.grid - the domain grid used for discritizing the basis functions on [0,1]
## Phi - the discretized eigenfunctions from K1 evaluated at each value of t.grid
## P - a 4-vector of how many eigeinfunctions to use for main effect, two-way, and
##     eventually 3-way interactions
## max.ord - the maximum total order (i.e., the sum of order of the baisis functions)
##           allowed in products of basis functions for interactions

get.all.X=function(t.mat,t.grid,Phi,intermat,P,cat.vars=NULL){
  
  n=nrow(t.mat); p=ncol(t.mat);
  neig=P[1];
  firstordmat=array(NA,c(n,neig,p));  # array of first order basis functions
  
  # compute all first order functions
  for (ii in 1:p){
    firstordmat[,,ii]=get.main.X(t.mat[,ii],neig,Phi,t.grid);			
  }
  # compute full BSS-Anova design matrix by computing interactions
  Xmat=get.all.basis(firstordmat,intermat,n);
  return(Xmat);
}

### compute matrix of t(X)%*%X once to feed into the updatebeta function
### also compute indices of full BSS-ANOVA design matrix
gettrXXmatr=function(X.em,inclmat,intermat) {
  Xsm=list();
  Xsm$idx=list(); Xsm$matr1=list(); Xsm$matr2=list(); Xsm$matr3=list();
  for (ii in 0:nrow(inclmat$incl)){
    if (ii==0) {idx1=1;}
    if (ii>0){	
      idx1=which(apply(as.matrix(intermat[,2*(1:ncol(inclmat$incl))]),1,identical,inclmat$incl[ii,]));
    }
    bigXsm=as.matrix(X.em[,idx1,drop=F]); # separate out columns of interest for design matrix
    
    Xsm$idx[[ii+1]]=idx1;
    Xsm$matr1[[ii+1]]=bigXsm;
    Xsm$matr2[[ii+1]]=t(bigXsm)%*%(bigXsm);
  }
  # get cross matrices
  for (jj1 in 0:nrow(inclmat$incl)){
    for (jj2 in 0:nrow(inclmat$incl)){
      Xsm$matr3[[jj1+1+(jj2)*(nrow(inclmat$incl)+1)]]=t(Xsm$matr1[[jj1+1]])%*%Xsm$matr1[[jj2+1]];
    }
  }
  return(Xsm);
}

### update betas
updatebeta=function(beta,resids,Lambda,Sigma,inclmat,Xsm,Xsmresids,y.trans,X.em,intermat){
  N.beta=nrow(beta); C=ncol(beta);
  betanew=beta;
  logdens=0;
  Sigmatemp.inv=solve(as.matrix(Sigma));
  resids2=resids;

  for (ii in 0:nrow(inclmat$incl)){
    idx1=Xsm$idx[[ii+1]];
    bigXsm=Xsm$matr1[[ii+1]]; betasm=as.matrix((betanew[idx1,])); # separate out columns of interest for design matrix and beta.
    if (ii==0){betasm=t(betasm);}
    # update residuals
    y.minusk=resids2+bigXsm%*%betasm;
    Lambdatemp.inv=solve(as.matrix(Lambda[idx1[1],,]));
    if (C==1) {Var.post.inv=Sigmatemp.inv[1,1]*(Xsm$matr2[[ii+1]])+Lambdatemp.inv[1,1]*diag(rep(1,length(idx1)));}
    if (C>1) {Var.post.inv=Sigmatemp.inv%x%(Xsm$matr2[[ii+1]])+Lambdatemp.inv%x%diag(rep(1,length(idx1)));}
    Var.post=solve(Var.post.inv);
    if (C==1) {
      mu.post=Var.post%*%(Sigmatemp.inv[1,1]*(t(bigXsm)%*%resids2+Xsm$matr2[[ii+1]]%*%betasm));
    }
    if (C>1) {
    		mu.post=Var.post%*%((Sigmatemp.inv%x%(t(bigXsm)))%*%as.vector(y.minusk));
    		mu.post.old=Var.post%*%as.vector((t(bigXsm)%*%resids2+Xsm$matr2[[ii+1]]%*%betasm)%*%Sigmatemp.inv);
    		}
    betanew[idx1,]=rmultnorm(mu.post,Var.post);
    resids2=resids2+bigXsm%*%(betasm-betanew[idx1,]);
    logdenstemp=0;
    for (kk in 1:length(idx1)){
      logdenstemp=logdenstemp-0.5*C*log(2*pi)+0.5*determinant(Lambdatemp.inv)$modulus-0.5*t(betasm[kk,])%*%Lambdatemp.inv%*%(betasm[kk,]);
    }
    logdens=logdens+logdenstemp;
  }
  return(list(beta=betanew,logdens=logdens[1],resids=resids2,Xsmresids=Xsmresids));
}

rmultnorm=function(mu,Var,inv=T){
  normsamp=rnorm(length(mu));
  ans=t(chol(Var))%*%normsamp+mu;
  return(ans);
}

### update lambdas
updatelambda=function(beta,priors1,inclmat,Xsm,intermat){
  N.beta=nrow(beta); M=ncol(beta);
  Lambda=array(1,c(nrow(beta),M,M));
  
  # compute Lambda_0
  Plambda=beta[1,]%*%t(beta[1,])+priors1$mu; 
  nu=1+priors1$nu;
  Lambda[1,,]=as.matrix(riwish(nu,Plambda));
  logdens=log(diwish(as.matrix(Lambda[1,,]),nu,Plambda));
  if (nrow(inclmat$incl)>0){
  	for (ii in 1:nrow(inclmat$incl)){
    		idx1=Xsm$idx[[ii+1]];
    		betasm=as.matrix(beta[idx1,]); #separate out columns of interest for beta.
    		Plambda=t(betasm)%*%(betasm)+priors1$mu; 
    		nu=length(idx1)+priors1$nu;
    		tempLambda=as.matrix(riwish(nu,Plambda));
    		for (jj in idx1)
     	 Lambda[jj,,]=tempLambda;
    # compute log density of this prior
    		logdens=logdens+log(diwish(tempLambda,priors1$nu,priors1$mu));
  	}
  }
  return(list(Lambda=Lambda,logdens=logdens));
}

updatesigma=function(resids,priors1){
  N=nrow(resids); M=ncol(resids);
  Sigma=array(1,c(M,M));
  # compute Sigma
  PSigma=t(resids)%*%resids+priors1$mu; 
  nu=N+priors1$nu;
  Sigma=as.matrix(riwish(nu,PSigma));
  logdens=log(diwish(Sigma,priors1$nu,priors1$mu));	
  
  return(list(Sigma=Sigma,logdens=logdens));
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

# ======================================================================
# ======================================================================

if (interactive) {
  args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned
  xfile <- args[1]        # training input
  yfile <- args[2]        # training output (ground truth)
  rdsfile <- args[3]      # trained model will save to R binary
  
  bte = args[4]           # vector containing...
                          #   B: burn-in (toss out this many iterations from beginning)
                          #   T: total number of MCMC iterations
                          #   E: how often to record (keep every e-th sample)
  nterms <- args[5]       # number of basis functions to use in K-L expansion
                          #   for each BSSANOVA component
  order <- args[6]        # order of interaction terms for BSS-ANOVA
  
  nterms = as.numeric(nterms)
  order = as.numeric(order)
  
  # parse BTE vector
  s = strsplit(bte,'[^[:digit:]]')   # split string at non-digits
  s = as.numeric(unlist(s))          # convert strings to numeric ('' becomes NA)
  s = unique(s[!is.na(s)])           # remove NA and duplicates
  bte = s
  
  X = read.table(xfile, sep=',', header=TRUE)
  nx = ncol(X)
  X = as.matrix(X[,1:nx])
  Y = read.table(yfile, sep=',', header=TRUE)
  ny = ncol(Y)
  Y = as.matrix(Y[,1:ny])
  model <- SolventFit_emul(X, Y, burnin=bte[1], nmcmc=bte[2], thinby=bte[3], nterms=nterms, order=order)
  saveRDS(model, rdsfile)
}
