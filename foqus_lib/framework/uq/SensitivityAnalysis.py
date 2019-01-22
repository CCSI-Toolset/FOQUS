from .UQAnalysis import UQAnalysis
from .RawDataAnalyzer import RawDataAnalyzer
from .Common import Common

class SensitivityAnalysis(UQAnalysis):

    fullNames = ['First-order', 'Second-order', 'Total-order']
    psuadeNames = ['me', 'ie', 'tsi']
    outFileNames = ['matlabme.m', 'matlabaie.m', 'matlabtsi.m']
                   
    def __init__(self, ensemble, output, subType):
        super(SensitivityAnalysis, self).__init__(ensemble, output, UQAnalysis.SENSITIVITY, subType)

    @staticmethod
    def getSubTypeFullName(num):
        return SensitivityAnalysis.fullNames[num]

    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(RawDataAnalyzer.dname, data.getModelName().split()[0], '.dat')
        data.writeToPsuade(fname)

        #perform screening
        cmd = SensitivityAnalysis.psuadeNames[self.subType]
        mfile = RawDataAnalyzer.performSA(fname, self.outputs[0], cmd)

        #archive file
        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        #restore .m file from archive
        fileName = SensitivityAnalysis.outFileNames[self.subType]
        self.restoreFromArchive(fileName)
        
        cmd = SensitivityAnalysis.psuadeNames[self.subType]
        RawDataAnalyzer.plotSA(self.ensemble, cmd, self.outputs[0], fileName)

