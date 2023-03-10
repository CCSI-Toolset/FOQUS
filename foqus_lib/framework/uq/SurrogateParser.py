#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
import os, re
import numpy as np
from .Model import Model
from .SampleData import SampleData
from .SamplingMethods import SamplingMethods
from .Distribution import Distribution


class SurrogateParser:
    @staticmethod
    def writeBssAnovaDriver(bssanovaData, outfile):

        outputNames = bssanovaData[
            "outputNames"
        ]  # list of strings indicating each output's variable name
        modelNames = bssanovaData[
            "modelNames"
        ]  # list of strings indicating path of each output's rdsfile
        rscript = bssanovaData[
            "rscriptPath"
        ]  # string indicating path to Rscript executable
        rfile = bssanovaData["rfile"]  # R script that gets written

        # write driver file
        f = open(outfile, "w")
        frontmatter = [
            "#!/usr/bin/python",
            "###################################################",
            "# Response surface interpolator from BSSANOVA",
            "# How to run this program : ",
            "#    Python program> <infile> <outfile> <aux>",
            "# where <infile> has the following format : ",
            "# line 1 : <npts> <nInputs> ",
            "# line 2 : 1 <test point 1 inputs> ",
            "# line 3 : 2 <test point 2 inputs> ",
            "# .... ",
            "# where <outfile> will be in the following format : ",
            "# line 1 : 1 <interpolated value for test point 1>",
            "# line 2 : 2 <interpolated value for test point 2>",
            "# .... ",
            "# where <aux> is an optional index (1-based) argument",
            "#    to specify which output to evaluate",
            "#==================================================",
            "import subprocess",
            #'import os',
            "import sys",
            "###################################################",
            "# Model parameters",
            "#==================================================",
        ]
        f.write("\n".join(frontmatter) + "\n")
        f.write("labels = " + "{}".format(outputNames) + "\n")
        f.write("models = " + "{}".format(modelNames) + "\n")
        f.write("nOutputs = %d\n" % len(outputNames))
        f.write("\nf = open(r'%s','w')\n" % rfile)
        code = [
            "##########################################################",
            "############### BSSANOVA Prediction ######################",
            "##########################################################",
            "",
            "predict.bssanova <- function(X.new, object, nreal=NA){",
            "",
            "###################### INPUTS ################################",
            "## X.new - a matrix of new values for the predictors",
            "## obj - a fitted acosso object",
            "## nreal - how many posterior realizations to obtain (defaults to same as fit object)",
            "##############################################################",
            "",
            "###################### OUTPUT #################################",
            "## yhat - a nrow(X.new) vector of the posterior mean of predicted outputs",
            "## yreal - a (nreal) x (nrow(X.new)) matrix:",
            "##          each row gives X predictions for a given posterior realization ",
            "## curves - a (# functional components) x (nreal) x (nrow(X.new)) array:",
            "##           e.g., curves[j,r,] provides predictions for j-th functional component",
            "##	     for the r-th posterior realization",
            "###############################################################",
            "",
            "  X.new <- as.matrix(X.new)",
            "  nx <- ncol(X.new)",
            "  if(length(dimnames(X.new)[[2]]) == 0){",
            "    dimnames(X.new)[[2]] <- list()",
            '    dimnames(X.new)[[2]] <- paste("x", 1:nx, sep="")',
            "  }",
            "  bss.model <- object$bss.model",
            "",
            "  pred.bss <- BSSANOVA.predict(bss.model, X.new, runs=bss.model$burn+nreal)",
            "  yhat <- pred.bss$pred.mn",
            "  yreal <- pred.bss$y.pred",
            "",
            "  return(list(yhat=yhat, yreal=yreal, curves=pred.bss$curves))",
            "}",
            "",
            "predict.bssanova.at.mean <- function(X.new, object){",
            "  X.new <- as.matrix(X.new)",
            "  nx <- ncol(X.new)",
            "  if(length(dimnames(X.new)[[2]]) == 0){",
            "    dimnames(X.new)[[2]] <- list()",
            '    dimnames(X.new)[[2]] <- paste("x", 1:nx, sep="")',
            "  }",
            "  bss.model <- object$bss.model",
            "",
            "  pred.bss <- BSSANOVA.predict.at.mean(bss.model, X.new)",
            "  return(pred.bss)",
            "}",
            "",
            "########################################################################",
            "########## Other Functions Used in the Creation of BSSANOVA ############",
            "########################################################################",
            "",
            "BSSANOVA.predict<-function(fit,newx,runs=NA){",
            "  x<-fit$x",
            "  xnew<-newx",
            "  main <- fit$main",
            "  twoway <- fit$twoway",
            "  categorical <- fit$categorical",
            "",
            "  all.x<-rbind(x,xnew)",
            "  if(is.na(runs) || runs>length(fit$int))",
            "    runs<-length(fit$int)",
            "",
            "  #set some sample size parameters ",
            "  n<-nrow(x)",
            "  nnew<-nrow(newx)",
            "  nterms<-fit$nterms",
            "  ncurves<-0",
            "  p<-ncol(x)",
            "",
            "  if(main){ncurves<-ncurves+p}",
            "  if(fit$twoway){ncurves<-ncurves+p*(p-1)/2}",
            "  term1<-term2<-rep(0,ncurves)",
            "",
            "  #Set up the covariance matrices for the main effects",
            "  B<-array(0,c(ncurves,nnew,nterms))  ",
            "  ",
            "  count<-1",
            "  ",
            "  #set up the covariances for the main effects",
            "  if(main){",
            "     for(j in 1:p){",
            "       term1[count]<-term2[count]<-j",
            "       if(!categorical[j]){",
            "          B[count,,]<-makeB.cont(xnew[,j],fit$theta.basis)",
            "       }",
            "       if(categorical[j]){",
            "          B[count,,]<-makeB.cat(xnew[,j],ncats=max(xnew[,j]),nterms=nterms)",
            "       }",
            "       count<-count+1",
            "     }",
            "  }",
            "",
            "  #set up the covariances for the two-way interactions",
            "  if(twoway){",
            "     for(j1 in 2:p){",
            "       for(j2 in 1:(j1-1)){",
            "         term1[count]<-j1;term2[count]<-j2",
            "         term<-1",
            "         for(k1 in 1:round(sqrt(nterms))){",
            "           for(k2 in 1:round(sqrt(nterms)+1)){",
            "             if(term<=nterms){",
            "                B[count,,term]<-B[j1,,k1]*B[j2,,k2]",
            "                term<-term+1",
            "             }",
            "           }",
            "         }",
            "         count<-count+1",
            "       }",
            "     }",
            "  }",
            "",
            "  curves<-array(0,c(ncurves,runs,nnew))",
            "  y.pred<-matrix(0,runs,nnew)",
            "  ########             Start the sampler       ###################",
            "  countiter<-0",
            "  start<-proc.time()[3]",
            "  for(i in 1:runs){",
            "      for(j in 1:ncurves){",
            "        curves[j,i,]<-fit$sigma[i]*B[j,,]%*%fit$theta[j,i,]",
            "      }",
            "      y.pred[i,]<-fit$int[i]+apply(curves[,i,,drop=F],2,sum)",
            "  }",
            "",
            "  pred.mn<-apply(y.pred[(fit$burn+1):fit$runs,,drop=F],2,mean)",
            "",
            "  list(pred.mn=pred.mn, y.pred=y.pred[(fit$burn+1):fit$runs,],",
            "       int=fit$int[(fit$burn+1):fit$runs], curves=curves[,(fit$burn+1):fit$runs,],",
            "       term1=fit$term1,term2=fit$term2)",
            "}",
            "",
            "BSSANOVA.predict.at.mean<-function(fit,newx){",
            "  x<-fit$x",
            "  xnew<-newx",
            "  main <- fit$main",
            "  twoway <- fit$twoway",
            "  categorical <- fit$categorical",
            "  all.x<-rbind(x,xnew)",
            "",
            "  #set some sample size parameters ",
            "  n<-nrow(x)",
            "  nnew<-nrow(newx)",
            "  nterms<-fit$nterms",
            "  ncurves<-0",
            "  p<-ncol(x)",
            "",
            "  if(main){ncurves<-ncurves+p}",
            "  if(fit$twoway){ncurves<-ncurves+p*(p-1)/2}",
            "  term1<-term2<-rep(0,ncurves)",
            "",
            "  #Set up the covariance matrices for the main effects",
            "  B<-array(0,c(ncurves,nnew,nterms))  ",
            "  ",
            "  count<-1",
            "  ",
            "  #set up the covariances for the main effects",
            "  if(main){",
            "     for(j in 1:p){",
            "       term1[count]<-term2[count]<-j",
            "       if(!categorical[j]){",
            "          B[count,,]<-makeB.cont(xnew[,j],fit$theta.basis)",
            "       }",
            "       if(categorical[j]){",
            "          B[count,,]<-makeB.cat(xnew[,j],ncats=max(xnew[,j]),nterms=nterms)",
            "      }",
            "     count<-count+1",
            "     }",
            "  }",
            "",
            "  #set up the covariances for the two-way interactions",
            "  if(twoway){",
            "     for(j1 in 2:p){",
            "       for(j2 in 1:(j1-1)){",
            "         term1[count]<-j1;term2[count]<-j2",
            "         term<-1",
            "         for(k1 in 1:round(sqrt(nterms))){",
            "           for(k2 in 1:round(sqrt(nterms)+1)){",
            "             if(term<=nterms){",
            "                B[count,,term]<-B[j1,,k1]*B[j2,,k2]",
            "                term<-term+1",
            "             }",
            "           }",
            "         }",
            "         count<-count+1",
            "       }",
            "     }",
            "  }",
            "",
            "  curves<-array(0,c(ncurves,nnew))",
            "  countiter<-0",
            "  start<-proc.time()[3]",
            "  for(j in 1:ncurves){",
            "    curves[j,]<-mean(fit$sigma)*B[j,,]%*%apply(fit$theta[j,,],2,mean)",
            "  }",
            "  y.pred<-mean(fit$int)+apply(curves,2,sum)",
            "  return(y.pred)",
            "}",
            "",
            "makeB.cat<-function(x.pred,ncats,nterms){",
            "  xxx<-1:ncats",
            "  sss<-matrix(xxx,ncats,ncats,byrow=T)",
            "  ttt<-matrix(xxx,ncats,ncats,byrow=F)",
            "  equals<-ifelse(sss==ttt,1,0)",
            "  COV<-(ncats-1)*equals/ncats -(1-equals)/ncats",
            "  COV<-COV/mean(diag(COV))",
            "  eig<-eigen(COV);",
            "  Gamma<-eig$vectors%*%diag(sqrt(abs(eig$values)))",
            "  B<-matrix(0,length(x.pred),nterms)",
            "  for(j in 1:(ncats-1)){",
            "     dat<-list(y=Gamma[,j],x=xxx)",
            "     pred.dat<-list(x=x.pred)",
            "     fit<-lm(y~as.factor(x),data=dat)",
            "     B[,j]<-predict(fit,newdata=pred.dat)",
            "  }",
            "B}  ",
            "",
            "make.basis.bosco<-function(x,n.knots){",
            "   B<-matrix(1,length(x),n.knots)",
            "   knots<-seq(0,1,length=n.knots-2)[-(n.knots-2)]",
            "   B[,2]<-x",
            "   B[,3]<-x*x",
            "   for(j in 1:length(knots)){",
            "      B[,j+3]<-ifelse(x>knots[j],(x-knots[j])^3,0)",
            "   }",
            "B}",
            "",
            "makeB.cont<-function(x.pred,theta){",
            "  X<-make.basis.bosco(x.pred,nrow(theta))",
            "X%*%theta}",
            "",
            "# ======================================================================",
            "# ======================================================================",
            "args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned",
            "rdsfile <- args[1]   # rds file containing model",
            "infile <- args[2]    # test data containing inputs",
            "outfile <- args[3]   # test data containing predicted outputs",
            "",
            "X.new = read.table(infile, header=FALSE, skip=1)  # skip first line",
            "nx = ncol(X.new)",
            "X.new = X.new[,2:nx] # ignore row names",
            "bssanova.fit = readRDS(rdsfile)",
            "bssanova.pred <- predict.bssanova(X.new, bssanova.fit)",
            "bssanova.yhat <- bssanova.pred$yhat",
        ]
        f.write("f.write('" + "\\n')\nf.write('".join(code) + "')\n")
        f.write(
            "f.write('\\nwrite.table(bssanova.yhat, file=outfile, sep=\\' \\', row.names=TRUE, col.names=FALSE, quote=FALSE)\\n')\n"
        )
        f.write("f.close()\n\n")
        backmatter = [
            "###################################################",
            "# main program",
            "#==================================================",
            "infileName  = sys.argv[1]",
            "outfileName = sys.argv[2]",
            "index = 0",
            "if len(sys.argv) > 3:",
            "   y = sys.argv[3]",
            "   if y.isdigit():",
            "      y = int(y)",
            "      if y in range(1, nOutputs+1):",
            "         index = y - 1",
            "   else:",
            "      if y in labels:",
            "         index = labels.index(y)",
        ]
        f.write("\n".join(backmatter) + "\n")
        f.write(
            "rdsfile = models[index]\n"
        )  # pass in the appropriate model file specific to that output
        f.write(
            "p = subprocess.Popen([r'%s', r'%s', rdsfile, infileName, outfileName], \n"
            % (rscript, rfile)
        )
        f.write(
            "                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n"
        )
        f.write("stdout, stderr = p.communicate()\n")
        f.write("if stdout:\n")
        f.write("   print(stdout)\n")
        f.write("if stderr:\n")
        f.write("   print(stderr)\n")
        # f.write("os.remove('%s')\n" % rfile)  # os required only to remove R script
        f.close()

        return outfile

    @staticmethod
    def writeAcossoDriver(acossoData, outfile):

        outputNames = acossoData[
            "outputNames"
        ]  # list of strings indicating each output's variable name
        modelNames = acossoData[
            "modelNames"
        ]  # list of strings indicating path of each output's rdsfile
        rscript = acossoData[
            "rscriptPath"
        ]  # string indicating path to Rscript executable
        rfile = acossoData["rfile"]  # R script that gets written

        # write driver file
        f = open(outfile, "w")
        frontmatter = [
            "#!/usr/bin/python",
            "###################################################",
            "# Response surface interpolator from ACOSSO",
            "# How to run this program : ",
            "#    Python program> <infile> <outfile> <aux>",
            "# where <infile> has the following format : ",
            "# line 1 : <npts> <nInputs> ",
            "# line 2 : 1 <test point 1 inputs> ",
            "# line 3 : 2 <test point 2 inputs> ",
            "# .... ",
            "# where <outfile> will be in the following format : ",
            "# line 1 : 1 <interpolated value for test point 1>",
            "# line 2 : 2 <interpolated value for test point 2>",
            "# .... ",
            "# where <aux> is an optional index (1-based) argument",
            "#    to specify which output to evaluate",
            "#==================================================",
            "import subprocess",
            #'import os',
            "import sys",
            "###################################################",
            "# Model parameters",
            "#==================================================",
        ]
        f.write("\n".join(frontmatter) + "\n")
        f.write("labels = " + "{}".format(outputNames) + "\n")
        f.write("models = " + "{}".format(modelNames) + "\n")
        f.write("nOutputs = %d\n" % len(outputNames))
        f.write("\nf = open(r'%s','w')\n" % rfile)
        code = [
            "##########################################################",
            "############### ACOSSO Prediction ########################",
            "##########################################################",
            "",
            "predict.acosso <- function(X.new, obj){",
            "",
            "###################### INPUTS ################################",
            "## X.new - a matrix of new values for the predictors",
            "## obj - a fitted acosso object",
            "##############################################################",
            "",
            "###################### OUTPUT #################################",
            "## a vector of the predicted outputs",
            "###############################################################",
            "",
            "  return(predict.venus(X.new, obj, order=obj$order))",
            "}",
            "",
            "##############################################################################",
            "############# Other Functions Used in the Creation of ACOSSO #################",
            "##############################################################################",
            "",
            "index <- function(m,n){",
            "  if(m<=n) return(m:n)",
            "  else return(numeric(0))",
            "}",
            "",
            "################################",
            "##### Sobolev RK function ######",
            "################################",
            "",
            "k1 <- function(t){",
            "  return(t-.5)",
            "}",
            "k2 <- function(t){",
            "  return( (k1(t)^2-1/12)/2 )",
            "}",
            "k4 <- function(t){",
            "  return( (k1(t)^4-k1(t)^2/2+7/240)/24 )",
            "}",
            "K.sob <- function(s,t){",
            "  ans <- k1(s)*k1(t) + k2(s)*k2(t) - k4(abs(s-t))",
            "  return(ans)",
            "}",
            "K.cat <- function(s,t,G){",
            "  ans <- (G-1)/G*(s==t) - 1/G*(s!=t) ",
            "  return(ans)",
            "}",
            "",
            "#######################################################################",
            "############# Predict new obs for Venus ###############################",
            "#######################################################################",
            "",
            "predict.venus <- function(X.new, obj, order=1){",
            "",
            "  theta <- obj$theta",
            "  w <- obj$w",
            "  c.hat <- obj$c.hat",
            "  mu.hat <- obj$mu.hat",
            "  X <- obj$X",
            "  X.orig <- obj$X.orig",
            "  p <- ncol(X)",
            "  rescale <- obj$rescale",
            "  cat.pos <- obj$cat.pos",
            "",
            " ## shift and rescale inputs to [0,1]",
            "  for(i in (1:p)[rescale])",
            "    X.new[,i] <- (X.new[,i]-min(X.orig[,i]))/(max(X.orig[,i])-min(X.orig[,i]))*.9 + .05",
            "",
            " ## Get Gram Matrix & predict y",
            "  Gram.mat <- get.gram.predict(X.new, X, order, theta, w, cat.pos=cat.pos)",
            "  y.hat <- as.vector(Gram.mat%*%c.hat + mu.hat)",
            "  return(y.hat)",
            "}",
            "",
            "#########################################################################",
            "######### Creates a single Gram matrix for Prediction of new obs ########",
            "#########################################################################",
            "",
            "get.gram.predict <- function(X1, X2, order, theta, w, cat.pos){",
            "",
            "  n1 <- nrow(X1)",
            "  n2 <- nrow(X2)",
            "  p <- ncol(X1)",
            "  gram.mat <- matrix(0, n1, n2)",
            "  gram <- list()",
            "  if(length(cat.pos)>0)",
            "    cont.pos <- (1:p)[-cat.pos]",
            "  else",
            "    cont.pos <- (1:p)",
            "",
            "  for(i in cont.pos){",
            "    x1 <- rep(X1[,i], times=n2)",
            "    x2 <- rep(X2[,i], each=n1)",
            "    ans <- K.sob(x1,x2)",
            "    gram[[i]] <- matrix(ans, n1, n2)",
            "    if(theta[i] > 1E-6)",
            "      gram.mat <- gram.mat + theta[i]*w[i]^2*gram[[i]]",
            "  }",
            "  for(i in cat.pos){",
            "    x1 <- rep(X1[,i], times=n2)",
            "    x2 <- rep(X2[,i], each=n1)",
            "    G <- length(unique(x1))",
            "    ans <- K.cat(x1,x2,G)",
            "    gram[[i]] <- matrix(ans, n1, n2)",
            "    if(theta[i] > 1E-6)",
            "      gram.mat <- gram.mat + theta[i]*w[i]^2*gram[[i]]",
            "  }",
            "  if(order==2){",
            "    next.ind <- p+1",
            "    for(i in index(1,p-1)){",
            "      for(j in index(i+1,p)){",
            "        if(theta[next.ind] > 1E-6)",
            "          gram.mat <-gram.mat+theta[next.ind]*w[next.ind]^2*gram[[i]]*gram[[j]]",
            "        next.ind <- next.ind+1",
            "      }",
            "    }",
            "  }",
            "  return(gram.mat)",
            "}",
            "",
            "# ======================================================================",
            "# ======================================================================",
            "args <- commandArgs(trailingOnly=TRUE)  # only arguments are returned",
            "rdsfile <- args[1]   # rds file containing model",
            "infile <- args[2]    # test data containing inputs",
            "outfile <- args[3]   # test data containing predicted outputs",
            "",
            "X.new = read.table(infile, header=FALSE, skip=1)  # skip first line",
            "nx = ncol(X.new)",
            "X.new = X.new[,2:nx] # ignore row names",
            "acosso.fit = readRDS(rdsfile)",
            "acosso.pred <- predict.acosso(X.new, acosso.fit)",
        ]
        f.write("f.write('" + "\\n')\nf.write('".join(code) + "')\n")
        f.write(
            "f.write('\\nwrite.table(acosso.pred, file=outfile, sep=\\' \\', row.names=TRUE, col.names=FALSE, quote=FALSE)\\n')\n"
        )
        f.write("f.close()\n\n")
        backmatter = [
            "###################################################",
            "# main program",
            "#==================================================",
            "infileName  = sys.argv[1]",
            "outfileName = sys.argv[2]",
            "index = 0",
            "if len(sys.argv) > 3:",
            "   y = sys.argv[3]",
            "   if y.isdigit():",
            "      y = int(y)",
            "      if y in range(1, nOutputs+1):",
            "         index = y - 1",
            "   else:",
            "      if y in labels:",
            "         index = labels.index(y)",
        ]
        f.write("\n".join(backmatter) + "\n")
        f.write(
            "rdsfile = models[index]\n"
        )  # pass in the appropriate model file specific to that output
        f.write(
            "p = subprocess.Popen([r'%s', r'%s', rdsfile, infileName, outfileName], \n"
            % (rscript, rfile)
        )
        f.write(
            "                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n"
        )
        f.write("stdout, stderr = p.communicate()\n")
        f.write("if stdout:\n")
        f.write("   print(stdout)\n")
        f.write("if stderr:\n")
        f.write("   print(stderr)\n")
        # f.write("os.remove('%s')\n" % rfile)  # os required only to remove R script
        f.close()

        return outfile

    @staticmethod
    def writeIRevealDriver(irData, outfile):

        # open driver file
        f = open(outfile, "w")
        frontmatter = [
            "#!/usr/bin/python",
            "###################################################",
            "# Response surface interpolator from iReveal",
            "# How to run this program : ",
            "#    python <this program> <infile> <outfile> <aux>",
            "# where <infile> has the following format : ",
            "# line 1 : <npts> <nInputs> ",
            "# line 2 : 1 <test point 1 inputs> ",
            "# line 3 : 2 <test point 2 inputs> ",
            "# .... ",
            "# where <outfile> will be in the following format : ",
            "# line 1 : 1 <interpolated value for test point 1>",
            "# line 2 : 2 <interpolated value for test point 2>",
            "# .... ",
            "# where <aux> is an optional index (1-based) argument",
            "#    to specify which output to evaluate",
            "#==================================================",
            "import sys",
            "import string",
            "import math",
            "###################################################",
            "# Function to get input data for interpolation",
            "#==================================================",
            "def getInputData(inFileName):",
            "   inFile  = open(inFileName, 'r')",
            "   lineIn  = inFile.readline()",
            "   nCols   = lineIn.split()",
            "   nSamp   = eval(nCols[0])",
            "   nInputs = eval(nCols[1])",
            "   inData  = (nSamp * nInputs) * [0]",
            "   for cnt in range(nSamp):",
            "      lineIn = inFile.readline()",
            "      nCols  = lineIn.split()",
            "      for ind in range(nInputs):",
            "         inData[cnt*nInputs+ind] = eval(nCols[ind+1])",
            "   inFile.close()",
            "   return nSamp, inData",
            "###################################################",
            "# Function to generate output file",
            "#==================================================",
            "def genOutputFile(outFileName, outData):",
            "   nLeng = len(outData)",
            "   outfile = open(outFileName, 'w')",
            "   for ind in range(nLeng):",
            '      outfile.write("%d " % (ind+1))',
            '      outfile.write("%e\\n" % outData[ind])',
            "   outfile.close()",
            "   return None",
            "###################################################",
            "# Model parameters",
            "#==================================================",
        ]
        f.write("\n".join(frontmatter) + "\n")
        outputNames = irData["ylabels"]
        f.write("labels = " + "{}".format(outputNames) + "\n")
        f.write("nInputs = %d\n" % irData["nx"])
        f.write("nOutputs = %d\n" % irData["ny"])
        f.write("iregression = %d\n" % irData["iregression"])
        f.write("icorrelation = %d\n" % irData["icorrelation"])
        f.write("nTrains = %d\n" % irData["nds"])
        f.write("Thetas = %s\n" % SurrogateParser.mat2str(irData["theta"]))
        xstats = [irData["xmean"], irData["xstd"]]
        f.write("XStats = %s\n" % SurrogateParser.mat2str(xstats))
        ystats = [irData["ymean"], irData["ystd"]]
        f.write("YStats = %s\n" % SurrogateParser.mat2str(ystats))
        f.write("TrainInputs = %s\n" % SurrogateParser.mat2str(irData["xdat"]))
        f.write("Betas = %s\n" % SurrogateParser.mat2str(irData["beta"]))
        f.write("Gammas = %s\n" % SurrogateParser.mat2str(irData["gamma"]))

        backmatter = [
            "###################################################",
            "# Interpolate function for iReveal",
            "#==================================================",
            "def interpolate(npts, XX, oid):",
            "   Ys = npts * [0.0]",
            "   for ss in range(npts) :",
            "      Xt = nInputs * [0.0]",
            "      for ii in range(nInputs):",
            "         Xt[ii] = (XX[ss*nInputs+ii]-XStats[0][ii])/XStats[1][ii]",
            "      ## compute the regression contributions ==> accum",
            "      accum = Betas[0][oid];",
            "      if (iregression >= 1):",
            "         for ii in range(nInputs):",
            "            accum = accum + Betas[ii+1][oid] * Xt[ii]",
            "      if (iregression == 2):",
            "         kk = nInputs + 1",
            "         for ii in range(nInputs):",
            "            for ii2 in range(nInputs-ii):",
            "               accum = accum + Betas[kk][oid]*Xt[ii]*Xt[ii2+ii]",
            "               kk = kk + 1",
            "      ## compute the correlation contributions",
            "      for jj in range(nTrains) :",
            "         sig = 1",
            "         for ii in range(nInputs):",
            "            dx = Xt[ii] - TrainInputs[jj][ii]",
            "            if (dx < 0):",
            "               dx  = - dx",
            "            if (icorrelation == 0):",
            "               sig = sig * math.exp(-Thetas[oid][ii]*dx*dx)",
            "            elif (icorrelation == 1):",
            "               sig = sig * math.exp(-Thetas[oid][ii]*dx)",
            "            elif (icorrelation == 2):",
            "               tmp = 1 - Thetas[oid][ii] * dx",
            "               if (tmp < 0):",
            "                  tmp = 0.0",
            "               sig = sig * tmp",
            "            elif (icorrelation == 3):",
            "               tmp = Thetas[oid][ii] * dx",
            "               if (tmp >= 1):",
            "                  tmp = 1",
            "               sig = sig * (1 - 1.5*tmp + 0.5*tmp*tmp*tmp)",
            "            elif (icorrelation == 4):",
            "               tmp = Thetas[oid][ii] * dx",
            "               if (tmp >= 1):",
            "                  tmp = 1",
            "               sig = sig * (1-3*tmp*tmp + 2*tmp*tmp*tmp)",
            "            elif (icorrelation == 5):",
            "               tmp = Thetas[oid][ii] * dx",
            "               if (tmp < 0):",
            "                  tmp = 0",
            "               if (tmp<=0.2):",
            "                  sig = sig * (1 -15*tmp*tmp + 30*tmp*tmp*tmp)",
            "               elif (tmp<1):  ",
            "                  tmp = 1 - tmp",
            "                  sig = sig * 1.25*tmp*tmp*tmp",
            "               else:",
            "                  sig = 0",
            "         if (sig < 1.0e-16) : ",
            "            sig = 0",
            "         accum = accum + Gammas[jj][oid] * sig",
            "      ## final scaling",
            "      Ys[ss] = accum * YStats[1][oid] + YStats[0][oid]",
            "   return Ys",
            "###################################################",
            "# Main program",
            "#==================================================",
            "infileName  = sys.argv[1]",
            "outfileName = sys.argv[2]",
            "index = 0",
            "if len(sys.argv) > 3:",
            "   y = sys.argv[3]",
            "   if y.isdigit():",
            "      y = int(y)",
            "      if y in range(1, nOutputs+1):",
            "         index = y - 1",
            "   else:",
            "      if y in labels:",
            "         index = labels.index(y)",
            "(nSamples, inputVectors) = getInputData(infileName)",
            "result = interpolate(nSamples, inputVectors, index)",
            "genOutputFile(outfileName, result)",
        ]
        f.write("\n".join(backmatter) + "\n")
        f.close()

        return outfile

    @staticmethod
    def mat2str(A):
        S = []
        for a in A:
            ss = ["{: .16e}".format(s) for s in a]
            S.append(", ".join(ss))
        SS = ["[" + s + "]" for s in S]

        return "[\n" + ",\n".join(SS) + "\n]"

    @staticmethod
    def addIRevealOutputs(irData, ylabels):
        irData["ylabels"] = ylabels
        return irData

    @staticmethod
    def parseIReveal(fname):
        f = open(fname, "r")
        line = f.readline()
        while not line.startswith("//Kriging regression data"):
            line = f.readline()
        line = f.readline()  # nx
        strs = line.split()
        nx = int(strs[0])
        line = f.readline()  # ny
        strs = line.split()
        ny = int(strs[0])
        line = f.readline()  # iregression
        strs = line.split()
        iregression = int(strs[0])
        line = f.readline()  # icorrelation
        strs = line.split()
        icorrelation = int(strs[0])
        line = f.readline()  # nds
        strs = line.split()
        nds = int(strs[0])
        line = f.readline()  # skip comment
        theta = []  # theta
        line = f.readline()
        for i in range(nx):
            strs = line.split()
            theta.append([float(s) for s in strs])
        line = f.readline()  # skip comment
        line = f.readline()  # mean of input vector
        strs = line.split()
        xmean = [float(s) for s in strs]
        line = f.readline()  # skip comment
        line = f.readline()  # mean of output vector
        strs = line.split()
        ymean = [float(s) for s in strs]
        line = f.readline()  # skip comment
        line = f.readline()  # sigma of input vector
        strs = line.split()
        xstd = [float(s) for s in strs]
        line = f.readline()  # skip comment
        line = f.readline()  # sigma of output vector
        strs = line.split()
        ystd = [float(s) for s in strs]
        line = f.readline()  # skip comment
        xdat = []  # input training data
        for i in range(nds):
            line = f.readline()
            strs = line.split()
            xdat.append([float(s) for s in strs])
        line = f.readline()  # skip comment
        if iregression == 0:  # calculate nf
            nf = 1
        elif iregression == 1:
            nf = nx + 1
        else:
            nf = (nx + 1) * (nx + 2) / 2
        beta = []  # beta matrix
        for i in range(nf):
            line = f.readline()
            strs = line.split()
            beta.append([float(s) for s in strs])
        line = f.readline()  # skip comment
        gamma = []  # gamma matrix
        for i in range(nds):
            line = f.readline()
            strs = line.split()
            gamma.append([float(s) for s in strs])

        return {
            "nx": nx,
            "ny": ny,
            "iregression": iregression,
            "icorrelation": icorrelation,
            "nds": nds,
            "theta": theta,
            "xmean": xmean,
            "ymean": ymean,
            "xstd": xstd,
            "ystd": ystd,
            "xdat": xdat,
            "beta": beta,
            "gamma": gamma,
        }

    @staticmethod
    def writeAlamoDriver(alamoData, outfile, ii, oi, inputNames, outputNames):

        # extract variable names and surrogate equations
        nInputs = len(inputNames)
        nOutputs = len(outputNames)
        alamoInputNames = alamoData["inputNames"]
        alamoOutputNames = alamoData["outputNames"]
        eqns = alamoData["outputEqns"]

        indexes = [0] * len(alamoOutputNames)
        in_indexes = [0] * len(alamoInputNames)
        for i, n in enumerate(alamoInputNames):
            in_indexes[i] = ii[n]
        for i, n in enumerate(alamoOutputNames):
            indexes[i] = oi[n]

        # rewrite output equations
        eqns_new = []
        for e in eqns:
            # replace output name
            e = re.sub(r".* = (.*)", r"g = lambda X: \1", e)
            # replace input names
            inputNames_ = [x for x in enumerate(alamoInputNames)]
            # ... sort from longest string to shortest string
            # ... otherwise, bad string substitution will occur if some input names are substrings of one another
            inputNames_.sort(key=lambda x: len(x[1]), reverse=True)
            for x in inputNames_:
                xlabel = "X[{0}]".format(in_indexes[x[0]])
                e = e.replace(x[1], xlabel)

            # replace operators
            e = e.replace("log(", "math.log(")
            e = e.replace("exp(", "math.exp(")
            e = e.replace("sin(", "math.sin(")
            e = e.replace("cos(", "math.cos(")
            # ... X**p
            e = re.sub(r"(X\d*)\*{2}(\d*\.\d*)", r"math.pow(\1,\2)", e)
            # ... (X1*X2)**p
            e = re.sub(r"(\(X\d*\*X\d*)\)\*{2}(\d*\.\d*)", r"math.pow(\1,\2)", e)
            # ... (X1*X2*X3)**p
            e = re.sub(r"(\(X\d*\*X\d*\*X\d*)\)\*{2}(\d*\.\d*)", r"math.pow(\1,\2)", e)
            # ... (X1/X2)**p
            e = re.sub(r"(\(X\d*\/X\d*)\)\*{2}(\d*\.\d*)", r"math.pow(\1,\2)", e)
            eqns_new.append(e)

        # write driver file
        frontmatter = [
            "#!/usr/bin/python",
            "###################################################",
            "# Response surface interpolator from ALAMO",
            "# How to run this program : ",
            "#    python <this program> <infile> <outfile> <aux>",
            "# where <infile> has the following format : ",
            "# line 1 : <npts> <nInputs> ",
            "# line 2 : 1 <test point 1 inputs> ",
            "# line 3 : 2 <test point 2 inputs> ",
            "# .... ",
            "# where <outfile> will be in the following format : ",
            "# line 1 : 1 <interpolated value for test point 1>",
            "# line 2 : 2 <interpolated value for test point 2>",
            "# .... ",
            "# where <aux> is an optional index (1-based) argument",
            "#    to specify which output to evaluate",
            "#==================================================",
            "import sys",
            "import string",
            "import math",
            "import json",
            "###################################################",
            "# Function to get input data for interpolation",
            "#==================================================",
            "def getInputData(inFileName):",
            '   with open(inFileName, "r") as inFile:',
            "      lineIn  = inFile.readline()",
            "      nCols   = lineIn.split()",
            "      nSamp   = int(float(nCols[0]))",
            "      nInputs = int(float(nCols[1]))",
            "      inData  = (nSamp * nInputs) * [0]",
            "      for cnt in range(nSamp):",
            "         lineIn = inFile.readline()",
            "         nCols  = lineIn.split()",
            "         for ind in range(nInputs):",
            "            inData[cnt*nInputs+ind] = float(nCols[ind+1])",
            "   return nSamp, inData, nInputs",
            "###################################################",
            "# Function to generate output file",
            "#==================================================",
            "def genOutputFile(outFileName, outData):",
            "   nLeng = len(outData)",
            "   outfile = open(outFileName, 'w')",
            "   for ind in range(nLeng):",
            '      outfile.write("%d " % (ind+1))',
            '      outfile.write("%e\\n" % outData[ind])',
            "   outfile.close()",
            "   return None",
            "###################################################",
            "# Model parameters",
            "#==================================================",
        ]
        with open(outfile, "w") as f:
            f.write("\n".join(frontmatter) + "\n")
            f.write("in_labels = {}\n".format(inputNames))
            f.write("labels = {}\n".format(outputNames))
            f.write("in_indexes = {}\n".format(in_indexes))
            f.write("indexes = {}\n".format(indexes))
            f.write("nInputs = %d\n" % nInputs)
            f.write("nOutputs = %d\n" % nOutputs)
            f.write("###################################################\n")
            f.write("# Interpolate function for ALAMO\n")
            f.write("#==================================================\n")
            f.write("def interpolate(npts, XX, oid):\n")
            for iy in range(nOutputs):
                f.write("   if oid == %d:\n" % iy)
                f.write("      %s\n" % eqns_new[iy])
            f.write("   Ys = npts * [0.0]\n")
            f.write("   for ss in range(npts):\n")
            f.write("      Xt = nInputs * [0.0]\n")
            f.write("      for ii in range(nInputs):\n")
            f.write("         Xt[ii] = XX[ss*nInputs+ii]\n")
            f.write("      Ys[ss] = g(Xt)\n")
            f.write("   return Ys\n")
            backmatter = [
                "###################################################",
                "# Main program",
                "#==================================================",
                "infileName  = sys.argv[1]",
                'if infileName=="__labels__":',
                "   sys.exit(0)",
                "outfileName = sys.argv[2]",
                "index = 0",
                "if len(sys.argv) > 3:",
                "   y = sys.argv[3]",
                "   if y.isdigit():",
                "      y = int(y)",
                "      if y in range(1, nOutputs+1):",
                "         index = y - 1",
                "   else:",
                "      if y in labels:",
                "         index = labels.index(y)",
                "(nSamples, inputVectors, nInputs) = getInputData(infileName)",
                "result = interpolate(nSamples, inputVectors, index)",
                "genOutputFile(outfileName, result)",
            ]
            f.write("\n".join(backmatter) + "\n")
        return outfile

    @staticmethod
    def parseAlamo(fname):

        # read output file
        with open(fname, "rU") as f:
            lines = f.read()

        # numSamples
        pat = "%s\s*=\s*(.*?)\n" % "NDATA"
        numSamples = SurrogateParser.grabfirst(lines, pat)
        numSamples = int(numSamples[0])

        # numInputs
        pat = "%s\s*=\s*(.*?)\n" % "NINPUTS"
        numInputs = SurrogateParser.grabfirst(lines, pat)
        numInputs = int(numInputs[0])

        # numOutputs
        pat = "%s\s*=\s*(.*?)\n" % "NOUTPUTS"
        numOutputs = SurrogateParser.grabfirst(lines, pat)
        numOutputs = int(numOutputs[0])

        # inputNames
        inputInfo = SurrogateParser.grabnext(lines, "XLABELS", numInputs)
        inputNames = []
        inputMins = []
        inputMaxs = []
        for e in inputInfo:
            x = e.split()
            inputNames.append(x[0].strip())
            inputMins.append(float(x[1]))
            inputMaxs.append(float(x[2]))

        # outputNames
        outputInfo = SurrogateParser.grabnext(lines, "ZLABELS", numOutputs)
        outputNames = []
        for e in outputInfo:
            x = e.split()
            outputNames.append(x[0].strip())

        # initial data
        inputData = []
        outputData = []
        pat = "XDATA and ZDATA\s*?(.*?)\n\n"
        data = SurrogateParser.grabfirst(lines, pat)
        if data is not None:
            ncols = numInputs + numOutputs
            data = np.reshape(data, [numSamples, ncols])
            inputData = data[:, range(numInputs)]
            outputData = data[:, range(numInputs, ncols)]

        # observed data
        numSamples_obs = 0
        inputData_obs = []
        outputData_obs = []
        pat = "Errors on observed data points \(.*\):\s*?(.*?)\n\n"
        data = SurrogateParser.grabfirst(lines, pat)
        if data is not None:
            # ... x, z, zmodel, errors
            ncols = numInputs + 2 * numOutputs + numOutputs
            numSamples_obs = len(data) / ncols
            data = np.reshape(data, [numSamples_obs, ncols])
            inputData_obs = data[:, range(numInputs)]
            outputData_obs = data[:, range(numInputs, numInputs + numOutputs)]

        # outputEqns
        outputEqns = []
        for y in outputNames:
            pat = "\s%s\s*=(.*?)\n" % y
            eqn = SurrogateParser.grablast(lines, pat)
            if eqn is not None:
                e = "%s = %s" % (y, eqn.strip())
                outputEqns.append(e)

        return {
            "numInputs": numInputs,
            "numOutputs": numOutputs,
            "inputNames": inputNames,
            "inputMins": inputMins,
            "inputMaxs": inputMaxs,
            "outputNames": outputNames,
            "numSamples": numSamples,
            "inputData": inputData,
            "outputData": outputData,
            "numSamples_obs": numSamples_obs,
            "inputData_obs": inputData_obs,
            "outputData_obs": outputData_obs,
            "outputEqns": outputEqns,
        }

    @staticmethod
    def alamo2ensemble(infile):
        inData = SurrogateParser.parseAlamo(infile)
        model = Model()
        model.setName(infile)
        model.setInputNames(inData["inputNames"])
        model.setOutputNames(inData["outputNames"])
        print(model.getNumInputs())
        model.setInputTypes([Model.VARIABLE] * model.getNumInputs())
        print(model.getInputTypes())
        model.setInputMins(inData["inputMins"])
        model.setInputMaxs(inData["inputMaxs"])
        model.setSelectedOutputs(range(model.getNumOutputs()))

        data = SampleData(model)
        data.setNumSamples(inData["numSamples"])
        data.setSampleMethod(SamplingMethods.MC)
        data.setInputData(inData["inputData"])
        data.setOutputData(inData["outputData"])
        data.setRunState([True] * inData["numSamples"])

        return data

    @staticmethod
    def grabfirst(lines, pat):

        regex = re.findall(pat, lines, re.DOTALL)
        # process only the first match
        if regex:
            i = 0
            tokens = regex[i].split()
            dat = [float(s) for s in tokens]
            return dat

        return None

    @staticmethod
    def grablast(lines, pat):

        regex = re.findall(pat, lines, re.DOTALL)

        # return last match
        if regex:
            return regex[-1]

        return None

    @staticmethod
    def grep(lines, datvar):

        n = 0
        for l in lines:
            n += 1
            if datvar in l:
                return n

        return None

    @staticmethod
    def grabnext(lines, datvar, N):

        lines = lines.split("\n")
        M = SurrogateParser.grep(lines, datvar)

        if M is None:
            return None

        return lines[M : M + N]
