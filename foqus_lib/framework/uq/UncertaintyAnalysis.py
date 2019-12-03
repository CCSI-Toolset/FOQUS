from .UQAnalysis import UQAnalysis
from .RawDataAnalyzer import RawDataAnalyzer
from .Common import Common

class UncertaintyAnalysis(UQAnalysis):

    def __init__(self, ensemble, output):
        self.moments = None
        super(UncertaintyAnalysis, self).__init__(ensemble, output, UQAnalysis.UNCERTAINTY)

    def saveDict(self):
        sd = super(UncertaintyAnalysis, self).saveDict()
        sd['moments'] = self.moments
        return sd

    def loadDict(self, sd):
        super(UncertaintyAnalysis, self).loadDict(sd)
        self.moments = sd.get('moments', None)

    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(RawDataAnalyzer.dname, data.getModelName().split()[0], '.dat')
        data.writeToPsuade(fname, fixedAsVariables=True)

        #perform UA
        mfile, self.moments = RawDataAnalyzer.performUA(fname, self.outputs[0])
        
        #archive file
        if mfile is not None:
            self.archiveFile(mfile)

        return mfile

    def showResults(self):
        #restore .m file from archive
        fileName = 'matlabua.m'
        self.restoreFromArchive(fileName)
        
        RawDataAnalyzer.plotUA(self.ensemble, self.outputs[0], fileName, self.moments)

