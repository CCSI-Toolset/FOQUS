import subprocess

# ---------------------------------------
# BSSANOVA fit function
# ---------------------------------------
def fit(xdatfile, ydatfile, modelfile, 
        bte='[200,1000,1]', categorical='auto', nterms='25', order='2', priorprob='0.5'):
    p = subprocess.Popen(['Rscript', 'bssanova_fit.R', xdatfile, ydatfile, modelfile, 
                          bte, categorical, nterms, order, priorprob],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
#   print stdout
#   print stderr

    return modelfile

# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = fit('xdat.csv','ydat.csv','bssanova_fit.rds')
print(rdsfile)

