library("MASS")
library("quadprog")

##########################################################
############### ACOSSO Function ##########################
##########################################################

acosso <- function(X, y, order=2, wt.pow=1, cv='bic', w, lambda.0, gcv.pen=1.01, categorical="auto", min.distinct=7){

########## INPUTS ############################################################
## X        - a matrix of predictors
## y        - a vector of responses
## order    - the order of interactions to consider (1 or 2)
## wt.pow   - the weights used in the adaptive penalty are ||P^j||^{-wt.pow} 
##            wt.pow=0 is the COSSO
## cv       - the method used to select the tuning parameter M from the ACOSSO
##            paper. (the tuning paramter is actually called K in this code).
##            Options are '5cv', 'gcv', and 'bic', or a numeric value to use 
##            for M
## w        - optional vector to use for w (only used if 'cv' is numeric)
## lambda.0 - optional value to use for lambda.0 (only used if 'cv' is numeric)
## categorical - vector containg the columns to be treated as categorical
## min.distinct - minimum number of distinct values to treat a predictor as
##                continuous (instead of categorical).  Only used if
##                categorical="auto".
##############################################################################

########## OUTPUTS ###########################################################
## c.hat   - coefficients of the Kernel representation f(x)=mu+sum K(x_i,x)*c
## mu.hat  - estimated constant in above representation
## y.hat   - vector of the predicted y's
## res     - vector of the residuals
## dfmod   - approximate degrees of freedom of the fit
## w       - adaptive weights used in the estimation
## gcv     - gcv score
## bic     - bic score
## theta   - estimated theta vector
## Rsq     - R^2 = 1-SSE/SSTOT
## Gram    - Gram matrix.  The (i,j)th element is K(x_i,x_j)
## y.mat   - Matrix of fitted y's for each functional component 
##           (i.e. y.hat = mu.hat + sum(y.mat))
## X       - the original matrix of predictors
## y	     - the original vector of inputs
## rescale - Did the data need to be rescaled to (0,1).  Used for prediction.
## order   - the order of interactions specified
## K	     - the value of K chosen by cv
## lambda.0- The value used for lambda.0
##############################################################################

if(!is.numeric(cv)){
  ans.cv <- venus.cv(X, y, order=order, cv=cv, wt.pow=wt.pow, w='L2', f.est='trad', seed=110, K.lim='data', nK=5, gcv.pen=gcv.pen, rel.K=5E-2, nlambda=5, lambda.lim=c(1E-10, 1E3), rel.lambda=5E-2, rel.theta=1E-2, maxit=2, init.cv='gcv', cat.pos=categorical, min.distinct=min.distinct)

  lambda.0 <- ans.cv$lambda.0
  K <- ans.cv$K
  fit.acosso <- venus(X, y, order=order, K=ans.cv$K, gcv.pen=gcv.pen, maxit=5, rel.tol=1E-2, cv='gcv', lambda.0=ans.cv$lambda.0, w=ans.cv$w, seed=110, cat.pos=ans.cv$cat.pos, min.distinct=min.distinct)
}

else{  ## use a prespecified numerical value for K
  K <- cv
  if(missing(w)||missing(lambda.0)){
    ans.cv <- venus.cv(X, y, order=order, cv='gcv', wt.pow=wt.pow, w='L2', f.est='trad', seed=110, K.lim='data', nK=5, gcv.pen=gcv.pen, rel.K=5E-2, nlambda=5, lambda.lim=c(1E-10, 1E3), rel.lambda=5E-2, rel.theta=1E-2, maxit=2, init.cv='gcv', cat.pos=categorical, min.distinct=min.distinct)
    w <- ans.cv$w
    lambda.0 <- ans.cv$lambda.0
  }
  fit.acosso <- venus(X, y, order=order, K=K, gcv.pen=gcv.pen, maxit=5, rel.tol=1E-2, cv='gcv', lambda.0=lambda.0, w=w, seed=110, cat.pos=ans.cv$cat.pos, min.distinct=min.distinct)
}

fit.acosso$order <- order
fit.acosso$K <- K
fit.acosso$lambda.0 <- lambda.0

return(fit.acosso)

}

##############################################################################
############# Other Functions Used in the Creation of ACOSSO #################
##############################################################################

index <- function(m,n){
  if(m<=n) return(m:n)
  else return(numeric(0))
}

which.equal <- function(x, y){
  n <- length(x)
  ans <- rep(0,n)
  for(i in 1:n){
    ans[i] <- any(approx.equal(y,x[i]))
  }
  return(as.logical(ans))
}

approx.equal <- function(x, y, tol=1E-9){
  return(abs(x - y) < tol)
}

## Generates a matrix whose columns are random samples from 1:n
get.obs.ind <- function(n, nfolds=5, seed=220){

  replace.seed <- T
  if(missing(seed))
    replace.seed <- F

  if(replace.seed){
   ## set seed to specified value
    if(!any(ls(name='.GlobalEnv', all.names=T)=='.Random.seed')){
      set.seed(1)
    }
    save.seed <- .Random.seed
    set.seed(seed)  
  }

  perm <- sample(1:n, n)
  n.cv <- rep(floor(n/nfolds),nfolds)
  rem <- n - n.cv[1]*nfolds
  n.cv[index(1,rem)] <- n.cv[index(1,rem)]+1
  obs.ind <- list()
  ind2 <- 0
  
  for(i in 1:nfolds){
    ind1 <- ind2+1
    ind2 <- ind2+n.cv[i]
    obs.ind[[i]] <- perm[ind1:ind2]
  }
  if(replace.seed){
   ## restore random seed to previous value
    .Random.seed <<- save.seed
  }
  return(obs.ind)
}

