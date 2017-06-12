from SurrogateParser import SurrogateParser as S

testAcosso = True
testIReveal = False
testAlamo = False

if testAcosso:
    fname = '/g/g19/ng30/ts6/foqus/foqus_lib/framework/surrogate/acosso/acosso_fit.rds'
    acossoData = {'outputNames': ['Y'],
                  'modelNames': [fname],
                  'rscriptPath': 'Rscript'}

    outfile = 'acosso_regression.py'
    acDriver = S.writeAcossoDriver(acossoData, outfile)
    print '................................................'
    print 'Executable has been written to %s.' % acDriver
    print '................................................'

if testIReveal:
    fname = '/g/g19/ng30/ts6/foqus/foqus_lib/framework/surrogate/iREVEAL/pyKriging/CapeOpen.rom'
    irData = S.parseIReveal(fname)
    print '................................................'
    print 'Data extracted from %s:\n' % fname 
    print 'START DATA'
    print irData
    print 'END DATA'

    ylabels = ['Y']
    irData = S.addIRevealOutputs(irData, ylabels)

    outfile = 'ireveal_regression.py'
    irDriver = S.writeIRevealDriver(irData, outfile)
    print '................................................'
    print 'Executable has been written to %s.' % irDriver
    print '................................................'

if testAlamo:
    fname = '/g/g19/ng30/ts6/foqus/examples/UQ/alamo_static.lst'

    alamoData = S.parseAlamo(fname)
    print '................................................'
    print 'Data extracted from %s:\n' % fname 
    print 'START DATA'
    print alamoData
    print 'END DATA'

    outfile = 'alamo_regression.py'
    alamoDriver = S.writeAlamoDriver(alamoData, outfile)
    print '................................................'
    print 'Executable has been written to %s.' % alamoDriver
    print '................................................'
