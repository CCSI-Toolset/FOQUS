import numpy as np

class SamplingMethods:
    MC, LPTAU, LH, OA, MOAT, GMOAT, LSA, METIS, GMETIS, FACT = list(range(10))
    fullNames = ('Monte Carlo', 'Quasi Monte Carlo', 'Latin Hypercube',
                 'Orthogonal Array', 'Morris Design', 'Generalized Morris Design',
                 'Gradient Sample', 'METIS', 'Monte Carlo', 'Full Factorial Design')
    psuadeNames = ('MC', 'LPTAU', 'LH', 'OA', 'MOAT', 'GMOAT', 'LSA', 'METIS', 'GMETIS', 'FACT')

    @staticmethod
    def getFullName(num):
        return SamplingMethods.fullNames[num]

    
    @staticmethod
    def getPsuadeName(num):
        return SamplingMethods.psuadeNames[num]

    @staticmethod
    def getInfo(num):
        return (SamplingMethods.fullNames[num], SamplingMethods.psuadeNames[num])

    @staticmethod
    def getEnumValue(name):
        try:
            index = SamplingMethods.fullNames.index(name)
            return index
        except ValueError:
            index = SamplingMethods.psuadeNames.index(name)
            return index
    
    @staticmethod
    def validateSampleSize(num, nInputs, nSamples):
        if num == SamplingMethods.LSA:
            return nInputs+1
        elif num == SamplingMethods.MOAT or num == SamplingMethods.GMOAT:
            M = float(nInputs+1)
            a = np.floor(float(nSamples)/M)*M
            b = np.ceil(float(nSamples)/M)*M
            if a == b:
                return nSamples
            else:
                return (a,b)
        else:
            return nSamples