################################
##### Sobolev RK function ######
################################

k1 <- function(t){
  return(t-.5)
}
k2 <- function(t){
  return( (k1(t)^2-1/12)/2 )
}
k4 <- function(t){
  return( (k1(t)^4-k1(t)^2/2+7/240)/24 )
}
K.sob <- function(s,t){
  ans <- k1(s)*k1(t) + k2(s)*k2(t) - k4(abs(s-t))
  return(ans)
}
K.cat <- function(s,t,G){
  ans <- (G-1)/G*(s==t) - 1/G*(s!=t) 
  return(ans)
}

#########################################################################
##### Create cross reference for kth component & ij th interaction ######
#########################################################################

get.int2ind <- function(p){

 ## create int2ind and ind2int to be able to switch back and forth between
 ##  i,j th interaction and kth component
  P <- p + choose(p,2)
  int2ind <- matrix(0,p,p)
  ind2int <- matrix(NA,P,2)
  diag(int2ind) <- index(1,p)
  ind2int[index(1,p),] <- cbind(index(1,p), index(1,p))
  next.ind <- p+1
  for(i in index(1,p-1)){
    for(j in index(i+1,p)){
      int2ind[i,j] <- int2ind[j,i] <- next.ind
      ind2int[next.ind,] <- c(i,j)
      next.ind <- next.ind+1
    }
  }
  return(list(int2ind=int2ind, ind2int=ind2int))
}

#########################################################################
############ Creates p Gram matrices, 1 for each predictor  #############
#########################################################################

get.gram <- function(X1, X2, order, cat.pos){

 ## Calculates K(X1[i,j]
  n1 <- nrow(X1)
  n2 <- nrow(X2)
  p <- ncol(X1)
  gram <- list()
  if(length(cat.pos)>0)
    cont.pos <- (1:p)[-cat.pos]
  else
    cont.pos <- (1:p)
  
  for(i in cont.pos){
    x1 <- rep(X1[,i], times=n2)
    x2 <- rep(X2[,i], each=n1)
    ans <- K.sob(x1,x2)
    gram[[i]] <- matrix(ans, n1, n2)
  }
  for(i in cat.pos){
    x1 <- rep(X1[,i], times=n2)
    x2 <- rep(X2[,i], each=n1)
    G <- length(unique(x1))
    ans <- K.cat(x1,x2,G)
    gram[[i]] <- matrix(ans, n1, n2)
  }
  if(order==2){
    next.ind <- p+1
    for(i in index(1,p-1)){
      for(j in index(i+1,p)){
        gram[[next.ind]] <- gram[[i]]*gram[[j]]
        next.ind <- next.ind+1
      }
    }
  }
  return(gram)
}

#########################################################################
############# Fits a penalized spline for given theta's  ################
#########################################################################

pen.spline <- function(X, y, order=1, lambda.0=1, theta, gcv.pen=1.01,
                       Gram, cv='gcv', seed=220){

  n <- nrow(X)
  p <- ncol(X)
  if(order==1)
    P <- p
  else
    P <- p + choose(p,2)
  
  if(missing(theta))
    theta <- 1
  if(length(theta)==1)
    theta <- rep(theta,P)

 ## shift and rescale x's to [0,1]
  rescale <- rep(F, p)
  for(i in 1:p){
    if(any( X[,i]<0 | X[,i]>1)){
      X[,i] <- (X[,i]-min(X[,i]))/(max(X[,i])-min(X[,i]))
      rescale[i] <- T
    }
  }

 ## Get Gram Matrix
  if(missing(Gram)){
   ## Get Gram Matrix
    Gram <- get.gram(X, X, order=order, cat.pos=numeric(0))
  }

 ############### Use 5 fold CV ##################
  if(cv=='5cv'){
    y.hat <- numeric(n)
    obs.ind <- get.obs.ind(n, nfolds=5, seed=seed)
    for(i in 1:5){
      X.i <- as.matrix(X[-obs.ind[[i]],])
      y.i <- y[-obs.ind[[i]]]
      Gram.i <- list()
      for(j in 1:P)
        Gram.i[[j]] <- (Gram[[j]])[-obs.ind[[i]],-obs.ind[[i]]]
      fit.i <- pen.spline(X.i, y.i, order=order, lambda.0=lambda.0,theta=theta,
                          cv='gcv', gcv.pen=gcv.pen, Gram=Gram.i)
                          
      K.theta <- matrix(0,n,n)
      for(j in 1:P)
        K.theta <- K.theta + fit.i$theta[j]*Gram[[j]]
      y.hat[obs.ind[[i]]]<- K.theta[obs.ind[[i]],-obs.ind[[i]]]%*%fit.i$c.hat +
                             fit.i$mu.hat 
    }
    fit.spline <- pen.spline(X, y, order=order, lambda.0=lambda.0, theta=theta,
                             cv='gcv', gcv.pen=gcv.pen, Gram=Gram)
    gcv <- sum((y-y.hat)^2)
    mu.hat <- fit.spline$mu.hat
    c.hat <- fit.spline$c.hat
    y.hat <- fit.spline$y.hat
    y.mat <- fit.spline$y.mat
    res <- fit.spline$res
    df <- fit.spline$df 
    Rsq <- fit.spline$Rsq
    bic <- fit.spline$bic
    norm <- fit.spline$norm
  }


 ############### Use GCV ##################
  else{  ## Use gcv

    K.theta <- matrix(0,n,n)
    for(i in 1:P){
      K.theta <- K.theta + theta[i]*Gram[[i]]
    }

    K.inv <- solve(K.theta + lambda.0*diag(n))
    J <- rep(1,n)
    alpha <- sum(K.inv)^(-1)*t(J)%*%K.inv
    mu.hat <- as.numeric(alpha%*%y)
    c.hat <- K.inv%*%(y-J*mu.hat)
    H <- K.theta%*%K.inv%*%(diag(n)-J%*%alpha)+J%*%alpha

    y.hat <- mu.hat + K.theta%*%c.hat
    res <- y-y.hat
    SSE <- sum(res^2)
    Rsq <- 1-SSE/sum((y-mean(y))^2)
    df <- sum(diag(H)) 
    if(gcv.pen*df >= n)
      gcv <- Inf
    else
      gcv <- SSE/(1-gcv.pen*df/n)^2
    bic <- n*log(SSE/n) + df*log(n)
    norm <- numeric(P)
    for(i in 1:P){
      norm[i] <- t(c.hat)%*%(theta[[i]]^2*Gram[[i]])%*%c.hat
    }
    y.mat <- matrix(0,n,P)
    for(i in 1:P){
      y.mat[,i] <- theta[[i]]*Gram[[i]]%*%c.hat
    }
  
  }

  return(list(mu.hat=mu.hat, c.hat=c.hat, y.hat=y.hat, res=res, dfmod=df, 
              gcv=gcv, bic=bic, Rsq=Rsq, norm=norm, y.mat=y.mat, X=X, y=y,
              theta=theta, Gram=Gram, w=rep(1,P), rescale=rescale))
}

