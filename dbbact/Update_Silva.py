from utils import debug, SetDebugLevel
import db_access
import dbsequences
import dbuser
import os
import time
import datetime
import hashlib
from pathlib import Path
from collections import defaultdict


def removeFile(file_name):
    try:
        os.remove(file_name)
    except OSError:
        pass

def createSeqFile(file_name,seq_str):
    with open(file_name, "w") as text_file:
        text_file.write(">seq\n%s" % seq_str)

def saveStringToFile(file_name,content_str):
    with open(file_name, "w") as text_file:
        text_file.write(content_str)        
        
def readResultFromFile(file_name):
    ret = ""
    try:
        with open (file_name, "r") as myfile:
            ret=myfile.readlines()
    except:
        pass
    return ret

def hash_sequences(filename, short_len=100):
	'''hash all the sequences in a fasta file

	Parameters
	----------
	filename: str
		the fasta file

	Returns
	-------
	seq_hash: dict of {seq: seqid}
	seq_lens : list of int
		all the sequence lengths in the fasta file (so we can hash all the lengths in the queries)
	short_hash: dict of {short_seq: seq_hash dict}
	'''
	num_too_short = 0
	seq_hash = {}
	seq_lens = set()
	short_hash = defaultdict(dict)
	for cseq, chead in iter_fasta_seqs(filename):
		clen = len(cseq)
		if clen < short_len:
			num_too_short += 1
			continue
		short_seq = cseq[:short_len]
		short_hash[short_seq][cseq] = chead
		if clen not in seq_lens:
			seq_lens.add(clen)
		seq_hash[cseq] = chead
	debug(2,'processed %d sequences.' % len(seq_hash))
	debug(2,'lens: %s' % seq_lens)
	debug(2,'num too short: %d' % num_too_short)
	return seq_hash, seq_lens, short_hash


def iter_fasta_seqs(filename):
	"""
	iterate a fasta file and return header,sequence
	input:
	filename - the fasta file name

	output:
	seq - the sequence
	header - the header
	"""

	fl = open(filename, "rU")
	cseq = ''
	chead = ''
	for cline in fl:
		if cline[0] == '>':
			if chead:
				yield(cseq.lower(), chead)
			cseq = ''
			chead = cline[1:].rstrip()
		else:
			cline = cline.strip().lower()
			cline = cline.replace('u', 't')
			cseq += cline.strip()
	if cseq:
		yield(cseq, chead)
	fl.close()



def isFileExist(fileName):
    my_file = Path("stop")
    if my_file.is_file():
        # file exists
        return True
    return False

if __name__ == '__main__':
    SetDebugLevel(0)
    date_time_str = datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
    
    #remove stop file
    removeFile("stop")
    
    #connect to the db
    con, cur = db_access.connect_db()
    
    debug(2, 'Started')
    if 'OPENU_FLAG' in os.environ:
        debug(2, 'Openu')
    else:
        debug(2, 'normal')
    
    
    count_success = 0
    count_failure = 0
    count_seq_success = 0
    count_seq_failure = 0
    count_seq_is_exist_failure = 0
    count_seq_exist = 0
    count = 1
    hash_log = ""
    sleep_time = 86400
    short_len=150
    seqdbid = 1 # SILVA
    silva_log = ""
    
    silvaFileName = 'SILVA_132_SSURef_tax_silva.fasta'
    
    #dbsequences.SequencesToFile(con, cur, 'tempEitanJune.fasta')
    
    while isFileExist("stop") == False:
    #while isFileExist("stop") == False:
        
        seq_hash, seq_lens, short_hash = hash_sequences(filename='tempEitanJune.fasta', short_len=150)
        
        idx = 0
        num_matches = 0
        
        for cseq, chead in iter_fasta_seqs(silvaFileName):
            isFound = False 
            idx += 1
            if idx % 1000 == 0:
                debug(2, "count: %d"  % idx)
            for cpos in range(len(cseq) - short_len):
                ccseq = cseq[cpos:cpos + short_len]
                if ccseq in short_hash:
					
                    for k, v in short_hash[ccseq].items():
                        if k in cseq:
                            cid = chead.split(' ')[0]
                            
                            silva_log += "rec found: seq id %s , db bact id %s, id %s\n" % (seqdbid, v, cid)
                            
                            #check if already exist
                            err, existFlag = dbsequences.WholeSeqIdExists(con,cur, seqdbid, v, cid);
                            if err:
                                count_seq_is_exist_failure += 1 
                                silva_log += "failed to found"
                            if existFlag:
                                count_seq_exist += 1
                                silva_log += "found"
                                isFound = True
                                break
                            else:
                                err = dbsequences.AddWholeSeqId(con,cur, seqdbid, v, cid)
                                if err:
                                    silva_log += "failed to add"
                                    count_seq_failure += 1 
                                    break
                                else:
                                    silva_log += "added"
                                    count_seq_success += 1
                                    isFound = True
                                    break
            #if count_seq_success == 10000:
            #    break
        
        debug(2, 'done')
        
        
        summary_str = "failed count = %s\nsuccess count = %s\nis exist count = %s\nis exist error = %s\n" % (count_seq_failure,count_seq_success,count_seq_exist,count_seq_is_exist_failure)
        
        saveStringToFile("silva_summary_log_" + date_time_str,summary_str)
        saveStringToFile("silva_log_" + date_time_str,silva_log)
        
        
        break