###############################################################
# SOLVENTFIT EMULATOR PREDICTION
###############################################################

# get emulator predictions for set of inputs/parameters
getfullemulpred=function(Xsinput,emulout,nsamp=50,transf=TRUE) {
  
  frontend=emulout$frontend;
  
  betafull=emulout$postdist$beta;
  beta=betafull[nrow(betafull)-15*(1:nsamp),,,drop=F];
  
  N.eig=frontend$N.eig; N.grid=length(frontend$t.grid);
  M=nrow(Xsinput); C=dim(beta)[3];
  intermat=frontend$intermat;  Phi=frontend$Phi; t.grid=frontend$t.grid;
  
  if (transf) {
    X.lim=frontend$X.trans$lim; Y.lim=frontend$Y.trans$lim;
    Xsinput=trans.pred(Xsinput,X.lim[,,drop=F]);
  } 
  firstordmat=get1ordinp(Xsinput=Xsinput,frontend=frontend,N.grid=N.grid);
  
  # compute full BSS-Anova design matrix by computing interactions
  X.pred=get.all.basis(firstordmat,intermat,M);
  nbeta=t(as.matrix(beta[,,1]));
  if (dim(beta)[1]==1 && dim(beta)[3]==1) {nbeta=t(nbeta);}
  preds=X.pred%*%nbeta;
  if (transf) {
    preds=as.matrix(apply(preds,2,backtrans.output,Y.lim));
    if (nrow(X.pred)==1) {preds=t(preds)}	
  }	
  meanpred=apply(preds,1,mean);
  
  return(list(preds=preds,meanpred=as.matrix(meanpred)));		
}

########################
# Support functions
########################

### "Evaluate" the eigenfunctions
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

get.all.basis=function(firstordmat,intermat,n){
  
  nbeta=nrow(intermat); ncol=ncol(intermat);
  Xmat=matrix(NA,n,nbeta); Xmat[]=1;
  
  for (ii in 2:nbeta){
    numord=sum(intermat[ii,-c(1,ncol)]>0)/2;
    Xmat[,ii]=Xmat[,intermat[ii,ncol]]*as.matrix(firstordmat[,intermat[ii,2*numord+1],intermat[ii,2*numord]]); 
  }	
  return(as.matrix(Xmat))
}

get1ordinp=function(Xsinput,frontend,N.grid=500){
  
  N.eig=frontend$N.eig;
  Phi=frontend$Phi;  t.grid=seq(0,1,length=N.grid);
  
  N.inp=ncol(Xsinput); M=nrow(Xsinput); C=dim(beta)[3];
  firstordmat=array(NA,c(M,N.eig[1],N.inp));  # array of first order basis functions
  
  # compute all first order functions
  for (ii in 1:N.inp){
    firstordmat[,,ii]=get.main.X(Xsinput[,ii],N.eig[1],Phi,t.grid);			
  }
  return(firstordmat);	
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

# ======================================================================
# ======================================================================

args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned
rdsfile <- args[1]   # rds file containing model
infile <- args[2]    # test data containing inputs
outfile <- args[3]   # test data containing predicted outputs

nsamples <- args[4]  # number of samples from the posterior distribution of beta coefficients
                     #   to be used in evaluating predictions
transform <-args[5]  # boolean indicating whether input values should be mapped to range [0,1]

nsamples = as.numeric(nsamples)
transform = as.numeric(transform)

X.new = read.table(infile, header=FALSE, skip=1)  # skip first line
nx = ncol(X.new)
X.new = as.matrix(X.new[,2:nx]) # ignore row names
model = readRDS(rdsfile)
pred <- getfullemulpred(Xsinput=X.new, emulout=model, nsamp=nsamples, transf=transform) 
Yhat <- pred$meanpred
write.table(Yhat, file=outfile, sep=' ', row.names=TRUE, col.names=FALSE, quote=FALSE)
