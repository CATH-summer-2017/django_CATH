### Enable this line to reduce verbositys
# log.none()
from Bio.PDB import *
from .util import *
import sys,os

def parse_PDB(pdbname,pdbdir=None,parser = None):
	if pdbdir:
		pass
	else:
		if 'PDBlib' in os.environ.keys():
			pdbdir = '$PDBlib/'
		else:
			os.environ['$PDBlib'] = './'
			pdbdir = '$PDBlib/'
	pdbfile = os.path.expandvar(pdbdir) + pdbname
	
	if not parser:
		parser = PDBParser()
	struct = parser.get_structure('X', pdbfile)

	return struct

def get_something(pdbname, env = None, auto_complete = False, s0 = None, pdbdir = None, cutout=15.0,cutin=3.5):

	struct = parse_PDB(pdbname)
	# struct = p.get_structure('X', pdbfile)
	alst = list(struct.get_atoms())
	rcount = sum( 1 for _ in struct.get_residues())
	nbpair_count = (
	len( NeighborSearch(alst ).search_all(radius =cutout))  
	-  len( NeighborSearch(alst ).search_all(radius =cutin)) 
	)

	outdict = {"nDOPE":0,
		"DOPE": 0,
		"nbpair_count":nbpair_count,
		"atom_count": len(alst),
		 "res_count": rcount,
		  }


# if django.settings

if 'USE_MODELLER' in os.environ.keys():
	USE_MODELLER = int(os.environ['USE_MODELLER'])
else:
	USE_MODELLER = 0
if USE_MODELLER:
	from modeller import *
	from modeller.scripts import complete_pdb

	def get_something( pdbfile, env = None, auto_complete = False, s0 = None):
		if not env:
			env = environ()
			#env.io.atom_files_directory = ['../atom_files']
			env.io.atom_files_directory = ['../pdbs',
			'$(PDBlib)']
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