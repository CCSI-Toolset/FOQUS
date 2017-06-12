##########################################################
############### BSSANOVA Function ########################
##########################################################

bssanova <- function(X, y, BTE=c(200, 1000, 1), cat.pos="auto", min.distinct=7, n.terms=25, lambda=2, int.order=2, l2.min=0, priorprob=.5){

########## INPUTS ############################################################
## X         - a matrix of predictors.
## y         - a vector of responses.
## BTE       - 3-vector specifying number of iterations for
##             (i) burn-in (toss out this many from the beginning),
##             (ii) total number of MCMC iterations, and
##             (iii) how often to record (keep every E samples).
## cat.pos   - vector containg the columns to be treated as categorical
## min.distinct - minimum number of distinct values to treat a predictor as
##                continuous (instead of categorical).  Only used if
##                categorical="auto".
## n.terms   - Number of eigenvalues to use to approximate BSSANOVA covariance
##             More the merrier, but slows down computation with too many.
## lambda    - Half-Cauchy hyperparameter
## int.order - the order of interactions to consider (1 or 2).
## l2.min    - minimum proportion of variance by a functional component to be
##             included in the variable order ranking (set to 0 to include all)
## prior.prob- the prior probability that a given component is uninformative
##############################################################################

########## OUTPUTS ###########################################################
## bss.model - a list with the elements...
##             * fittedvalues,fittedsds are the posterior means and sds 
##                       of f at the data points:
##             * inprob is the posterior inclusion probability
##             * l2 is the posterior distribution of the l2 norm of each component
##             * curves and curvessd are the posterior means and sds of the
##               individual components f_{ij}
##             * r is the posterior distribution of the variance r
##             * predmn is the posterior predicive mean of f(xnew) 
##             * term1 and term2 index the compnents f_{ij}.  For example, if
##               term1[j]=3 and term2[j]=4 then curves[,j] is the posterior 
##               mean of ef_{3,4}.  Terms with terms1[j]=terms2[j] 
##               are main effects
##             * dev is the posterior samples of the deviance
##             * int is the posterior samples of the intercept
##             * sigma is the posterior samples of the error sd
## yhat      - predicted values at the rows of the X matrix
## Rsq       - R^2 of the posterior mean function fit
## order     - Variable order importance according to total variance
##             (assuming uniform distribution for inputs)
##############################################################################

  X <- as.matrix(X)
  n <- nrow(X)
  nx <- ncol(X)
  if(length(dimnames(X)[[2]]) == 0){
    dimnames(X)[[2]] <- list()
    dimnames(X)[[2]] <- paste("x", 1:nx, sep="")
  }

  runs<-BTE[2]       #number of MCMC samples
  burn<-BTE[1]	      #Toss out these many
  update<-25         #How often to display the current iteration?
  n.terms<-n.terms   #Number of eigenvalues to keep
  lambda<-lambda     #Half-Cauchy hyperparameter			

  interactions <- (int.order>1) #Include interactions?

  ## Identify categorical vars 
  if(cat.pos[1]=='auto'){
   # scan for variables with min.distinct or less distinct values. 
    cat.pos <- numeric(0)
    for(i in index(1,nx)){
      unique.i <- unique(X[,i])
      if(length(unique.i)<=min.distinct || is.character(X[,i])){
        cat.pos <- c(cat.pos, i)
      }
    }
  }
  categorical <- rep(FALSE, nx)
  categorical[cat.pos] <- TRUE
  
  bss.model<-BSSANOVA(y,X,categorical=categorical,lambda=lambda,nterms=n.terms,twoway=interactions,runs=runs,burn=burn,update=update,priorprob=priorprob)

  res <- y-bss.model$fittedvalues
  yhat <- bss.model$fittedvalues
  SSE <- sum(res^2)
  SSTot <- sum((y-mean(y))^2)
  SSReg <- SSTot - SSE
  Rsq <- SSReg/SSTot

  l2.t <- numeric(nx)
  l2 <- colMeans(bss.model$l2)
  for(j in 1:nx)
    l2.t[j] <- sum(l2[bss.model$term1==j | bss.model$term2==j])/sum(l2)
  var.ord <- order(-l2.t)
  num.gt.min <- sum(l2.t>l2.min)
  var.ord <- var.ord[1:num.gt.min]
  
  return(list(bss.model=bss.model, yhat=yhat, Rsq=Rsq, order=var.ord))
}