#########################################################################
##### used by VENUS: solves for beta.hat and c.hat for fixed theta's ####
#########################################################################

get.H.c <- function(Gram, y, theta, lambda.0, w, gcv.pen){

  n <- length(y)
  P <- length(theta)

  K.theta <- matrix(0,n,n)
  for(i in 1:P){
    K.theta <- K.theta + theta[i]*w[i]^2*Gram[[i]]
  }
  K.inv <- solve(K.theta + lambda.0*diag(n))
  J <- rep(1,n)
  alpha <- sum(K.inv)^(-1)*t(J)%*%K.inv
  mu.hat <- as.numeric(alpha%*%y)
  c.hat <- K.inv%*%(y-J*mu.hat)
  H <- K.theta%*%K.inv%*%(diag(n)-J%*%alpha)+J%*%alpha

  df <- sum(diag(H))
  y.hat <- mu.hat + K.theta%*%c.hat
  res <- y-y.hat
  SSE <- sum(res^2)
  if(gcv.pen*df >= n)
    gcv <- Inf
  else
    gcv <- SSE/(1-gcv.pen*df/n)^2
  bic <- n*log(SSE/n) + df*log(n)
  Rsq <- 1-SSE/sum((y-mean(y))^2)

  return(list(mu.hat=mu.hat, H=H, df=df, y.hat=y.hat, gcv=gcv, Rsq=Rsq,
              c.hat=c.hat, bic=bic))
}

#######################################################################
############# used by VENUS: solves for theta for fixed c's ###########
#######################################################################

get.theta.hat <- function(Gram, mu.hat, c.hat, y, lambda.0, theta.0.ind, K, w){

      n <- length(y)
      P <- length(Gram)
      if(length(theta.0.ind)==0)
        keep.col <- 1:P
      else
        keep.col <- (1:P)[-theta.0.ind]
      G <- matrix(NA,n,P)

      for(i in 1:P){
        G[,i] <- w[i]^2*Gram[[i]]%*%c.hat
      }
      G.red <- G[,keep.col]
      P.red <- length(keep.col)
      D <- t(G.red)%*%G.red
      d <- t( (t(y) - mu.hat - .5*lambda.0*t(c.hat))%*%G.red )
      A <- t(rbind(diag(1,P.red), rep(-1,P.red)))
      b.0 <- c(rep(0,P.red), -K)

      opt.ans <- try(solve.QP(D, d, A, b.0, meq=0), silent=T)
      add.to.diag <- sum(diag(D)/ncol(D))*1E-10
      while(is.character(opt.ans)){
        add.to.diag <- add.to.diag*10
        opt.ans <- try(solve.QP(D+diag(add.to.diag,P.red), d, A, b.0, meq=0), silent=T)
      }

      theta.new <- opt.ans$solution
      theta <- rep(0,P)
      theta[keep.col] <- theta.new
      return(theta)
}

#######################################################################
######### VENUS for a fixed smoothing param M   #######################
#######################################################################

