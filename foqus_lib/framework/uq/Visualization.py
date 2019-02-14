import numpy
from .UQAnalysis import UQAnalysis
from .Visualizer import Visualizer
from .Common import Common

class Visualization(UQAnalysis):
    def __init__(self, ensemble, output, inputs):
        super(Visualization, self).__init__(ensemble, output, UQAnalysis.VISUALIZATION)
        if not isinstance(inputs, (tuple, list)):
            inputs = [inputs]
        self.setInputs(inputs)
        xlist = numpy.array(inputs)
        k = numpy.where(xlist > 0)
        self.x = xlist[k]
        self.cmd = 'splot'
        if len(self.x) == 2:
            self.cmd = 'splot2'
        outfile = {'splot': 'matlabsp.m',
                   'splot2': 'matlabsp2.m'}
        self.outfile = outfile[self.cmd]
    
    def analyze(self):
        data = self.ensemble.getValidSamples()
        Common.initFolder(Visualizer.dname)

        fname = Common.getLocalFileName(Visualizer.dname, data.getModelName().split()[0], '.dat')
        data.writeToPsuade(fname)

        #perform screening
        mfile = Visualizer.yScatter(fname, self.outputs[0], self.x, self.cmd)

        #archive file
        if mfile is not None:
            self.archiveFile(mfile)
        return mfile

    def showResults(self):
        #restore .m file from archive
        fileName = self.outfile
        self.restoreFromArchive(fileName)
        
        Visualizer.yScatterPlot(self.ensemble, self.outputs[0], self.x, self.cmd, fileName)

    def getAdditionalInfo(self):
        pass