########################################################################
########## Other Functions Used in the Creation of BSSANOVA ############
########################################################################

index <- function(m,n){
  if(m<=n) return(m:n)
  else return(numeric(0))
}

BSSANOVA<-function(y,x,categorical=NA,
    runs=10000,burn=2000,update=10,
    ae=.01,be=.01,priorprob=0.5,nterms=25,lambda=2,
    main=T,twoway=F,const=10,init.sigma=NA){

#########  Definitions of the input    ################:
#  y is the n*1 vector of data
#  x is the n*p design matrix
#  categorical is the p-vector indicating (TRUE/FALSE) which
#       columns of x are categorical variables
#  runs is the number of MCMC samples to generate
#  burn is the number of samples to discard as burnin
#  update is the number of interations between displays
#  error variance sigma^2~Gamma(ae,be)
#  priorprob is the prior includion probability for 
#       each functional component
#  nterms is the number of eigenvector to retain
#  lambda is the hyperparameters in the half-Cauchy prior
#  main indicates whether to include main effects
#  twoway incicates whether to include interactions
#  const is the relative variance for the polynomial trend
#  init.sigma is the initial value for the error sd

  #set some sample size parameters 
  n<-length(y)
  ncurves<-0
  p<-ncol(x)
  if(is.na(mean(categorical))){categorical<-rep(F,p)}

  if(main){ncurves<-ncurves+p}
  if(twoway){ncurves<-ncurves+p*(p-1)/2}
  term1<-term2<-rep(0,ncurves)
  if(p>0){o1<-order(x[,1])}
  if(p>1){o2<-order(x[,2])}
  if(p>2){o3<-order(x[,3])}
  if(p>3){o4<-order(x[,4])}

  #Set up the covariance matrices for the main effects
  B<-array(0,c(ncurves,n,nterms))
  Gamma<-array(0,c(ncurves,nterms,nterms))
  D<-matrix(0,nterms,ncurves)
  GammaB<-array(0,c(ncurves,nterms,n))
  count<-1

  theta.basis<-make.eig.functions(const=const,npts=500,nterms=nterms,nknots=100)

  #set up the covariances for the main effects
  if(main){
     for(j in 1:p){
       term1[count]<-term2[count]<-j
       if(!categorical[j]){
          B[count,,]<-makeB.cont(x[,j],theta.basis)
          eig<-eigen(t(B[count,,])%*%(B[count,,]))
          Gamma[count,,]<-eig$vectors
          D[,count]<-abs(eig$values)   
          GammaB[count,,]<-t(Gamma[count,,])%*%t(B[count,,])
       }
       if(categorical[j]){
          B[count,,]<-makeB.cat(x[,j],ncats=max(x[,j]),nterms=nterms)
          eig<-eigen(t(B[count,,])%*%(B[count,,]))
          Gamma[count,,]<-eig$vectors
          D[,count]<-abs(eig$values)   
          GammaB[count,,]<-t(Gamma[count,,])%*%t(B[count,,])
       }
       count<-count+1
     }
  }

  #set up the covariances for the two-way interactions
  if(twoway){
     for(j1 in 2:p){
       for(j2 in 1:(j1-1)){
         term1[count]<-j1;term2[count]<-j2
         term<-1
         for(k1 in 1:round(sqrt(nterms))){
           for(k2 in 1:round(sqrt(nterms)+1)){
              if(term<=nterms){
                 B[count,,term]<-B[j1,,k1]*B[j2,,k2]
                 term<-term+1
              }
           }
         }
         eig<-eigen(t(B[count,,])%*%(B[count,,]))
         Gamma[count,,]<-eig$vectors
         D[,count]<-abs(eig$values)   
         GammaB[count,,]<-t(Gamma[count,,])%*%t(B[count,,])
         count<-count+1
       }
     }  
  }

  ########                 Initial values      ###################
  int<-mean(y)
  sige<-ifelse(is.na(init.sigma),0.5*sd(lm(y~x)$residuals),init.sigma)
  taue<-1/sige^2
  curves<-matrix(0,n,ncurves)
  curfit<-int+sige*apply(curves,1,sum)
  r<-rep(0,ncurves)

  #keep track of the mean of the fitted values
  afterburn<-0
  sumfit<-sumfit2<-rep(0,n)
  suminout<-rep(0,ncurves)
  sumcurves<-sumcurves2<-matrix(0,n,ncurves)
  keepr<-keepl2<-matrix(0,runs,ncurves)
  dev<-keepsige<-keepint<-rep(0,runs)
  theta<-array(0,c(ncurves,runs,nterms))

  npts<-50
  if(priorprob==1){mxgx<-grid<-c(seq(0.0001,2,length=npts/2),seq(2,1000,length=npts/2))}
  if(priorprob<1){mxgx<-grid<-c(seq(0,2,length=npts/2),seq(2,1000,length=npts/2))} 

  ########             Start the sampler       ###################
  countiter<-0
  sdy<-sd(y)
  acc<-att<-0;mh<-sdy/10;
  for(i in 1:runs){
   sumcurv<-apply(curves,1,sum)

   #new sige
   if(F){
      cansige<-rnorm(1,sige,mh)
      if(cansige>0 & cansige<2*sdy){
        att<-att+1  
        R<-sum(dnorm(y,int+cansige*sumcurv,cansige,log=T))-
           sum(dnorm(y,int+sige*sumcurv,sige,log=T))
        if(runif(1)<exp(R)){sige<-cansige;acc<-acc+1}
        taue<-1/sige^2
      }
   }

   #new taue
   cantaue<-rnorm(1,taue,0.05*sd(y))
   if(cantaue>0){
     cansige<-1/sqrt(cantaue)
     MHrate<-sum(dnorm(y,int+cansige*apply(curves,1,sum),cansige,log=T))
     MHrate<-MHrate-sum(dnorm(y,int+sige*apply(curves,1,sum),sige,log=T))
     MHrate<-MHrate+dgamma(cantaue,ae,rate=be,log=T)-dgamma(taue,ae,rate=be,log=T) 
     if(runif(1)<exp(MHrate)){taue<-cantaue;sige<-cansige}
   }

   if(i<burn & att>50){
     mh<-mh*ifelse(acc/att<0.2,0.5,1)*ifelse(acc/att>.6,1.5,1)
     acc<-att<-0
   }

   #new intercept
   int<-rnorm(1,mean(y-sige*sumcurv),sige/sqrt(n))
 
   #new curves
   for(j in 1:ncurves){
      #first draw the sd:

      ncp<-min(c(median(keepr[1:i,j]),10))
      if(i==1){npc<-5}
      ncp<-min(c(median(keepr[,j]),2))
      mxgx<-grid<-c(0,qt(seq(0.01,0.99,length=npts-1),1,ncp))
      mxgx<-grid<-grid[grid>=0]
      rrr<-y-int-sige*apply(curves[,-j],1,sum)
      z<-GammaB[j,,]%*%rrr
      for(jjj in 1:length(grid)){
         mxgx[jjj]<-g(grid[jjj],z,sige,D[,j],priorprob=priorprob,lambda=lambda)-
                    log(dcan(grid[jjj],ncp,priorprob=priorprob))
      } 

      big<-max(mxgx)
      highpt<-1.05*max(exp(mxgx-big))
      ratio<-0
      if(highpt==0){r[j]<-10;ratio<-1}
      while(ratio<1){
        r[j]<-rcan(1,ncp,priorprob)
        lll<-g(r[j],z,sige,D[,j],priorprob=priorprob,lambda=lambda)-
             log(dcan(r[j],ncp,priorprob=priorprob))
        ratio<-exp(lll-big)/highpt/runif(1)
        if(is.na(ratio)){ratio<-0}
      }

      #then draw the curve
      if(r[j]==0){curves[,j]<-0}
      if(r[j]>0){
        var<-r[j]/(r[j]*D[,j]+1)
        theta[j,i,]<-sqrt(var)*rnorm(nterms)
        theta[j,i,]<-Gamma[j,,]%*%(theta[j,i,]+var*z/sige)
        curves[,j]<-B[j,,]%*%theta[j,i,]
      }
   }

   #Record results:
   keepr[i,]<-r  
   keepl2[i,]<-apply(curves^2,2,mean)
   fit<-int+sige*apply(curves,1,sum)
   dev[i]<- -2*sum(dnorm(y,fit,sige,log=T))
   keepsige[i]<-sige
   keepint[i]<-int

   if(i>burn){
      afterburn<-afterburn+1
      sumfit<-sumfit+fit
      sumfit2<-sumfit2+fit^2
      suminout<-suminout+ifelse(r>0,1,0)
      sumcurves<-sumcurves+sige*curves
      sumcurves2<-sumcurves2+(sige*curves)^2
    }
  }

  #Calculate posterior means:
  fitmn<-sumfit/afterburn
  fitsd<-sqrt(sumfit2/afterburn-fitmn^2)
  curves<-sumcurves/afterburn
  curvessd<-sqrt(sumcurves2/afterburn-curves^2)
  probin<-suminout/afterburn

#########  Definitions of the output    ################:
# fittedvalues,fittedsds are the posterior means and sds 
#                        of f at the data points:
# inprob is the posterior inclusion probability
# l2 is the posterior distribution of the l2 norm of each component
# curves and curvessd are the posterior means and sds of the
#                     individual components f_{ij}
# r is the posterior distribution of the variance r
# predmn is the posterior predicive mean of f(xnew) 
# term1 and term2 index the compnents f_{ij}.  For example, if
#     term1[j]=3 and term2[j]=4 then curves[,j] is the posterior 
#     mean of f_{3,4}.  Terms with terms1[j]=terms2[j] 
#     are main effects
# dev is the posterior samples of the deviance
# int is the posterior samples of the intercept
# sigma is the posterior samples of the error sd

list(fittedvalues=fitmn,fittedsds=fitsd,inprob=probin,l2=keepl2[burn:runs,],
     curves=curves,curvessd=curvessd,r=keepr[burn:runs,],
     term1=term1,term2=term2,dev=dev,int=keepint,sigma=keepsige,
     x=x,categorical=categorical,nterms=nterms,main=main,
     twoway=twoway,const=const,theta=theta,burn=burn,runs=runs,
     theta.basis=theta.basis)
}

