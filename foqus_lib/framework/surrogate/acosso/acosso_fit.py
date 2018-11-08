import subprocess

# ---------------------------------------
# ACOSSO fit function
# ---------------------------------------
def fit(rscriptPath, xdatfile, ydatfile, modelfile, order='2', cv='bic', categorical='auto'):
    
    p = subprocess.Popen([rscriptPath, 'acosso_fit.R', xdatfile, ydatfile, modelfile, order, cv, categorical], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
#   print stdout
#   print stderr

    return modelfile

# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = fit('C:\\Program Files\\R\\R-3.1.2\\bin\\x64\\Rscript.exe','xdat.csv','ydat.csv','acosso_fit.rds')
#rdsfile = fit('xdat.csv','ydat.csv','acosso_fit.rds',categorical='[1,2]')
print(rdsfile)
