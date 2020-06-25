import os
import warnings
warnings.filterwarnings('ignore')

def file_read(fname):
        content_array = []
        with open(fname) as f:
                for line in f:
                        content_array.append(line)
                return content_array

def which_to_invalidate_in_dbs(fname):
    invalidate = []
    files = file_read(fname)
    for line_ in range(len(files)):
        os.system("xrdfs cms-xrd-global.cern.ch locate -d -m "+line_+" > aux.txt")
        sites = file_read("aux.txt")
        if sites[0] == "[FATAL] Redirect limit has been reached":
            invalidate.append(line_)
    print(invalidate)
    return invalidate

def main(list_of_files):
        print('Files will be invalidated in DBS', list_of_files)

if __name__ == '__main__':

    list_of_files = which_to_invalidate_in_dbs('invalidate_in_dbs.txt')
    main(list_of_files)
    
