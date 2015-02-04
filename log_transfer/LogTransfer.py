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

def getFileInfo(fileDir,fileInfo):
    """
    returns an object with file's LFN, size and checksum
    """
    file = {}
    elements = fileInfo.split()
    file['name'] = '%s/%s' % (fileDir, elements[-1])
    file['size'] = elements[4] 
    if len(elements) == 11:
        file['checksum'] = elements[9]
    else:
        file['checksum'] = None
    return file

def createXML(dsName, fileDir, fileList):
    xml = []
    xml.append('<data version="2.0">')
    xml.append(' <dbs name="Log_Files" dls="dbs">')
    xml.append('  <dataset name="%s" is-open="y" is-transient="n">' % dsName)
    xml.append('   <block name="%s#01" is-open="n">' % dsName)

    for fileInfo in fileList.splitlines():
        # using nsls output, get file's lfn, size and checksum
        file = getFileInfo(fileDir,fileInfo)
        # if checksum is missing do not add it to xml
        if file['checksum']:
            xml.append('    <file name="%s" bytes="%s" checksum="adler32:%s"/>' % (file['name'],file['size'],file['checksum']))
        else:
            xml.append('    <file name="%s" bytes="%s"/>' % (file['name'],file['size']))
    xml.append('   </block>')
    xml.append('  </dataset>')
    xml.append(' </dbs>')
    xml.append('</data>')
    return ''.join(xml)

def getAlreadyInjectedDatasets():
    """
    returns log datasets already injected to PhEDEx
    """
    urlReplica = urlPhedex + 'blockreplicas?dataset=/Log%s/%s/*' % (year,month)
    result = json.loads(request.send(urlReplica))
    injectedDatasets = set()
    for block in result['phedex']['block']:
        injectedDatasets.add(block['name'].split('#')[0])
    return injectedDatasets


if __name__ == '__main__':
    # Get request object for future PhEDEx calls
    request = Request()

    # get list of datasets injected before
    Logger.log('retrieving list of injected datasets in %s/%s' % (year,month))
    injectedDatasets = getAlreadyInjectedDatasets()
    Logger.log('number of injected datasets: %s' % len(injectedDatasets))

    #list log directories on CASTOR
    Logger.log('listing directories under %s' % logCastorPath)
    cmd = 'nsls %s' % logCastorPath
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outDirs,errDirs = process.communicate()

    if errDirs:
        Logger.log('Failed to list directory, exiting now reason: %s' % errDirs)
        sys.exit(1)

    for WFName in outDirs.splitlines():
        WFName = WFName.rstrip()
        dsName = '/Log%s/%s/%s' % (year,month,WFName)

        # if dataset was already injected skip
        if dsName in injectedDatasets:
            continue

        # list log files in the directory
        castorDir = ' %s/%s' % (logCastorPath, WFName)
        Logger.log('listing files under       %s' % castorDir)
        cmd2 = 'nsls -l --checksum %s' % castorDir
        proc2 = subprocess.Popen(cmd2.split(),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outFiles,errFiles = proc2.communicate()

        # if failed to list files, skip to the next folder
        if errFiles:
            Logger.log('Failed listing files reason: %s' % errFiles)
            continue

        # if no error, create xml data for injection&subscription
        Logger.log('Creating xml file for injection')
        LFNDir = '%s/%s' % (pathBaseLFN, WFName)
        xmlData = createXML(dsName,LFNDir,outFiles)


        # inject data
        Logger.log("Injecting to CASTOR: %s" %dsName)
        data = request.send(urlInject, {'data':xmlData,'node':'T0_CH_CERN_Export'})
        if data:
            # subscribed it so that transfer can start from CASTOR to EOS
            Logger.log("Subscribing at EOS : %s" % dsName)
            request.send(urlSubscribe, {'data':xmlData,'node':'T2_CH_CERN','group':'transferops','no_mail':'y','comments':'auto-approved log transfer from CASTOR to EOS'})
        else:
            Logger.log('Skipping subscription since injection got failed')

        break
