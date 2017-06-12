library(MASS)

##########################
### Generate some data ###
##########################
set.seed(22)

f <- function(X){
  ans <- 7*X[,1] + 15*X[,2] + 10*sin(4*pi*(X[,1]-.5)*(X[,2]-.5))
  return(ans)
}

n <- 200
p <- 4
sigma <- 1
X <- matrix(runif(n*p),n,p)
y <- f(X)+rnorm(n,0,sigma)
write.table(X,file='xdat.csv',sep=',',row.names=FALSE,col.names=c('X1','X2','X3','X4'))
write.table(y,file='ydat.csv',sep=',',row.names=FALSE,col.names=c('Y'))
