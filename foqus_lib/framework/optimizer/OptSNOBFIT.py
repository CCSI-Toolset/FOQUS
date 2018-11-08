import time, copy
import numpy

snobfit_available = True
try:
	from snobfit import snobfit
except ImportError as e:
	snobfit_available = False


class opt():
	def __init__(self, graph = None):
		self.graph   = graph
		self.options = dict()
		self.optionsDesc = dict()
		self.optionOrder = []
		self.name = "SNOBFIT-NIST"
		self.available = snobfit_available
		self.description = "Python implimentation of SNOBFIT from ..."
		self.mp = False
		self.mobj = False
        # add options   Name             Default              Description
		self.addOption("lower",          [0, 0],             " lower bounds on scaled vars"             )
		self.addOption("upper",          [10,10],            " upper bounds on scaled vars"             )
		self.addOption("itmax",          0,                  " maximum number of iterations"            )
		self.addOption("Output File",    "snobfit-out.txt",  " file to store results of each func eval" )
		self.addOption("Flush Modulus",  1,                  " how often to flush output to file"       )

	def addOption(self, name, dflt, desc = None):
		self.optionOrder.append(name)
		self.options[name] = dflt
		self.optionsDesc[name] = desc

	def func(self, x):
		self.graph.setGlobalVariables(self.xnames, x, 'scaled', True)
		obj = self.graph.calcObjective()[0]
		if self.ofile != "":
			self.graph.writeCSV() #write all graph input, output, err code, and solution time plus add objective
			self.flushc += 1
			if self.flushc%self.flushm == 0:
				self.graph.flushCSV()
		return obj

	def optimize(self):
		gr = self.graph
		gr.generateGlobalVariables()
		print("Decision Variables")
		print("---------------------")
		xnames = gr.opt.v
		self.xnames = xnames
		gr.scaleGlobalVariables(xnames)
		xinit = gr.getGlobalVariables(xnames, 'scaled', True)
		for xn in xnames:
			print((xn + ": " + str(gr.x[xn].value) + "  scaled: " + str(gr.x[xn].scaled)))
		print("----------------------")
		print("Optimizer = SNOBFIT-NIST")

		opts = copy.deepcopy(self.options)

		itmax        =  opts.pop( "itmax"         )
		ofile        =  opts.pop( "Output File"   )
		self.flushm  =  opts.pop( "Flush Modulus" )
		upper        =  opts.pop( "upper"         )
		lower        =  opts.pop( "lower"         )
		bounds       =  [numpy.array(lower),numpy.array(upper)]
		if itmax == 0: itmax = 50000 # in nmax is 0 just set max iterations to large number

		#
		# setup solver set options ...

		f = len(xnames)*[0]
		it = 0

		if ofile != "":
			gr.createCSV(ofile) # create a CSV output file add a coulmn for objective
			self.ofile = ofile
		self.flushc = 0
		start = time.clock()

		xopt, fopt, nit = snobfit.snobfit(self.func,
										  xinit,
										  bounds,
										  maxiter = itmax)

		if ofile != "":
			gr.closeCSV()
		print("-------------------------")
		print(("Elapsed Time: " + str(time.clock() - start) + " sec"))
		print("-------------------------")
		print("Solution")
		print("-------------------------")

		# resolve with opt so the best solution will be on flowsheet
		gr.setGlobalVariables(xnames, xopt, 'scaled', True)
		gr.solve() #resolve with optimal input
		xfinal = gr.getGlobalVariables(xnames, 'value', True)

		print(("best f " + str(fopt)))
		print(("best x (scaled): " + str(xopt)))
		print(("best x (notscaled): " + str(xfinal)))
		print(("number of iterations: " + str(nit)))
