from utils import debug, SetDebugLevel
import db_access
import dbsequences
import dbuser
import os
import time
import datetime
import hashlib
from pathlib import Path


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
    count = 1
    hash_log = ""
    sleep_time = 86400
    
    hash_seq_full = ''
    hash_seq_150 = ''
    hash_seq_100 = ''
    
    while isFileExist("stop") == False:
        
        err, seq_id = dbsequences.GetSequenceWithNoHashID(con, cur)
        if err or seq_id == -1:
            #If no empty sequence, wait for long time
            time.sleep(sleep_time)
        
        hash_log += "sequence id = " + str(seq_id) + "\n"
        
        err, seq_str = dbsequences.GetSequenceStrByID(con, cur, seq_id)
        if err:
            tax_log += "Fatal Error, could not find sequence " + "\n"
            break
        
        hash_seq_full = 'na'
        hash_seq_150 = 'na'
        hash_seq_100 = 'na'
        
        seq_str = seq_str.upper()
        
        if len(seq_str) > 0  :
            hash_seq_full = hashlib.md5(seq_str.encode('utf-8')).hexdigest()
        
        if len(seq_str) >= 150 :
            hash_seq_150 = hashlib.md5(seq_str[:150].encode('utf-8')).hexdigest()
            
        if len(seq_str) >= 100  :
            hash_seq_100 = hashlib.md5(seq_str[:100].encode('utf-8')).hexdigest()
            
        
        hash_log += "id: " + str(seq_id) + "\n"
        hash_log += "hash: " + str(hash_seq_full) + "\n"
        hash_log += "hash 150: " + str(hash_seq_150) + "\n"
        hash_log += "hash 100: " + str(hash_seq_100) + "\n"
        
        has_failure = False
        if dbsequences.UpdateHash(con, cur, seq_id,hash_seq_full,hash_seq_150,hash_seq_100) == True:
            hash_log += " SUCCESS" + "\n"
            count_seq_success = count_seq_success + 1
        else:
            hash_log += " FAILED" + "\n"
            count_seq_failure = count_seq_failure + 1
            has_failure = True
                        
            
        if has_failure == True:
            count_failure = count_failure + 1
        else:
            count_success = count_success + 1
        
        
        summary_str = "count_seq_success = %s\ncount_seq_failure = %s\n" % (count_seq_success,count_seq_failure)
        
        saveStringToFile("hash_summary_log_" + date_time_str,summary_str)
        saveStringToFile("hash_log_" + date_time_str,hash_log)
        debug(2, 'found sequence %s' % seq_str)
        debug(2, 'return %s,%s,%s' % (hash_seq_full,hash_seq_150,hash_seq_100))
        count = count + 1
        
        #stop the script in case of error
        if count_failure > 0:
            break;
