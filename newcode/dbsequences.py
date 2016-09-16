import primers
from utils import debug


def AddSequences(con,cur,sequences,taxonomies=None,ggids=None,primer='V4',commit=True):
	"""
	Add sequence entries to database if they do not exist yet
	input:
	con,cur : database connection and cursor
	sequences: list of str
		the sequences to add
	taxonomies: list of str (optional)
		taxonomy of each sequence or None to add NA
	ggids: list of int (optional)
		list of GreenGenes id for each sequence or None to add 0
	primer: str (optional)
		Name of the primer (from PrimersTable). default is V4
	commit : bool (optional)
		True (default) to commit, False to wait with the commit

	output:
	seqids : list of int or None
		list of the new ids or None if error enountered
	"""
	# get the primer region id
	seqids=[]
	numadded=0
	idprimer = primers.GetIdFromName(con,cur,primer)
	if idprimer<=0:
		debug(2,'primer %s not found' % primer)
		return None
	debug(1,'primerid %s' % idprimer)
# try:
	for idx,cseq in enumerate(sequences):
		# test if already exists, skip it
		cseqid=GetSequenceId(con,cur,sequence=cseq,idprimer=idprimer)
		if cseqid<=0:
			if taxonomies is None:
				ctax='na'
			else:
				ctax=taxonomies[idx].lower()
			if ggids is None:
				cggid=0
			else:
				cggid=ggids[idx]
			cseq=cseq.lower()
			cur.execute('INSERT INTO SequencesTable (idPrimer,sequence,length,taxonomy,ggid) VALUES (%s,%s,%s,%s,%s) RETURNING id',[idprimer,cseq,len(cseq),ctax,cggid])
			cseqid=cur.fetchone()[0]
			numadded+=1
		seqids.append(cseqid)
	if commit:
		con.commit()
	debug(3,"Added %d sequences (out of %d)" % (numadded,len(sequences)))
	return(seqids)
# except:
	debug(7,'error enountered - sequences not added')
	return(None)


def GetSequencesId(con,cur,sequences):
	"""
	Get sequence ids for a sequence or list of sequences

	input:
	con,cur : database connection and cursor
	sequences : list of str (ACGT sequences)

	output:
	ids : ilist of int
		the list of ids for each sequence (-1 for sequences which were not found)
	"""
	ids=[]
	for cseq in sequences:
		ids.append(GetSequenceId(con,cur,cseq))
	return ids


def GetSequenceId(con,cur,sequence,idprimer=None):
	"""
	Get sequence ids for a sequence or list of sequences

	input:
	con,cur : database connection and cursor
	sequence : str (ACGT sequences)
	idprimer : int (optional)
		if supplied, verify the sequence is from this idPrimer

	output:
	sid : int
		the ids of the sequence (-1 if not found)
	"""
	cseq=sequence.lower()
	# if no regionid specified, fetch only 1 (faster)
	if idprimer is None:
		cur.execute('SELECT id FROM SequencesTable WHERE sequence=%s LIMIT 1',cseq)
		if cur.rowcount==0:
			sid=-1
			debug(2,'sequence %s not found' % sequence)
		else:
			debug(1,'sequence %s found id %d' % (sequence,sid))
			sid=cur.fetchone()[0]
		return sid
	# regionid was specified, so test all matching sequences
	cur.execute('SELECT id,idPrimer FROM SequencesTable WHERE sequence=%s LIMIT 1',[cseq])
	for cres in cur:
		if cres[1]==idprimer:
			sid=cres[0]
			debug(1,'sequence %s found with primer. id %d' % (sequence,sid))
			return sid
	debug(2,'sequence %s not found with primer. non primer matches: %d' % (sequence,cur.rowcount))
	return -1
