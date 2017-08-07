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
	pdbfile = os.path.expandvars(pdbdir) + pdbname
	# print os.path.isfile(pdbfile)
	# assert os.path.isfile(pdbfile), "Cannot open PDB file at %s" % pdbfile
	
	if not parser:
		parser = PDBParser()
	struct = parser.get_structure('X', pdbfile)

	return struct

def get_something(input, env = None, auto_complete = False, s0 = None, pdbdir = None, cutout=15.0,cutin=3.5,
	 **kwargs):
	if isinstance(input,Structure.Structure):
		struct = input
	else:
		with stdoutIO(s0) as s:
			pdbname = input
			struct = parse_PDB(pdbname, **kwargs)
		# struct = p.get_structure('X', pdbfile)
	alst = list(struct.get_atoms())
	acount = len(alst)
	rcount = sum( 1 for _ in struct.get_residues())
	nbpair_count = (
	len( NeighborSearch(alst ).search_all(radius =cutout))  
	-  len( NeighborSearch(alst ).search_all(radius =cutin)) 
	)

	### For some weird reasons, many structures are not correctly parsed by Biopython, (but Okay with modeller)
	### This is a temporary patch to detect overlapping
	if acount > rcount * 11:
		acount /= 2
		nbpair_count /= 4

	outdict = {"nDOPE":0,
		"DOPE": 0,
		"nbpair_count":nbpair_count,
		"atom_count": acount,
		 "res_count": rcount,
		  }
	return outdict


# if django.settings

if 'USE_MODELLER' in os.environ.keys():
	USE_MODELLER = int(os.environ['USE_MODELLER'])
else:
	USE_MODELLER = 0
if USE_MODELLER:
	from modeller import *
	from modeller.scripts import complete_pdb

	def	init_env(env=None):

		with stdoutIO() as s:	
			env = environ()
			#env.io.atom_files_directory = ['../atom_files']
			env.io.atom_files_directory = ['../pdbs','$(PDBlib)/',
			'$(repos)/cathdb/dompdb/',
			'$(repos)/cathdb/temppdbs/',
			]
			env.libs.topology.read(file='$(LIB)/top_heav.lib')
			env.libs.parameters.read(file='$(LIB)/par.lib')
		return env	

	def get_something_modeller( pdbfile, env = None, auto_complete = False, s0 = None, **kwargs):
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