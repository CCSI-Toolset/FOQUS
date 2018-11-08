from .UQRSAnalysis import UQRSAnalysis
from .UQAnalysis import UQAnalysis
from .ResponseSurfaces import ResponseSurfaces
from .RSAnalyzer import RSAnalyzer
from .SensitivityAnalysis import SensitivityAnalysis
from .Common import Common


class RSSensitivityAnalysis(UQRSAnalysis):

    psuadeNames = ['rssobol1','rssobol2','rssoboltsi']

    def __init__(self, ensemble, output, subType, responseSurface, rsOptions = None,
                 userRegressionFile = None, xprior = None):
        super(RSSensitivityAnalysis, self).__init__(ensemble, output, UQAnalysis.RS_SENSITIVITY,
                                                    responseSurface, subType, rsOptions,
                                                    userRegressionFile, xprior)
        sa_bars = [False, False, False]
        self.showErrorBars = sa_bars[self.subType]

    @staticmethod
    def getSubTypeFullName(num):
        return SensitivityAnalysis.fullNames[num]

    def analyze(self):
        data = self.ensemble  
        fnameRS = Common.getLocalFileName(RSAnalyzer.dname, data.getModelName().split()[0], '.rsdat')
        index = ResponseSurfaces.getEnumValue(self.responseSurface)
        fixedAsVariables = index == ResponseSurfaces.USER
        data.writeToPsuade(fnameRS, fixedAsVariables=fixedAsVariables)
        cmd = RSSensitivityAnalysis.psuadeNames[self.subType]
        mfile = RSAnalyzer.performSA(fnameRS, self.outputs[0], cmd, self.showErrorBars,
                                     self.responseSurface, self.rsOptions,
                                     self.userRegressionFile, self.xprior)

        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        cmd = RSSensitivityAnalysis.psuadeNames[self.subType]
        cmd_ = cmd
        if self.showErrorBars:
            cmd = cmd + 'b'
        mfile = 'matlab' + cmd + '.m'
        self.restoreFromArchive(mfile)
        
        RSAnalyzer.plotSA(self.ensemble, self.outputs[0], self.responseSurface,
                          cmd_, self.showErrorBars, mfile)

