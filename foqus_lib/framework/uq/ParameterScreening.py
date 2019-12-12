from .UQAnalysis import UQAnalysis
from .RawDataAnalyzer import RawDataAnalyzer
from .Common import Common

class ParameterScreening(UQAnalysis):
    MOAT, LSA, MARSRANK, SOT, DELTA, GP = list(range(6))

    fullNames = ('MOAT', 'Local Sensitivity Analysis', 'MARS Ranking', 
                 'Sum of Trees', 'Delta Test', 'Gaussian Process')
    psuadeNames = ('moat', 'lsa', 'mars_sa', 'sot_sa', 'delta_test', 'gp_sa')

    outFileNames = ('matlabmoatbs.m', 'matlablsa.m', 'matlabmarsa.m', 'matlabsot.m',
                    'matlabdelta.m', 'matlabkrisa.m')

    @staticmethod
    def getSubTypeFullName(num):
        return ParameterScreening.fullNames[num]

    @staticmethod
    def getSubTypePsuadeName(num):
        return ParameterScreening.psuadeNames[num]

    @staticmethod
    def getInfo(num):
        return (ParameterScreening.fullNames[num], ParameterScreening.psuadeNames[num])

    @staticmethod
    def getEnumValue(name):
        try:
            index = ParameterScreening.fullNames.index(name)
            return index
        except ValueError:
            index = ParameterScreening.psuadeNames.index(name)
            return index

    def __init__(self, ensemble, output, subType):
        super(ParameterScreening, self).__init__(ensemble, output, UQAnalysis.PARAM_SCREEN, subType)
    
    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(RawDataAnalyzer.dname)
        fname = Common.getLocalFileName(RawDataAnalyzer.dname, data.getModelName().split()[0], '.dat')
        data.writeToPsuade(fname)

        #perform screening
        cmd = ParameterScreening.getSubTypePsuadeName(self.subType)
        mfile = RawDataAnalyzer.screenInputs(fname, self.outputs[0], cmd)

        if mfile is not None:
            #archive file
            self.archiveFile(mfile)

        return mfile

    def showResults(self):
        #restore .m file from archive
        fileName = ParameterScreening.outFileNames[self.subType]
        self.restoreFromArchive(fileName)
        
        cmd = ParameterScreening.getSubTypePsuadeName(self.subType)
        RawDataAnalyzer.plotScreenInputs(self.ensemble, cmd, self.outputs[0], fileName)