venus <- function(X, y, K, order=1, gcv.pen=1.01,lambda.0, theta.0, rel.tol=1E-2,
                  maxit=2, Gram, cv='gcv', w, seed=220, 
                  alpha=.05, nvar=ncol(X), nfit=20, cat.pos="auto",
                  min.distinct=7){

  n <- nrow(X)
  p <- ncol(X)
  if(order==1)
    P <- p
  else
    P <- p + choose(p,2)
  if(missing(lambda.0))
    lambda.0 <- .01
  if(missing(theta.0))
    theta.0 <- rep(1,P)
  if(missing(w))
    w <- rep(1,P)
  if(length(w)==1)
    w <- rep(w,P)
  theta.hat <- theta.0

  ## Identify categorical vars 
  if(length(cat.pos)>0 && cat.pos[1]=='auto'){
   # scan for variables with min.distinct or less distinct values. 
    cat.pos <- numeric(0)
    for(i in 1:p){
      unique.i <- unique(X[,i])
      if(length(unique.i)<=min.distinct || is.character(X[,i])){
        cat.pos <- c(cat.pos, i)
      }
    }
  }

  if(length(cat.pos)>0)
    cont.pos <- (1:p)[-cat.pos]
  else
    cont.pos <- (1:p)
  ## shift and rescale continuous x's to [0,1]
  rescale <- rep(F, p)
  X.orig <- X
  for(i in cont.pos){
    if(any( X[,i]<0 | X[,i]>1)){
      X[,i] <- (X[,i]-min(X[,i]))/(max(X[,i])-min(X[,i]))*.9 + .05
      rescale[i] <- T
    }
  }

 ## Get Gram Matrix
  if(missing(Gram)){
    Gram <- get.gram(X, X, order=order, cat.pos=cat.pos)
  }

 ############### Use 5 fold CV ##################
  if(cv=='5cv'){
    y.hat <- numeric(n)
    obs.ind <- get.obs.ind(n, nfolds=5, seed=seed)
    for(i in 1:5){
      X.i <- as.matrix(X[-obs.ind[[i]],])
      y.i <- y[-obs.ind[[i]]]
      Gram.i <- list()
      for(j in 1:P)
        Gram.i[[j]] <- (Gram[[j]])[-obs.ind[[i]],-obs.ind[[i]]]
      fit.i<-venus(X=X.i, y=y.i, order=order, K=K, gcv.pen=gcv.pen, 
                   lambda.0=.8*lambda.0, theta.0=theta.0, rel.tol=rel.tol,
                   maxit=maxit, Gram=Gram.i, cv='gcv', w=w,
                   min.distinct=min.distinct)
      K.theta <- matrix(0,n,n)
      for(j in 1:P)
        K.theta <- K.theta + fit.i$theta[j]*w[j]^2*Gram[[j]]

      y.hat[obs.ind[[i]]]<- K.theta[obs.ind[[i]],-obs.ind[[i]]]%*%fit.i$c.hat +
                             fit.i$mu.hat 
    }

    fit.venus <- venus(X=X, y=y, order=order, K=K, gcv.pen=gcv.pen, 
                       lambda.0=lambda.0, theta.0=theta.0, rel.tol=rel.tol, 
                       maxit=maxit, Gram=Gram, cv='gcv', w=w,
                       min.distinct=min.distinct)
    fit.venus$Gram <- NULL
    gcv <- sum((y-y.hat)^2)
    mu.hat <- fit.venus$mu.hat
    c.hat <- fit.venus$c.hat
    y.hat <- fit.venus$y.hat
    res <- fit.venus$res
    df <- fit.venus$df 
    theta.hat <- fit.venus$theta
    Rsq <- fit.venus$Rsq
    bic <- fit.venus$bic
  }
    
 ############### Use 10 fold CV ##################
  else if(cv=='10cv'){
    y.hat <- numeric(n)
    obs.ind <- get.obs.ind(n, nfolds=10, seed=seed)
    for(i in 1:10){
      X.i <- as.matrix(X[-obs.ind[[i]],])
      y.i <- y[-obs.ind[[i]]]
      Gram.i <- list()
      for(j in 1:P)
        Gram.i[[j]] <- (Gram[[j]])[-obs.ind[[i]],-obs.ind[[i]]]
      fit.i<-venus(X=X.i, y=y.i, order=order, K=K, gcv.pen=gcv.pen, 
                   lambda.0=.9*lambda.0, theta.0=theta.0, rel.tol=rel.tol,
                   maxit=maxit, Gram=Gram.i, cv='gcv', w=w,
                   min.distinct=min.distinct)
      K.theta <- matrix(0,n,n)
      for(j in 1:P)
        K.theta <- K.theta + fit.i$theta[j]*w[j]^2*Gram[[j]]

      y.hat[obs.ind[[i]]]<- K.theta[obs.ind[[i]],-obs.ind[[i]]]%*%fit.i$c.hat +
                             fit.i$mu.hat 
    }

    fit.venus <- venus(X=X, y=y, order=order, K=K, gcv.pen=gcv.pen, 
                       lambda.0=lambda.0, theta.0=theta.0, rel.tol=rel.tol, 
                       maxit=maxit, Gram=Gram, cv='gcv', w=w,
                       min.distinct=min.distinct)
    fit.venus$Gram <- NULL
    gcv <- sum((y-y.hat)^2)
    mu.hat <- fit.venus$mu.hat
    c.hat <- fit.venus$c.hat
    y.hat <- fit.venus$y.hat
    res <- fit.venus$res
    df <- fit.venus$df 
    theta.hat <- fit.venus$theta
    Rsq <- fit.venus$Rsq
    bic <- fit.venus$bic
  }
    
 ############### Use type I Error Rate ##################
  else if(cv=='var'){
    for(i in 1:nfit){
      X.i <- as.matrix(X[-obs.ind[[i]],])
      y.i <- y[-obs.ind[[i]]]
      Gram.i <- list()
      for(j in 1:P)
        Gram.i[[j]] <- (Gram[[j]])[-obs.ind[[i]],-obs.ind[[i]]]
      fit.i<-venus(X=X.i, y=y.i, order=order, K=K, gcv.pen=gcv.pen, 
                   lambda.0=lambda.0, theta.0=theta.0, rel.tol=rel.tol,
                   maxit=maxit, Gram=Gram.i, cv='gcv', w=w,
                   min.distinct=min.distinct)
      K.theta <- matrix(0,n,n)
      for(j in 1:P)
        K.theta <- K.theta + fit.i$theta[j]*w[j]^2*Gram[[j]]

      y.hat[obs.ind[[i]]]<- K.theta[obs.ind[[i]],-obs.ind[[i]]]%*%fit.i$c.hat +
                             fit.i$mu.hat 
    }

    fit.venus <- venus(X=X, y=y, order=order, K=K, gcv.pen=gcv.pen, 
                       lambda.0=lambda.0, theta.0=theta.0, rel.tol=rel.tol, 
                       maxit=maxit, Gram=Gram, cv='gcv', w=w,
                       min.distinct=min.distinct)
    fit.venus$Gram <- NULL
    gcv <- sum((y-y.hat)^2)
    mu.hat <- fit.venus$mu.hat
    c.hat <- fit.venus$c.hat
    y.hat <- fit.venus$y.hat
    res <- fit.venus$res
    df <- fit.venus$df 
    theta.hat <- fit.venus$theta
    Rsq <- fit.venus$Rsq
    bic <- fit.venus$bic
  }
    
 ############### Use gcv ##################
  else{

   ## Solve for c.hat when theta=theta.0
    H.c <- get.H.c(Gram, y, theta.0, lambda.0, w, gcv.pen)
    mu.hat <- H.c$mu.hat
    c.hat <- H.c$c.hat
    df <- H.c$df
    y.hat <- H.c$y.hat
    res <- H.c$res
    gcv <- H.c$gcv
    bic <- H.c$bic
    Rsq <- H.c$Rsq

   ## Iterative solving for theta, then c ...
    iter <- 1

    theta.0.ind <- which(theta.hat < 1E-9 | w==0)

    repeat{
      if(iter > maxit){
        break
      }
      iter <- iter + 1

     ## First solve for theta for a fixed c
      if(K==0){
        theta.new <- rep(0,P)
      }
      else{
        theta.new <- get.theta.hat(Gram, mu.hat, c.hat, y, lambda.0, 
                                   theta.0.ind, K, w)
        if(any(theta.new == -1)||any(is.na(theta.new))){### prob with solution
          theta.new <- theta.hat
        }
      }

      theta.0.ind <- which(theta.new <= 1E-9 | w==0)
      theta.new[theta.0.ind] <- 0

     ## Now solve for c.hat for a fixed theta
      H.c <- get.H.c(Gram, y, theta.new, lambda.0, w, gcv.pen)
      mu.hat <- H.c$mu.hat
      c.hat <- H.c$c.hat
      H <- H.c$H
      df <- H.c$df
      y.hat <- H.c$y.hat
           

      res <- H.c$res
      gcv <- H.c$gcv
      bic <- H.c$bic
      Rsq <- H.c$Rsq

     ## Now check for convergence
      divisor <- theta.new
      divisor[theta.new < 1E-6] <- 1
      rel.norm <- sqrt(sum(((theta.hat-theta.new)/divisor)^2))

      if(rel.norm < rel.tol){
        theta.hat <- theta.new
        break
      }
      theta.hat <- theta.new
    }  
  }
  y.mat <- matrix(0,n,P)
  for(i in 1:P){
    y.mat[,i] <- theta.hat[i]*w[i]^2*Gram[[i]]%*%c.hat
  }
  return(list(c.hat=c.hat, mu.hat=mu.hat, y.hat=y.hat, res=res, dfmod=df,
              w=w, gcv=gcv, bic=bic, theta=theta.hat, Rsq=Rsq, Gram=Gram, 
              y.mat=y.mat, X=X, X.orig=X.orig, y=y, rescale=rescale,
              cat.pos=cat.pos))
}

