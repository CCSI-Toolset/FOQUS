import subprocess

# ---------------------------------------
# SOLVENTFIT EMULATOR predict function
# ---------------------------------------
def pred(modelfile, xdatfile, yhatfile, nsamples='50', transform='1'):
    p = subprocess.Popen(['Rscript', 'solvfit_emulpred.R', modelfile, xdatfile, yhatfile,
                          nsamples, transform],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print(stdout)
    print(stderr)

    return yhatfile

# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = 'solvfit_emulator.rds'
infile = 'example/infile.emulpred'
outfile = 'outfile.emulpred'
resfile = pred(rdsfile, infile, outfile)
print(resfile)
