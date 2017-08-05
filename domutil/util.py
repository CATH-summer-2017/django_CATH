from modeller import *
from modeller.scripts import complete_pdb
### Enable this line to reduce verbositys
# log.none()
import sys
import StringIO
import contextlib
import re 
import numpy as np

p_nb = re.compile("Number of non-bonded pairs \(excluding 1-2,1-3,1-4\): *([0-9]*)")
p_energy=re.compile("Current energy *: *([0-9,\.,-]*)")
p_atomCount = re.compile("Number of all, selected real atoms *: ([0-9, ]{10})")
p_resCount = re.compile("Number of all residues in MODEL *: *([0-9]*)")


levels=[ None,
'root',
'Class',
'arch',
'topo',
'homsf',
's35',
's60',
's95',
's100'];

@contextlib.contextmanager
def stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = StringIO.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old


class counter():
    def __init__(self, lst, per = 100):
        self.lst = list(lst);
        self.imax= len(lst)
        self.i   = 0
        self.per = per
    def count(self):
        if not self.i % self.per:
            print('%d of %d'%(self.i,self.imax))
        self.i += 1

def get_something( pdbfile, env = None, auto_complete = False, s0 = None):
	if not env:
		env = environ()
		#env.io.atom_files_directory = ['../atom_files']
		env.io.atom_files_directory = ['../pdbs']
		env.libs.topology.read(file='$(LIB)/top_heav.lib')
		env.libs.parameters.read(file='$(LIB)/par.lib')
	if auto_complete:
		mdl = complete_pdb(env, pdbfile)
	else:
		mdl = model(env)
		mdl.read( pdbfile, model_format='PDB', model_segment=('FIRST:@', 'LAST:'), io=None);
	if not s0:
		s0 = StringIO.StringIO();
	else:
		s0.truncate(0)
	
	with stdoutIO(s0) as s:
		nDOPE = mdl.assess_normalized_dope()
	s0buf = ''.join(s0.buflist)
	# return 
	outdict = {"nDOPE":nDOPE,
		"DOPE": float(p_energy.findall(s0buf)[0]),
		"nbpair_count":int(p_nb.findall(s0buf)[0]),
		"atom_count":int(p_atomCount.findall(s0buf)[0].strip()),
		 "res_count":  int(p_resCount.findall(s0buf)[0]),
		  }
	return outdict


def get_nDOPE( pdbfile, env = None, auto_complete = False, **kwargs):
# pdbfile = "4xz8A_chop"
#mdl = complete_pdb(env, "1fas")
	
	### Use existing environment to avoid redundant re-initialisation.
	# if not env:
	# 	env = environ()
	# 	#env.io.atom_files_directory = ['../atom_files']
	# 	env.io.atom_files_directory = ['../pdbs']
	# 	env.libs.topology.read(file='$(LIB)/top_heav.lib')
	# 	env.libs.parameters.read(file='$(LIB)/par.lib')

	# if auto_complete:
	# 	mdl = complete_pdb(env, pdbfile)
	# else:
	# 	mdl = model(env)
	# 	mdl.read( pdbfile, model_format='PDB', model_segment=('FIRST:@', 'LAST:'), io=None);
	# nDOPE = mdl.assess_normalized_dope()
	# # pdbname = os.path.basename(pdbfile)


	nDOPE = get_something(pdbfile, env, auto_complete,**kwargs).get("nDOPE")
	return nDOPE

import csv

def csv_listener( q, fname):
	'''listens for messages on the q, writes to file. '''
	## Read "fname" from global. "fname" file must exists prior to call.

	f = open(fname, 'a') 
	c = csv.writer(f)
	while 1:
		m = q.get()
		if m == 'kill':
			# f.write('killed \n')
			break
		elif m == 'clear':
			f.truncate();	
		else:## Asumme a csv row
			row = m
			c.writerow( row )
		f.flush()
	f.close()



def worker( i, q, slist):
	# global wait, waitname
	# pdbfile = onlyfiles[i];
	(wait,waitname,reset,fname,env,args) = slist

	pdbfile = i;
	import os 

	pdbname = os.path.basename(pdbfile);
	if pdbname.split(".")[-1] in ["bak","csv"]:
		return 
	if wait:
		nDOPE = 0
		if pdbname == waitname:
			q.put('start');
			nDOPE = get_nDOPE( pdbfile, env = env, auto_complete = args.auto_complete)
		row = [pdbname, nDOPE ];

	else:	
		# print("\n\n//Testing structure from %s" % pdbfile)
		nDOPE = get_nDOPE( pdbfile, env = env, auto_complete = args.auto_complete)				
		row = [pdbname, nDOPE] ;
	q.put( row );
	
	return row



### Statistics helper functions

def MAD_outlier(points, thresh=3.5):
	"""
	Returns a boolean array with True if points are outliers and False 
	otherwise.

	Parameters:
	-----------
		points : An numobservations by numdimensions array of observations
		thresh : The modified z-score to use as a threshold. Observations with
			a modified z-score (based on the median absolute deviation) greater
			than this value will be classified as outliers.

	Returns:
	--------
		mask : A numobservations-length boolean array.

	References:
	----------
		Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
		Handle Outliers", The ASQC Basic References in Quality Control:
		Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
	"""
	if not isinstance(points,np.ndarray):
		points = np.array(points)
	if len(points.shape) == 1:
		points = points[:,None]
	median = np.median(points, axis=0)
	diff = np.sum((points - median)**2, axis=-1)
	diff = np.sqrt(diff)
	med_abs_deviation = np.median(diff)

	modified_z_score = 0.6745 * diff / med_abs_deviation

	return modified_z_score > thresh


def cov2corr(c):
	c = np.copy(c)
	try:
		d = np.diag(c)
	except ValueError:
		# scalar covariance
		# nan if incorrect value (nan, inf, 0), 1 otherwise
		return c / c
	stddev = np.sqrt(d.real)
	c /= stddev[:, None]
	c /= stddev[None, :]

	# Clip real and imaginary parts to [-1, 1].  This does not guarantee
	# abs(a[i,j]) <= 1 for complex arrays, but is the best we can do without
	# excessive work.
	np.clip(c.real, -1, 1, out=c.real)
	if np.iscomplexobj(c):
		np.clip(c.imag, -1, 1, out=c.imag)

	return c