#######################################################################
################# GET NORMS FOR A VENUS OBJECT  #######################
#######################################################################

get.venus.norms <- function(obj){

  y.mat <- obj$y.mat
  P <- ncol(y.mat)
  c.hat <- obj$c.hat
  Gram <- obj$Gram
  theta <- obj$theta
  w <- obj$w

  L2.norm <- numeric(P)
  H2.norm <- numeric(P)
  for(i in 1:P){
    H2.norm[i] <- sqrt(theta[i]^2*w[i]^4*t(c.hat)%*%(Gram[[i]])%*%c.hat)
    L2.norm[i] <- sqrt(mean((y.mat[,i])^2))
  }

  return(list(L2.norm=L2.norm, H2.norm=H2.norm))
}

#######################################################################
######### ESTIMATE w VIA FULL SMOOTHING SPLINE ###################
#######################################################################
           
get.w <- function(X, y, order, lambda.lim, nlambda=3, gcv.pen, wt.pow,
                  rel.tol, df.lim, w='L2', w.0=1, w.lim=c(1E-10, 1E10), Gram,
                  cat.pos){

  n <- nrow(X)
  p <- ncol(X)
  if(order==1)
    P <- p
  else
    P <- p + choose(p,2)  

  if(missing(df.lim)){
    df.lim <- c(0,.5*n)
  }

  if(w[1]!='L2' && w[1]!='RKHS'){
    if(length(w)==1)
      w <- rep(w,P)
    w.0 <- w
  }
  else if(length(w.0)==1){
    w.0 <- rep(w.0,P)
  }

 ## shift and rescale x's to [0,1]
  for(i in 1:p){
    if(any( X[,i]<0 | X[,i]>1)){
      X[,i] <- (X[,i]-min(X[,i]))/(max(X[,i])-min(X[,i]))
    }
  }

 ## Get Gram Matrix
  if(missing(Gram)){
    Gram <- get.gram(X, X, order=order, cat.pos=cat.pos)
  }
  K.theta <- matrix(0,n,n)
  for(i in 1:P){
    K.theta <- K.theta + w.0[i]^2*Gram[[i]]
  }
  lambda.min <- lambda.lim[1]
  lambda.max <- lambda.lim[2]
  log.lambda.best <- .01
  LAMBDAMIN <- log(lambda.min)
  LAMBDAMAX <- log(lambda.max)
  log.lambda.min <- LAMBDAMIN
  log.lambda.max <- LAMBDAMAX
  inc <- (log.lambda.max - log.lambda.min)/(nlambda-1)
  log.lambda.vec <- seq(log.lambda.min, log.lambda.max, inc)
  log.lambda.old <- log.lambda.vec
  gcv.best <- Inf

  repeat{
    nlambda.now <- length(log.lambda.vec)
    df.vec <- rep(0, length(log.lambda.vec))
    for(j in 1:nlambda.now){
      llambda <- log.lambda.vec[j]
      lambda <- exp(llambda)

      K.inv <- solve(K.theta + lambda*diag(n), tol=1E-25)
      J <- rep(1,n)
      alpha <- sum(K.inv)^(-1)*t(J)%*%K.inv
      mu.hat <- as.numeric(alpha%*%y)
      c.hat <- K.inv%*%(y-J*mu.hat)
      H <- K.theta%*%K.inv%*%(diag(n)-J%*%alpha)+J%*%alpha

      df <- sum(diag(H))
      df.vec[j] <- df
      y.hat <- mu.hat + K.theta%*%c.hat
      res <- y-y.hat
      SSE <- sum(res^2)
      if(gcv.pen*df >= n)
        gcv <- Inf
      else
        gcv <- SSE/(1-gcv.pen*df/n)^2

      if(gcv < gcv.best && df>=df.lim[1] && df<=df.lim[2]){
        gcv.best <- gcv     
        c.best <- c.hat
        df.best <- df
        log.lambda.best <- llambda
        lambda.best <- exp(log.lambda.best)
        mu.best <- mu.hat
      }
    }

    if(gcv.best==Inf){
      df.err <- (df.vec-df.lim[1])^2+(df.vec-df.lim[2])^2
      ind.j <- order(df.err)[1]
      df.best <- df.vec[ind.j]
      log.lambda.best <- log.lambda.vec[ind.j]
      lambda.best <- exp(log.lambda.best)
    }

    diff <- exp(log.lambda.best+inc) - lambda.best
    if(diff/lambda.best <= rel.tol)
      break

   ## create log.lambda.vec for next pass
    log.lambda.min <- log.lambda.best - floor(nlambda/2)/2*inc
    log.lambda.min <- max(LAMBDAMIN, log.lambda.min)  
    log.lambda.max <- log.lambda.best + floor(nlambda/2)/2*inc
    log.lambda.max <- min(LAMBDAMAX, log.lambda.max)  
    inc <- inc/2
    log.lambda.vec <- seq(log.lambda.min, log.lambda.max, inc) 
    ind <- which.equal(log.lambda.vec, log.lambda.old)
    log.lambda.vec <- log.lambda.vec[!ind]
    log.lambda.old <- c(log.lambda.old, log.lambda.vec)
  }

 ## Now get weights w
  L2.norm <- numeric(P)
  H2.norm <- numeric(P)
  y.mat <- matrix(0,n,P)
  for(i in 1:P){
    y.mat[,i] <- w.0[i]^2*Gram[[i]]%*%c.hat
    H2.norm[i] <- sqrt(t(c.best)%*%(w.0[i]^4*Gram[[i]])%*%c.best)
    L2.norm[i] <- sqrt(mean((y.mat[,i])^2))
  }

  if(w[1]=='L2'){
    w <- L2.norm^wt.pow
  }
  else if(w[1]=='RKHS'){
    w <- H2.norm^wt.pow
  }

  return(list(lambda=lambda.best, gcv=gcv.best, df=df.best, w=w, 
              Gram=Gram, y.mat=y.mat, X=X, y=y, c.hat=c.best, mu.hat=mu.best))
}

