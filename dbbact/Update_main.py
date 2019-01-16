#!/usr/bin/env python

import sys
import os

import time
import datetime
from pathlib import Path

from Update_Gg import main_func_gg
from Update_Silva import main_func_silva
from Update_Tax import main_func_tax
from Update_Seq_Hash import main_func_seq_hash

from dbbact.utils import debug, SetDebugLevel

sys.path.append(os.getcwd())

sleep_time = 86400
#sleep_time = 10 # Debug

def isFileExist(fileName):
    my_file = Path(fileName)
    if my_file.is_file():
        # file exists
        return True
    return False

def removeFile(file_name):
    try:
        os.remove(file_name)
    except OSError:
        pass 

def saveStringToFile(file_name,content_str):
    with open(file_name, "w") as text_file:
        text_file.write(content_str)        

if __name__ == '__main__':
    sys.path.insert(0, '/Users/admin/supercooldb')
    sys.path.insert(0, '/home/eitano/supercooldb')

    SetDebugLevel(0)
    date_time_str = datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
    maint_log = ""
    summary_str = ""
    #remove stop files
    removeFile("stop")
    removeFile("stop_gg")
    removeFile("stop_silva")
    removeFile("stop_tax")
    removeFile("stop_seq_hash")

    while isFileExist("stop") == False:
 		#Update GG
        summary_str = "GG script started at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"
        main_func_gg()
        summary_str += "GG script ended at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"

 		#Update silva
        summary_str += "Silva script started at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"
        main_func_silva()
        summary_str += "Silva script ended at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"

 		#Update tax
        summary_str += "Tax script started at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"
        main_func_tax()
        summary_str += "Tax script ended at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"        

 		#Update hash for sequence
        summary_str += "Seq hash script started at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"
        main_func_seq_hash()
        summary_str += "Seq hash script ended at :  " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"        

        summary_str += "Sleep sleep at: " + datetime.datetime.now().strftime("%Y-%m-%d--%H:%M:%S") + "\n"

        maint_log += summary_str
 		##summary_str = "failed count = %s\nsuccess count = %s\nis exist count = %s\nis exist error = %s\nfailed dummy count = %s\nsuccess dummy count = %s\nis exist dummy count = %s\nis exist dummy error %s\n" % (count_seq_failure,count_seq_success,count_seq_exist,count_seq_is_exist_failure,count_seq_dummy_failure,count_seq_dummy_success,count_seq_dummy_exist,count_seq_dummy_exist)
        saveStringToFile("maint_summary_log_" + date_time_str,summary_str)
        saveStringToFile("maint_log_" + date_time_str,maint_log)
        
        #Sleep until the next time
        time.sleep(sleep_time)


saveStringToFile("maint_summary_log_" + date_time_str,summary_str)
saveStringToFile("maint_log_" + date_time_str,maint_log)
