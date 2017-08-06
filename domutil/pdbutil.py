from modeller import *
from modeller.scripts import complete_pdb
### Enable this line to reduce verbositys
# log.none()
from .util import *


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