#######################################################################
############ GET LAMBDA_0 VIA FULL SMOOTHING SPLINE ###################
#######################################################################
           
get.lambda0 <- function(X, y, order, lambda.lim, nlambda, gcv.pen, rel.tol, 
                        w, Gram, df.lim, cat.pos){

  n <- nrow(X)
  p <- ncol(X)
  if(order==1)
    P <- p
  else
    P <- p + choose(p,2)  

  if(missing(df.lim)){
    df.lim <- c(0,.5*n)
  }

  if(length(w)==1)
    w <- rep(w,P)

 ## shift and rescale x's to [0,1]
  for(i in 1:p){
    if(any( X[,i]<0 | X[,i]>1)){
      X[,i] <- (X[,i]-min(X[,i]))/(max(X[,i])-min(X[,i]))
    }
  }

 ## Get Gram Matrix
  if(missing(Gram)){
    Gram <- get.gram(X, X, order=order, cat.pos=cat.pos)
  }
  K.theta <- matrix(0,n,n)
  for(i in 1:P){
    K.theta <- K.theta + w[i]^2*Gram[[i]]
  }

  lambda.min <- lambda.lim[1]
  lambda.max <- lambda.lim[2]
  log.lambda.best <- .01
  LAMBDAMIN <- log(lambda.min)
  LAMBDAMAX <- log(lambda.max)
  log.lambda.min <- LAMBDAMIN
  log.lambda.max <- LAMBDAMAX
  inc <- (log.lambda.max - log.lambda.min)/(nlambda-1)
  log.lambda.vec <- seq(log.lambda.min, log.lambda.max, inc)
  log.lambda.old <- log.lambda.vec
  gcv.best <- Inf

  repeat{
    nlambda.now <- length(log.lambda.vec)
    df.vec <- rep(0, length(log.lambda.vec))
    for(j in 1:nlambda.now){
      llambda <- log.lambda.vec[j]
      lambda <- exp(llambda)

#K.theta..<<-K.theta
#lambda..<<-lambda

      K.inv <- solve(K.theta + lambda*diag(n), tol=1E-25)
      J <- rep(1,n)
      alpha <- sum(K.inv)^(-1)*t(J)%*%K.inv
      mu.hat <- as.numeric(alpha%*%y)
      c.hat <- K.inv%*%(y-J*mu.hat)
      H <- K.theta%*%K.inv%*%(diag(n)-J%*%alpha)+J%*%alpha

      df <- sum(diag(H))
      df.vec[j] <- df
      y.hat <- mu.hat + K.theta%*%c.hat
      res <- y-y.hat
      SSE <- sum(res^2)
      if(gcv.pen*df >= n)
        gcv <- Inf
      else
        gcv <- SSE/(1-gcv.pen*df/n)^2


#cat("\nlambda =",lambda)
#cat("    df =",df)
#cat("    gcv =",gcv)
#cat("    gcv.best =",gcv.best)
#cat("\nw =")
#print(w)

      if(gcv < gcv.best && df>=df.lim[1] && df<=df.lim[2]){
        gcv.best <- gcv     
        c.best <- c.hat
        log.lambda.best <- llambda
        lambda.best <- exp(log.lambda.best)
      }
    }

    if(gcv.best==Inf){
      df.err <- (df.vec-df.lim[1])^2+(df.vec-df.lim[2])^2
      ind.j <- order(df.err)[1]
      log.lambda.best <- log.lambda.vec[ind.j]
      lambda.best <- exp(log.lambda.best)
    }

    diff <- exp(log.lambda.best+inc) - lambda.best
#cat("\ndiff =",diff)
#cat("\nlambda.best =",lambda.best)

    if(diff/lambda.best <= rel.tol)
      break

   ## create log.lambda.vec for next pass
    log.lambda.min <- log.lambda.best - floor(nlambda/2)/2*inc
    log.lambda.min <- max(LAMBDAMIN, log.lambda.min)  
    log.lambda.max <- log.lambda.best + floor(nlambda/2)/2*inc
    log.lambda.max <- min(LAMBDAMAX, log.lambda.max)  
    inc <- inc/2
    log.lambda.vec <- seq(log.lambda.min, log.lambda.max, inc) 
    ind <- which.equal(log.lambda.vec, log.lambda.old)
    log.lambda.vec <- log.lambda.vec[!ind]
    log.lambda.old <- c(log.lambda.old, log.lambda.vec)
  }

 ## Now get norm and y.mat
  norm <- numeric(P)
  y.mat <- matrix(0,n,P)
  for(i in 1:P){
    y.mat[,i] <- w[i]^2*Gram[[i]]%*%c.hat
    norm[i] <- t(c.hat)%*%(w[i]^4*Gram[[i]])%*%c.hat
  }
  return(list(lambda=lambda.best, gcv=gcv.best, w=w, Gram=Gram, 
              y.mat=y.mat, X=X, y=y, norm=norm))
}




