suppressPackageStartupMessages(library(abind))

###############################################################
# SOLVENTFIT CALIBRATION PREDICTION
###############################################################

getfullcalibpred=function(Xsinput,uqout,nsamp=100,transf=TRUE,incl.em=TRUE,incl.disc=TRUE,pred.func=NULL){
  
  if (Xsinput[1,1]==-999.999) Xsinput=matrix(0,nrow(Xsinput),0);
  
  C=ncol(uqout$calibout$chain$sigma); 
  thetaraw=uqout$calibout$chain$theta;
  idx1=nrow(thetaraw)-15*(1:nsamp);
  Npar=ncol(thetaraw)-2;
  theta=thetaraw[idx1,1:(Npar),drop=F];
  
  predscalib=list();
  predscalib$preds=array(0,c(nrow(Xsinput),nrow(theta),C));
  
  predsdisc=list();
  predsdisc$preds=array(0,c(nrow(Xsinput),nrow(theta),C));
  predsem=array(0,c(nrow(Xsinput),nrow(theta),C));
  
  incl.em=(is.null(uqout$inputs$ctrl1$mod$name))
  
  if (incl.em){
    beta.em=uqout$calibout$betamatem;
    frontend.em=uqout$emulout$frontend;
    N.grid.em=length(frontend.em$t.grid);
    for (ii in 1:nrow(theta)){
      predsemtemp=getemulpred1(theta[ii,],Xsinput,beta.em,frontend.em,transf=transf,N.grid=N.grid.em);
      predsem[,ii,]=predsemtemp$meanpred;
      predscalib$preds[,ii,]=predsemtemp$meanpred;
    }
  }
  
  if (!incl.em){
  	pred.func=list();
  	pred.func$name=uqout$inputs$ctrl1$mod$name;
  	pred.func$inputs=list();
  	
    FUN1=match.fun(pred.func$name);
    for (ii in 1:nrow(theta)){
      pred.func$inputs$Xmat=cbind(Xsinput,matrix(1,nrow(Xsinput),1)%x%theta[ii,,drop=F]);
	  predtemp=FUN1(pred.func$inputs)$yout; 
	  if (C>1) predtemp=t(predtemp);
      predsem[,ii,]=predtemp;
      predscalib$preds[,ii,]=predsem[,ii,];
    }
  }
  
  if (!is.null(uqout$calibout$chain$disc)){
    beta.disc=uqout$calibout$chain$disc[idx1,,,drop=F];
    frontend.disc=uqout$calibout$frontend.disc;
    N.grid.disc=length(frontend.disc$t.grid);
    predsdisc=getdiscpred1(Xsinput,beta.disc,frontend.disc,transf=transf,N.grid=N.grid.disc);
  }
  
  predscalib$preds=predscalib$preds+predsdisc$preds;  
  predscalib$meanpred=apply(predscalib$preds,c(1,3),mean);

  return(list(em=predsem,disc=predsdisc,calib=predscalib));
  
}

########################
# Support functions
########################

getdiscpred1=function(Xsinput,beta,frontend,transf=FALSE,N.grid=500){
  
  N.inp=ncol(Xsinput); M=nrow(Xsinput); C=dim(beta)[3];
  if (transf) {
    X.lim=frontend$X.trans$lim; Y.lim=frontend$Y.trans$lim;
    if (N.inp>0) Xsinput=trans.pred(Xsinput,X.lim);
  } 
  N.eig=frontend$N.eig;
  intermat=frontend$intermat;  Phi=frontend$Phi; 
  t.grid=seq(0,1,length=N.grid);
  X.pred=matrix(1,M,1);
  
  if (N.inp>0){
  	ord1.inp=get1ordinp(Xsinput=Xsinput,frontend=frontend,N.grid=N.grid);
  	firstordmat=ord1.inp;
  	X.pred=get.all.basis(firstordmat,intermat,M);
  }
  # compute full BSS-Anova design matrix by computing interactions
  preds=array(0,c(M,dim(beta)[1],C));
  meanpred=matrix(0,M,C);
  for (jj in 1:C){
	nbeta=t(as.matrix(beta[,,jj]));
	if (dim(beta)[1]==1 && dim(beta)[3]==1) {nbeta=t(nbeta);}
	preds[,,jj]=X.pred%*%nbeta;
	if (transf) {preds=preds*Y.lim[jj,2];}	
	meanpred[,jj]=apply(preds[,,jj,drop=F],1,mean);
}
  # nbeta=t(as.matrix(beta[,,1]));
  # if (dim(beta)[1]==1 && dim(beta)[3]==1) {nbeta=t(nbeta);}
  # preds=X.pred%*%nbeta;
  # if (transf) {preds=preds*Y.lim[1,2];}	
  # meanpred=apply(preds,1,mean);	
  return(list(preds=preds,meanpred=as.matrix(meanpred)));		
}

