
import os
import time
import datetime
import hashlib
from pathlib import Path
from collections import defaultdict

#change the working directory
import sys
sys.path.insert(0, '/Users/admin/supercooldb')
sys.path.insert(0, '/home/eitano/supercooldb')
    

from dbbact.utils import debug, SetDebugLevel
from dbbact import db_access
from dbbact import dbsequences
from dbbact import dbuser

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
	all_ids = set()
	short_hash = defaultdict(dict)
	for cseq, chead in iter_fasta_seqs(filename):
		all_ids.add(chead)
		
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
	return all_ids, seq_hash, seq_lens, short_hash


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
    my_file = Path(fileName)
    if my_file.is_file():
        # file exists
        return True
    return False

def main_func_silva():
    
    SetDebugLevel(0)
    date_time_str = datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
    
    #connect to the db
    con, cur = db_access.connect_db()
    
    debug(2, 'Started')
    if 'OPENU_FLAG' in os.environ:
        debug(2, 'Openu')
    else:
        debug(2, 'normal')
    
    
    count_success = 0
    count_failure = 0
    count_dummy_success = 0
    count_dummy_failure = 0
    count_seq_success = 0
    count_seq_failure = 0
    count_seq_is_exist_failure = 0
    count_seq_exist = 0
    
    count_seq_is_exist_dummy_failure = 0
    count_seq_dummy_exist = 0
    count_seq_dummy_failure = 0
    count_seq_dummy_success = 0
    
    count = 1
    hash_log = ""
    sleep_time = 86400
    #sleep_time = 10
    short_len=150
    seqdbid = 1 # SILVA
    silva_log = ""
    
    tempFileName = 'tempSilvaScript.fasta'
    silvaFileName = 'SILVA_132_SSURef_tax_silva.fasta'
    
    while isFileExist("stop_silva") == False:
        
        #Create the file and read it
        dbsequences.SequencesWholeToFile(con, cur, tempFileName, seqdbid)    
        all_ids , seq_hash, seq_lens, short_hash = hash_sequences(filename=tempFileName, short_len=150)
        
        #nothing to do, go to sleep
        if len(all_ids) == 0:
            debug(2, "go to sleep")
            silva_log += "sleep start " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"
            saveStringToFile("silva_summary_log_sleep_" + date_time_str,"sleep started " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S"))
            #continue
            return # insted of sleep, one master file run all scripts
        else:
            for seq_id in all_ids:
                err = dbsequences.AddWholeSeqId(con,cur, seqdbid, seq_id, 'na', noTest = True)
                if err:
                    debug(2, "failed to add dummy")
                    silva_log += "failed to add\n"
                    count_seq_dummy_failure += 1 
                else:
                    debug(2, "add dummy")
                    silva_log += "added\n"
                    count_seq_dummy_success += 1
        
        idx = 0
        num_matches = 0
        
        for cseq, chead in iter_fasta_seqs(silvaFileName):
            isFound = False 
            idx += 1
            if idx % 1000 == 0:
                debug(2, "count: %d"  % idx)
                summary_str = "failed count = %s\nsuccess count = %s\nis exist count = %s\nis exist error = %s\nfailed dummy count = %s\nsuccess dummy count = %s\nis exist dummy count = %s\nis exist dummy error %s\n" % (count_seq_failure,count_seq_success,count_seq_exist,count_seq_is_exist_failure,count_seq_dummy_failure,count_seq_dummy_success,count_seq_dummy_exist,count_seq_dummy_exist)
        
                saveStringToFile("silva_summary_log_" + date_time_str,summary_str)
                saveStringToFile("silva_log_" + date_time_str,silva_log)
        
            for cpos in range(len(cseq) - short_len):
                ccseq = cseq[cpos:cpos + short_len]
                if ccseq in short_hash:
					
                    for k, v in short_hash[ccseq].items():
                        if k in cseq:
                            cid = chead.split(' ')[0]
                            
                            # remove the tail from the id
                            split_cid=cid.split('.') 
                            if len(split_cid) > 2:
                                cid=".".join(split_cid[:-2])
                            else:
                                cid=".".join(split_cid)
                            cid = cid.lower()

                            
                            silva_log += "rec found: seq id %s , db bact id %s, id %s\n" % (seqdbid, v, cid)
                            
                            #check if already exist
                            err, existFlag = dbsequences.WholeSeqIdExists(con,cur, seqdbid, v, cid);
                            if err:
                                count_seq_is_exist_failure += 1 
                                silva_log += "failed to found\n"
                            if existFlag:
                                count_seq_exist += 1
                                silva_log += "found\n"
                                isFound = True
                                break
                            else:
                                debug(2, "add normal")
                                cid = cid.replace('.', '')
                                cid = cid.lower()
                                err = dbsequences.AddWholeSeqId(con,cur, seqdbid, v, cid)
                                if err:
                                    silva_log += "failed to add\n"
                                    count_seq_failure += 1 
                                    break
                                else:
                                    silva_log += "added\n"
                                    count_seq_success += 1
                                    isFound = True
                                    break
        
        
        #go over all ids, if not exist add record
        for seq_id in all_ids:
            err, existFlag = dbsequences.WholeSeqIdExists(con,cur, seqdbid, seq_id)
            if err:
                count_seq_is_exist_dummy_failure += 1 
                silva_log += "failed to found\n"
            if existFlag:
                count_seq_dummy_exist += 1
                silva_log += "found\n"
                isFound = True
                break
            else:
                debug(2, "add dummy")
                err = dbsequences.AddWholeSeqId(con,cur, seqdbid, seq_id, 'na')
                if err:
                    silva_log += "failed to add\n"
                    count_seq_dummy_failure += 1 
                    break
                else:
                    silva_log += "added\n"
                    count_seq_dummy_success += 1
                    break
            
        
        debug(2, 'done')
        
        summary_str = "failed count = %s\nsuccess count = %s\nis exist count = %s\nis exist error = %s\nfailed dummy count = %s\nsuccess dummy count = %s\nis exist dummy count = %s\nis exist dummy error %s\n" % (count_seq_failure,count_seq_success,count_seq_exist,count_seq_is_exist_failure,count_seq_dummy_failure,count_seq_dummy_success,count_seq_dummy_exist,count_seq_dummy_exist)
        
        saveStringToFile("silva_summary_log_" + date_time_str,summary_str)
        saveStringToFile("silva_log_" + date_time_str,silva_log)
    