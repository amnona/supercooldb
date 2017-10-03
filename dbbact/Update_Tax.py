from utils import debug, SetDebugLevel
import db_access
import dbsequences
import dbuser
import os
import time
import datetime
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
    
    rank_list = []
    rank_list.append("rootrank")
    rank_list.append("life")
    rank_list.append("domain")
    rank_list.append("kingdom")
    rank_list.append("phylum")
    rank_list.append("class")
    rank_list.append("order")
    rank_list.append("family")
    rank_list.append("genus")
    rank_list.append("species")
    
    count_success = 0
    count_failure = 0
    count_seq_success = 0
    count_seq_failure = 0
    count = 1
    tax_log = ""
    rdp_exe_location = "rdp_classifier_2.12/"
    sleep_time = 86400
        
    while isFileExist("stop") == False:
        removeFile("%sinput" %  rdp_exe_location)
        removeFile("%soutput" %  rdp_exe_location)
        
        err, seq_id = dbsequences.GetSequenceWithNoTaxonomyID(con, cur)
        if err or seq_id == -1:
            #If no empty sequence, wait for long time
            time.sleep(sleep_time)
        
        tax_log += "sequence id = " + str(seq_id) + "\n"
        
        err, seq_str = dbsequences.GetSequenceStrByID(con, cur, seq_id)
        if err:
            tax_log += "Fatal Error, could not find sequence " + "\n"
            break
        
        
        #java -Xmx1g -jar dist/classifier.jar classify  -o output_filename example.fasta
        input_file_name = "%sinput" %  rdp_exe_location
        output_file_name = "%soutput" %  rdp_exe_location
        
        #get the taxononmy for specific sequence
        createSeqFile(input_file_name,seq_str)
        os.system("java -Xmx1g -jar %sdist/classifier.jar classify  -o %s %s" % (rdp_exe_location,output_file_name,input_file_name))
        tex_res = readResultFromFile(output_file_name)
        
        tax_log += "the data:\n"
        for line in tex_res:
            tax_log += line + "\n"
            data = line.split('\t')
            
        
        #search for the string
        prev = ""
        has_failure = False
        
        size_of_list = len(data)
        
        list_index = 0
        while list_index < size_of_list:
            has_failure = False
            curr_val = data[list_index]
            curr_val = curr_val.replace("\"", "")
            curr_val = curr_val.replace("\n", "")
            
            for y in rank_list:
                if curr_val == y:
                    tax_log += curr_val + " = " +  prev 
                    if list_index > 0 & list_index < (size_of_list - 1):
                        # keep the next and previous value    
                        prev_val = data[list_index - 1]
                        next_val = data[list_index + 1]
                        #remove unnecesary characters
                        prev_val = prev_val.replace("\"", "")
                        prev_val = prev_val.replace("\n", "")
                        next_val = next_val.replace("\"", "")
                        next_val = next_val.replace("\n", "")
                        
                        if( float(next_val) >= 0.9 ):
                            # Add to DB
                            if dbsequences.AddSequenceTax(con, cur, seq_id, "tax" + curr_val, prev_val) == True:
                                tax_log += " SUCCESS" + "\n"
                                count_seq_success = count_seq_success + 1
                            else:
                                tax_log += " FAILED" + "\n"
                                count_seq_failure = count_seq_failure + 1
                                has_failure = True
                        else:
                            tax_log += " FAILED (low probablility)" + "\n"
                    else:
                        tax_log += " FAILED (bad index)" + "\n"
                        
            list_index = list_index + 1
            
        if has_failure == True:
            count_failure = count_failure + 1
        else:
            count_success = count_success + 1
        
        
        summary_str = "count_success = %s\ncount_failure = %s\ncount_seq_success = %s\ncount_seq_failure = %s\n" % (count_success,count_failure,count_seq_success,count_seq_failure)
        
        saveStringToFile("tax_summary_log_" + date_time_str,summary_str)
        saveStringToFile("tax_log_" + date_time_str,tax_log)
        debug(2, 'found sequence %s' % seq_str)
        debug(2, 'return %s' % tex_res)
        count = count + 1
        
        #stop the script in case of error
        if count_failure > 0:
            break;
