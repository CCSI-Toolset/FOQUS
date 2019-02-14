import subprocess

# ---------------------------------------
# SOLVENTFIT EMULATOR fit function
# ---------------------------------------
def fit(xdatfile, ydatfile, modelfile,
        bte='[0,1000,1]', nterms='25', order='2'):
    p = subprocess.Popen(['Rscript', 'solvfit_emulfit.R', xdatfile, ydatfile, modelfile,
                          bte, nterms, order],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print(stdout)
    print(stderr)

    return modelfile

# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = fit('example/xdat.csv','example/ydat.csv','solvfit_emulator.rds')
print(rdsfile)
