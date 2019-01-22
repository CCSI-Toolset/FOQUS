from .UQAnalysis import UQAnalysis
from .RawDataAnalyzer import RawDataAnalyzer
from .Common import Common

class CorrelationAnalysis(UQAnalysis):

    def __init__(self, ensemble, output):
        self.moments = None
        super(CorrelationAnalysis, self).__init__(ensemble, output, UQAnalysis.CORRELATION)
    
    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(RawDataAnalyzer.dname, data.getModelName().split()[0], '.dat')
        data.writeToPsuade(fname)

        #perform UA
        mfile = RawDataAnalyzer.performCA(fname, self.outputs[0])
        
        #archive file
        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        #restore .m file from archive
        fileName = 'matlabca.m'
        self.restoreFromArchive(fileName)
        
        RawDataAnalyzer.plotCA(self.ensemble, self.outputs[0], fileName)

