import subprocess

# ---------------------------------------
# SOLVENTFIT CALIBRATION predict function
# ---------------------------------------
def pred(modelfile, xdatfile, yhatfile, disc=True, nsamples='100', transform='1'):
    booldict = {True:'1', False:'0'}
    disc = booldict[disc]

    emul = '1'      # if emul is set to False, then extra arguments are required
    p = subprocess.Popen(['Rscript', 'solvfit_calibpred.R', modelfile, xdatfile, yhatfile, disc,
                          nsamples, transform, emul],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()
    print(stdout)
    print(stderr)

    return yhatfile

# ---------------------------------------
# Example usage
# ---------------------------------------
rdsfile = 'solvfit_calibrator.rds'
infile = 'example/infile.calibpred'
outfile = 'outfile.calibpred'
resfile = pred(rdsfile, infile, outfile, disc=True)
print(resfile)