priorr<-function(r,priorprob=0.5,lambda=2){
  ifelse(r==0,1-priorprob,priorprob*2*dt(sqrt(r)/lambda,1)/lambda)
}

rcan<-function(n,ncp,priorprob=0.5){
  if(priorprob==1){rrr<-abs(rt(n,1,ncp=ncp))}
  if(priorprob<1){rrr<-ifelse(runif(n,0,1)<0.975,abs(rt(n,1,ncp=ncp)),0)}
rrr}

dcan<-function(r,ncp,priorprob=0.5){
  if(priorprob==1){2*dt(r,1,ncp=ncp)}
  if(priorprob<1){rrr<-ifelse(r==0,1-0.975,0.975*2*dt(r,1,ncp=ncp))}
rrr}

g<-function(r,z,sige,d,priorprob=.5,lambda=2){
   lll<- -sum(log((r*d+1)))+sum(r*z*z/(r*d+1))/sige^2
0.5*lll+log(priorr(r,priorprob,lambda=lambda))}

#Define Bernoulli polynomials
B0<-function(x){1+0*x}
B1<-function(x){x-.5}
B2<-function(x){x^2-x+1/6}
B3<-function(x){x^3-1.5*x^2+.5*x}
B4<-function(x){x^4-2*x^3+x^2-1/30}
B5<-function(x){x^5-2.5*x^4+1.667*x^3-x/6}
B6<-function(x){x^6-3*x^5+2.5*x^4-.5*x^2+1/42}