#######################################################################
######## GET INITIAL WEIGHTS VIA FULL SMOOTHING SPLINE ################
#######################################################################
           
get.lambda.w <- function(X, y, order, lambda.lim, nlambda, w='L2', 
                         gcv.pen, rel.tol, wt.pow, w.0, w.lim=c(1E-10, 1E10),
                         f.est='trad', rel.K, rel.lambda, rel.theta, maxit, 
                         nK, seed, cv, init.cv='gcv', cat.pos, min.distinct){

  if(f.est=='trad'){
    ans1 <- get.w(X=X, y=y, order=order, lambda.lim=lambda.lim, 
                  nlambda=nlambda, gcv.pen=gcv.pen, wt.pow=wt.pow, 
                  rel.tol=rel.tol, w=w, w.lim=w.lim, cat.pos=cat.pos)
    ans1$Gram <- NULL
    w <- ans1$w

  }

  else{ #f.est = 'cosso'
    ans1 <- venus.cv(X, y, order=order, w=1, wt.pow=0, seed=seed, K.lim='data',
                     nK=nK, gcv.pen=gcv.pen, rel.K=rel.K, nlambda=nlambda, 
                     lambda.lim=lambda.lim, rel.lambda=rel.lambda, 
                     rel.theta=rel.theta, maxit=maxit, cv=init.cv,
                     cat.pos=cat.pos, min.distinct=min.distinct)
    ans1$Gram <- NULL
    fit.venus <- venus(X, y, order=order, K=ans1$K, gcv.pen=gcv.pen, maxit=5, 
                       rel.tol=1E-2, cv='gcv', lambda.0=ans1$lambda.0, 
                       w=ans1$w, cat.pos=cat.pos, min.distinct=min.distinct)
    ans.norm <- get.venus.norms(fit.venus)

    if(w[1]=='L2'){
      w <- ans.norm$L2.norm^wt.pow
    }
    else if(w[1]=='RKHS'){
      w <- ans.norm$H2.norm^wt.pow
    }
  }

  ans2 <- get.lambda0(X=X, y=y, order=order, lambda.lim=lambda.lim, 
                      nlambda=nlambda, gcv.pen=gcv.pen, rel.tol=rel.tol, w=w,
                      cat.pos=cat.pos)
  lambda <- ans2$lambda
  norm <- ans2$norm
  y.mat <- ans2$y.mat
  w <- ans2$w

  return(list(lambda=lambda, norm=norm, X=X, y=y, Gram=ans2$Gram, y.mat=y.mat, 
              w=w))
}

