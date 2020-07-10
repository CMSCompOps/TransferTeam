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
    for line_ in files:
        line_ = line_[:-1]
        os.system("xrdfs cms-xrd-global.cern.ch locate -d -m "+line_+" > aux.txt")
        sites = file_read("aux.txt")
	#:print(sites[0])
        if len(sites) == 0:
            invalidate.append(line_)
    return invalidate

def main(list_of_files_): 
    with open('Invalidate_in_DBS.txt', 'w') as f:
        for item in list_of_files_:
            f.write("%s\n" % item)
    
if __name__ == '__main__':

    list_of_files = which_to_invalidate_in_dbs('check_in_dbs.txt')
    main(list_of_files)
    print(list_of_files)
