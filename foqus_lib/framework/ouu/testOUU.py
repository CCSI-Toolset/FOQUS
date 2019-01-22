from .OUU import OUU


y = 1
xtable = [{'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'Opt: Primary (X1)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'Opt: Primary (X1)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'Opt: Primary (X1)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'Opt: Primary (X1)'},
          {'param2': None, 'param1': None, 'max': 10.0, 'pdf': 0, 'min': -10.0, 'type': 'Opt: Recourse (X2)'},
          {'param2': None, 'param1': None, 'max': 10.0, 'pdf': 0, 'min': -10.0, 'type': 'Opt: Recourse (X2)'},
          {'param2': None, 'param1': None, 'max': 10.0, 'pdf': 0, 'min': -10.0, 'type': 'Opt: Recourse (X2)'},
          {'param2': None, 'param1': None, 'max': 10.0, 'pdf': 0, 'min': -10.0, 'type': 'Opt: Recourse (X2)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'UQ: Discrete (X3)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'UQ: Discrete (X3)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'UQ: Discrete (X3)'},
          {'param2': None, 'param1': None, 'max': 5.0, 'pdf': 0, 'min': -5.0, 'type': 'UQ: Continuous (X4)'}]
phi = {'type':1}
#phi = {'type':2, 'beta':.2}
#phi = {'type':3, 'alpha':.01}
#phi = {'type':4}
x3sample = {'file':'/g/g19/ng30/ts6/foqus/foqus_lib/gui/ouu/ouu_example/x3sample.txt'}
#x4sample = {'method':'LHS', 'nsamples':5}
x4sample = {'method':'Factorial', 'nlevels':5}
#useRS = True
useRS = False
#useBobyqa = True
useBobyqa = False
if useBobyqa:   # the driver is a simulator, will use BOBYQA to optmize
    fname = '/g/g19/ng30/ts6/foqus/foqus_lib/gui/ouu/ouu_example/ouu_simdriver.in'
else:           # the driver is an optimizer
    fname = '/g/g19/ng30/ts6/foqus/foqus_lib/gui/ouu/ouu_example/ouu_optdriver.in'

results = OUU.ouu(fname,y,xtable,phi,x3sample=x3sample,x4sample=x4sample,useRS=useRS,useBobyqa=useBobyqa)

#f = open('ouu.out')
#lines = f.read()
#f.close()
#results = OUU.getResults(lines)

print(results)