### get emulator predictions for single theta
getemulpred1=function(theta,Xsinput,beta,frontend,transf=TRUE,N.grid=500){
  
  N.eig=frontend$N.eig;
  N.inp=ncol(Xsinput); N.par=length(theta); P=N.inp+N.par;
  M=nrow(Xsinput); C=dim(beta)[3];
  intermat=frontend$intermat;  Phi=frontend$Phi; t.grid=frontend$t.grid;
  
  if (transf) {
    X.lim=frontend$X.trans$lim; Y.lim=frontend$Y.trans$lim;
    if (N.inp>0) Xsinput=trans.pred(Xsinput,X.lim[1:N.inp,,drop=F]);
    theta=trans.pred(theta,X.lim[(1:N.par)+N.inp,,drop=F]);
  } 
  firstordmat=array(NA,c(M,N.eig[1],N.par));  #array of first order basis functions
  
  # compute all first order functions
  for (ii in 1:N.par){
    temp1=get.main.X(theta[ii],N.eig[1],Phi,t.grid)
    firstordmat[,,ii]=t(as.matrix(replicate(M,temp1[1,])));			
  }
  if (N.inp>0){
  	ord1.inp=get1ordinp(Xsinput=Xsinput,frontend=frontend,N.grid=N.grid);	
  	firstordmat=abind(ord1.inp,firstordmat,along=3);
  }
  # compute full BSS-Anova design matrix by computing interactions
  X.pred=get.all.basis(firstordmat,intermat,M);
  preds=array(0,c(M,dim(beta)[1],C));
  meanpred=matrix(0,M,C);
  for (jj in 1:C){
	nbeta=t(as.matrix(beta[,,jj]));
	preds[,,jj]=X.pred%*%nbeta;
	if (transf) {preds[,,jj]=apply(preds[,,jj,drop=F],2,backtrans.output,Y.lim[jj,,drop=F]);}	
	meanpred[,jj]=apply(preds[,,jj,drop=F],1,mean);
}
  
  
  # X.pred=get.all.basis(firstordmat,intermat,M);
  # nbeta=t(as.matrix(beta[,,1]));
  # if (dim(beta)[1]==1 && dim(beta)[3]==1) {nbeta=t(nbeta);}
  # preds=X.pred%*%nbeta;
  # if (transf) {preds=apply(preds,2,backtrans.output,Y.lim);}	
  # meanpred=apply(preds,1,mean);
  
  return(list(preds=preds,meanpred=as.matrix(meanpred)));		
}

get1ordinp=function(Xsinput,frontend,N.grid=500){
  
  N.eig=frontend$N.eig;
  Phi=frontend$Phi; t.grid=seq(0,1,length=N.grid);
  
  N.inp=ncol(Xsinput); M=nrow(Xsinput); C=dim(beta)[3];
  firstordmat=array(NA,c(M,N.eig[1],N.inp));  # array of first order basis functions
  
  #compute all first order functions
  for (ii in 1:N.inp){
    firstordmat[,,ii]=get.main.X(Xsinput[,ii],N.eig[1],Phi,t.grid);			
  }
  return(firstordmat);	
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

### transform inputs to [0,1]
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

### transform outputs back to original scale
backtrans.output=function(Ymat,Y.lim){
  transmat=Ymat;
  if (is.null(ncol(transmat)))
    transmat=matrix(transmat,nrow=length(transmat)/nrow(Y.lim),ncol=nrow(Y.lim));
  
  for (j in 1:nrow(Y.lim)){
    Y.mean=Y.lim[j,1]; Y.sd=Y.lim[j,2];	
    transmat[,j]=(transmat[,j]*Y.sd+Y.mean);
  }
  return(as.matrix(transmat));
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

#actual model for Morris function

#form of inputs are [t,par1,..,park]
morrisfunc=function(inps)
{
	
	s=(sum(inps[-1])-1.5)/1.5;
	fx=(1+sign(s)*(abs(s))^0.3)/2
	
	#output=fx*(-log(1-inps[1]));
	out1=fx*inps[1]^2*5;
	output=out1;
	
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
rdsfile <- args[1]   # rds file containing model
infile <- args[2]    # test data containing inputs
outfile <- args[3]   # test data containing predicted outputs
outrdsfile <- args[4]   # rds file for predictions
disc <- args[5]      # boolean indicating whether discrepancy should be included

nsamples <- args[6]  # number of samples from the posterior distribution of beta coefficients
                     #   to be used in evaluating predictions
transform <-args[7]  # boolean indicating whether input values should be mapped to range [0,1]
emul <- args[8]      # boolean indicating whether BSS-ANOVA emulator should be used
                     #    if set to FALSE, then pred.func must be set (not currently supported)

disc = as.numeric(disc)
nsamples = as.numeric(nsamples)
transform = as.numeric(transform)
emul = as.numeric(emul)

X.new = read.table(infile, header=FALSE, skip=1)  # skip first line
nx = ncol(X.new)
X.new = as.matrix(X.new[,2:nx]) # ignore row names
model = readRDS(rdsfile)
pred <- getfullcalibpred(Xsinput=X.new, uqout=model, nsamp=nsamples,
                         transf=transform, incl.em=emul, incl.disc=disc, pred.func=NULL) 
Yhat <- pred$calib$meanpred
write.table(Yhat, file=outfile, sep=' ', row.names=TRUE, col.names=FALSE, quote=FALSE)
print(outrdsfile);
saveRDS(pred, outrdsfile);