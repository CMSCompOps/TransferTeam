import sys,getopt,urllib,os,time

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["input="])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options'
    sys.exit(2)

inputFile=None
# check command line parameter
for opt, arg in opts :
    if opt == "--input" :
        inputFile = arg

def getValue(dict,key):
    if key not in dict:
        dict[key] = {}
    return dict[key]

# datasets = {dataset1:[{block1:[file:]}],dataset2:[]}
datasets = {}
with open(inputFile, 'r') if inputFile != None else sys.stdin as file:
    for line in file:
        line = line.rstrip()

        block,file,cksum,adler32,size = line.split(' ')
        dataset = block.split('#')[0]

        blocks = getValue(datasets,dataset)

        if block not in blocks:
            blocks[block] = []

        blocks[block].append({'lfn':file,'size':size,'cksum':cksum,'adler32':adler32})

closeDataset=False
closeBlock=False
print '<data version="2.0">'
print ' <dbs name="https://cmsweb.cern.ch/dbs/prod/global/DBSReader" dls="dbs">'

for dataset in datasets:
    print '  <dataset name="%s" is-open="y" is-transient="n">' % dataset
    for block in datasets[dataset]:
        print '   <block name="%s" is-open="n">' % block
        for file in datasets[dataset][block]:
            print '    <file name="%s" bytes="%s" checksum="adler32:%s,cksum:%s"/>' % (file['lfn'], file['size'], file['adler32'], file['cksum'])
        print '   </block>'
    print '  </dataset>'

print ' </dbs>'
print '</data>'