makeB.cat<-function(x.pred,ncats,nterms){
  xxx<-1:ncats
  sss<-matrix(xxx,ncats,ncats,byrow=T)
  ttt<-matrix(xxx,ncats,ncats,byrow=F)
  equals<-ifelse(sss==ttt,1,0)
  COV<-(ncats-1)*equals/ncats -(1-equals)/ncats
  COV<-COV/mean(diag(COV))
  eig<-eigen(COV);
  Gamma<-eig$vectors%*%diag(sqrt(abs(eig$values)))
  B<-matrix(0,length(x.pred),nterms)
  for(j in 1:(ncats-1)){
     dat<-list(y=Gamma[,j],x=xxx)
     pred.dat<-list(x=x.pred)
     fit<-lm(y~as.factor(x),data=dat)
     B[,j]<-predict(fit,newdata=pred.dat)
  }
B}      
 
make.basis.bosco<-function(x,n.knots){
   B<-matrix(1,length(x),n.knots)
   knots<-seq(0,1,length=n.knots-2)[-(n.knots-2)]
   B[,2]<-x
   B[,3]<-x*x
   for(j in 1:length(knots)){
      B[,j+3]<-ifelse(x>knots[j],(x-knots[j])^3,0)
   }
B}

make.eig.functions<-function(const=10,npts=1000,nterms=25,nknots){
  xxx<-seq(0,1,length=npts)
  sss<-matrix(xxx,length(xxx),length(xxx),byrow=T)
  ttt<-matrix(xxx,length(xxx),length(xxx),byrow=F)
  diff<-as.matrix(dist(xxx,diag=T,upper=T))
  COV<-const*(B1(sss)*B1(ttt)+B2(sss)*B2(ttt)/4)-B4(diff)/24
  COV<-COV/mean(diag(COV[1:npts,1:npts]))
  eig<-eigen(COV);
  Gamma<-eig$vectors[,1:nterms]%*%
            diag(sqrt(abs(eig$values[1:nterms])))
  B<-make.basis.bosco(xxx,nknots)
  theta<-matrix(0,nknots,nterms)
  for(j in 1:nterms){
     theta[,j]<-lm(Gamma[,j]~B-1)$coef
  }
theta}  

