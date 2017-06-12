import numpy as np
import sys

def main(nSamples, nInputs):

    # Generate a sample from U(a,b)
    a = -5.0
    b = 5.0
    r = (b-a)*np.random.random_sample((nSamples,nInputs))+a

    fname = 'x3sample.txt'
    with open(fname,'wb') as f:
        f.write(b'%d %d\n' % (nSamples,nInputs))
        np.savetxt(f, r, delimiter=' ')
        f.close()

    print 'Sample of size (%d,%d) written to %s' % (nSamples, nInputs, fname)
    return None

if __name__ == '__main__':
    main(int(sys.argv[1]),int(sys.argv[2]))
