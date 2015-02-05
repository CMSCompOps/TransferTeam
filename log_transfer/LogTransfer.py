#!/usr//bin/python
import sys,subprocess,getopt
from Common import Request
from Common import Logger
try: import json
except ImportError: import simplejson as json

year=None
month=None

try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["year=","month="])
except getopt.GetoptError:
    print  >> sys.stderr, 'Failed to parse options!'
    sys.exit(2)

# check parameters
for opt, arg in opts :
    if opt == "--year":
        year = arg
    elif opt == "--month":
        month = arg
        if len(month) == 1:
            month = "0" + month

if year == None or month==None:
    print  >> sys.stderr, 'Please specify --year and --month options'
    sys.exit(2)


pathBaseLFN = '/store/logs/prod/%s/%s/WMAgent' % (year,month)
logCastorPath = '/castor/cern.ch/cms' + pathBaseLFN 

urlPhedex = 'https://phedex-dev.cern.ch/phedex/datasvc/json/ops/'
urlInject = urlPhedex + 'inject'
urlSubscribe = urlPhedex + 'subscribe'
#urlPhedex = 'https://cmsweb.cern.ch/phedex/datasvc/json/dev/'

def getDatasetName(WFName):
    return '/Log%s/%s/%s' % (year,month,WFName)

def getLFN(WFName,fileName):
    return '%s/%s/%s' % (pathBaseLFN, WFName, fileName)

def getFileInfo(line):
    """
    returns an object with file's LFN, size and checksum
    """
    file = {}
    elements = line.split()
    file['name'] = elements[-1]
    file['size'] = elements[4]
    if len(elements) == 11:
        file['checksum'] = elements[9]
    else:
        file['checksum'] = None
    return file

def createXML(WFName, fileInfoList):
    dsName = getDatasetName(WFName)
    xml = []
    xml.append('<data version="2.0">')
    xml.append(' <dbs name="Log_Files" dls="dbs">')
    xml.append('  <dataset name="%s" is-open="y" is-transient="n">' % dsName)
    xml.append('   <block name="%s#01" is-open="y">' % dsName)

    for file in fileInfoList:
        fileLFN = getLFN(WFName,file['name'])
        # if checksum is missing do not add it to xml
        if not file['checksum']:
            Logger.log('skipping file without checksum: %s' % fileLFN)
            continue
        xml.append('    <file name="%s" bytes="%s" checksum="adler32:%s"/>' % (fileLFN,file['size'],file['checksum']))

    xml.append('   </block>')
    xml.append('  </dataset>')
    xml.append(' </dbs>')
    xml.append('</data>')
    return ''.join(xml)

def getAlreadyInjectedFiles():
    """
    returns log files already injected to PhEDEx
    """
    urlReplica = urlPhedex + 'filereplicas?dataset=/Log%s/%s/*' % (year,month)
    result = json.loads(request.send(urlReplica))
    injectedFiles = set()
    for block in result['phedex']['block']:
        for file in block['file']:
            injectedFiles.add(file['name'])
    return injectedFiles


if __name__ == '__main__':
    # Get request object for future PhEDEx calls
    request = Request()

    # get list of datasets injected before
    Logger.log('retrieving list of injected files in %s/%s' % (year,month))
    injectedFiles = getAlreadyInjectedFiles()
    Logger.log('number of already injected files: %s' % len(injectedFiles))

    #list log directories on CASTOR
    Logger.log('listing files under %s' % logCastorPath)
    cmd = 'nsls -lR --checksum %s' % logCastorPath
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outDirs,errDirs = process.communicate()

    if errDirs:
        Logger.log('Failed to list directory, exiting now reason: %s' % errDirs)
        sys.exit(1)

    Logger.log('listing is completed, parsing the output')
    WFList = {}
    currentWF = None
    #collect info from castor
    for line in outDirs.splitlines():
        line = line.strip()
        # skip empty lines in the output
        if len(line) == 0:
            continue

        # if directory, add it to the list key
        if line.startswith('/'):
            line = line.strip(':')
            # skip the root dir
            if line == logCastorPath:
                continue

            line = line.split('/')[-1]
            WFList[line] = []
            # it will be used in the next iteration while adding files in the dictionary
            currentWF = line
        # if file, add it to its dir's list
        elif not line.startswith('d'):
            # using nsls output, get file's lfn, size and checksum
            fileInfo = getFileInfo(line)
            fileLFN = getLFN(currentWF, fileInfo['name'])
            if fileLFN not in injectedFiles:
                WFList[currentWF].append(fileInfo)


    for WFName in WFList:
        dsName = getDatasetName(WFName)
        fileInfoList = WFList[WFName]

        # no file to inject for the dataset
        if not fileInfoList:
            continue

        # create xml data for injection&subscription
        Logger.log('Creating xml file for injection')
        xmlData = createXML(WFName, fileInfoList)

        # inject data
        Logger.log("Injecting to CASTOR: %s" %dsName)
        data = request.send(urlInject, {'data':xmlData,'node':'T0_CH_CERN_Export'})
        if data:
            # subscribed it so that transfer can start from CASTOR to EOS
            Logger.log("Subscribing at EOS : %s" % dsName)
            request.send(urlSubscribe, {'data':xmlData,'node':'T2_CH_CERN','group':'transferops','no_mail':'y','comments':'auto-approved log transfer from CASTOR to EOS'})
        else:
            Logger.log('Skipping subscription since injection got failed')