makeB.cont<-function(x.pred,theta){
  X<-make.basis.bosco(x.pred,nrow(theta))
X%*%theta}      

# ======================================================================
# ======================================================================
args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned
xfile <- args[1]        # training input
yfile <- args[2]        # training output (ground truth)
rdsfile <- args[3]      # trained model will save to R binary

bte = args[4]           # vector containing...
                        #   B: burn-in (toss out this many iterations from beginning)
                        #   T: total number of MCMC iterations
                        #   E: how often to record (keep every e-th sample)
cat <- args[5]          # vector containing columns to be treated as categorical 
nterms <- args[6]       # number of eigenvalues to approximate BSSANOVA covariance 
order <- args[7]        # order of interactions (1 or 2)
p <- args[8]            # prior prob that a given component is uninformative

nterms = as.numeric(nterms)
order = as.numeric(order)
p = as.numeric(p)

# parse categorical vector
if(!identical(cat,'auto')) {
  s = strsplit(cat,'[^[:digit:]]')   # split string at non-digits
  s = as.numeric(unlist(s))          # convert strings to numeric ('' becomes NA)
  s = unique(s[!is.na(s)])           # remove NA and duplicates
  cat = s
}

# parse BTE vector
s = strsplit(bte,'[^[:digit:]]')   # split string at non-digits
s = as.numeric(unlist(s))          # convert strings to numeric ('' becomes NA)
s = unique(s[!is.na(s)])           # remove NA and duplicates
bte = s

X = read.table(xfile, sep=',', header=TRUE)
nx = ncol(X)
X = X[,1:nx]
y = read.table(yfile, sep=',', header=TRUE)
y = y[,1]                          # assume one output
bssanova.fit <- bssanova(X, y, BTE=bte, cat.pos=cat, n.terms=nterms, int.order=order, priorprob=p)
saveRDS(bssanova.fit, rdsfile)