#######################################################################
################### CROSS VALIDATE ON K ###############################
#######################################################################

venus.cv <- function(X, y, order=1, w='L2', K.lim='data', nK=5, gcv.pen, 
             rel.K=1E-2, nlambda=10, lambda.lim=c(1E-10, 1E2), rel.lambda=1E-2, 
             theta.0, rel.theta=1E-2, maxit=2, cv='gcv', wt.pow=1, seed=220, 
             w.lim=c(1E-12, 1E10), lambda.0='est', Gram, f.est='trad', 
             init.cv='gcv', cat.pos="auto", min.distinct=7){

  n <- nrow(X)
  p <- ncol(X)
  if(order==1)
    P <- p
  else
    P <- p + choose(p,2)  

  if(missing(theta.0))
    theta.0 <- rep(1,P)
  theta.00 <- theta.0

  ## Identify categorical vars 
  if(length(cat.pos)>0 && cat.pos[1]=='auto'){
   # scan for variables with 5 or less distinct values. 
    cat.pos <- numeric(0)
    for(i in 1:p){
      unique.i <- unique(X[,i])
      if(length(unique.i)<=min.distinct || is.character(X[,i])){
        cat.pos <- c(cat.pos, i)
      }
    }
  }
  
 ## First get lambda.0 
  if(lambda.0=='est' || missing(Gram)){
    ans.lambda0 <- get.lambda.w(X=X, y=y, order=order, lambda.lim=lambda.lim, 
                   nlambda=nlambda, w=w, gcv.pen=gcv.pen, rel.tol=rel.lambda, 
                   wt.pow=wt.pow, w.0=1, w.lim=w.lim, f.est=f.est, rel.K=rel.K,
                   rel.lambda=rel.lambda, rel.theta=rel.theta, maxit=maxit,
                   nK=nK, seed=seed, cv=cv, init.cv=init.cv, cat.pos=cat.pos,
                   min.distinct=min.distinct)
    w <- ans.lambda0$w

### Changed this for numerical stability
#    lambda.0 <- ans.lambda0$lambda*1E-3
    lambda.0 <- ans.lambda0$lambda*1E0
#######################################
    Gram <- ans.lambda0$Gram
    ans.lambda0$Gram <- NULL
    norm <- ans.lambda0$norm
  }

  if(K.lim[1]=='data'){
    K.lim <- c(0, 10*P)
  }

 ## Now conduct grid search on K
  K.min <- K.lim[1]
  K.max <- K.lim[2]
  KMIN <- log10(K.min+1)
  KMAX <- log10(K.max+1)
  log.K.min <- KMIN
  log.K.max <- KMAX

  inc <- (log.K.max - log.K.min)/(nK-1)
  log.K.vec <- seq(log.K.min, log.K.max, inc)
  log.K.old <- log.K.vec
  pen.best <- Inf

  repeat{
    nK.now <- length(log.K.vec)
    theta.0 <- theta.00
    for(j in 1:nK.now){
      K <- 10^(log.K.vec[j])-1
      fit.venus <- venus(X=X,y=y,order=order, K=K,gcv.pen=gcv.pen, 
                         lambda.0=lambda.0, theta.0=theta.0,rel.tol=rel.theta, 
                         maxit=maxit, Gram=Gram, cv=cv, w=w, seed=seed,
                         cat.pos=cat.pos, min.distinct=min.distinct)
      fit.venus$Gram <- NULL

      if(cv=='bic')
        pen <- fit.venus$bic
      else
        pen <- fit.venus$gcv

      if(pen < pen.best){
        pen.best <- pen     
        K.best <- K
        log.K.best <- log.K.vec[j]
        theta.best <- fit.venus$theta
      }
    }
    diff <- 10^(log.K.best+inc)-1 - K.best
    if(diff/(K.best+1E-6) <= rel.K)
      break

   ## create K.vec for next pass
    log.K.min <- log.K.best - floor(nK/2)/2*inc
    log.K.min <- max(KMIN, log.K.min)  
    log.K.max <- log.K.best + floor(nK/2)/2*inc
    log.K.max <- min(KMAX, log.K.max)  
    inc <- inc/2
    log.K.vec <- seq(log.K.min, log.K.max, inc) 
    ind <- which.equal(log.K.vec, log.K.old)
    log.K.vec <- log.K.vec[!ind]
    log.K.old <- c(log.K.old, log.K.vec)
  }

  return(list(K=K.best, lambda.0=lambda.0, theta=theta.best, Gram=Gram,
              pen=pen.best, w=w, cat.pos=cat.pos))
}

# ======================================================================
# ======================================================================
args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned
xfile <- args[1]       # training input
yfile <- args[2]       # training output (ground truth)
rdsfile <- args[3]     # trained model will save to R binary
order <- args[4]
cv <- args[5]
cat <- args[6]

# parse categorical vector
if(!identical(cat,'auto')) {
  s = strsplit(cat,'[^[:digit:]]')   # split string at non-digits
  s = as.numeric(unlist(s))          # convert strings to numeric ('' becomes NA)
  s = unique(s[!is.na(s)])           # remove NA and duplicates
  cat = s 
}

X = read.table(xfile, sep=',', header=TRUE)
nx = ncol(X)
X = X[,1:nx]
y = read.table(yfile, sep=',', header=TRUE)
y = y[,1]                            # assume one output 
acosso.fit <- acosso(X, y, order=order, wt.pow=1, cv=cv, categorical=cat)
saveRDS(acosso.fit, rdsfile)
