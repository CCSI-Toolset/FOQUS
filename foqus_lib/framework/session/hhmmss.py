import math

def hhmmss(sec_in):
    # convert seconds to hh:mm:ss format
    h = int(sec_in//3600)
    m = int(sec_in%3600//60)
    s = sec_in%3600%60
    if h < 24:
        hstr = "{0:0>2}".format(h)
    if h >= 24:
        hstr = "{0} days {1:0>2}".format(h//24, h%24)
    return "{0}:{1:0>2}:{2:0>2}".format(hstr,m,int(s))
    

#test 
if __name__ == "__main__":
    print hhmmss(0.1)
    print hhmmss(1)
    print hhmmss(10)
    print hhmmss(100)
    print hhmmss(1000)
    print hhmmss(10000)
    print hhmmss(100000000)
    
    
