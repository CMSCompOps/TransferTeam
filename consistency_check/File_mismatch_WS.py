import urllib.request as request
import urllib
import json
import requests
import os
import pandas
from pandas.io.json import json_normalize
from bs4 import BeautifulSoup as soup 
#import urllib.request.urlopen as uReq
import warnings
warnings.filterwarnings('ignore')

class x509RESTSession(object):
    datasvc = "https://cmsweb.cern.ch/phedex/datasvc/json/prod"
    datasvc_xml = "https://cmsweb.cern.ch/phedex/datasvc/xml/prod"

    def __init__(self):
        self._session = requests.Session()
        home = os.path.expanduser('~/')
        # $ openssl rsa -in userkey_protected.pem -out userkey.pem; chmod 0600 userkey.pem
        self._session.cert = (home+'.globus/usercert.pem', home+'.globus/userkey2.pem')
        self._session.verify = os.getenv('X509_CERT_DIR')
    
    def data(self, dataset):
        res = self._session.get("%s/data" % self.datasvc, params={'dataset': dataset})
        resjson = json.loads(res.content)
        out = []
        for _instance in resjson["phedex"]["dbs"]:
            for _dataset in _instance["dataset"]:
                for _block in _dataset["block"]:
                    for _file in _block["file"]:
                        out.append(
                            {
                                "Dataset": _dataset["name"],
                                "File_name": _file["lfn"],
                                "File_checksum": _file["checksum"]
                                
                            }
                        )
        df = pandas.io.json.json_normalize(out)
        return df
        #format_dates(df, ["Time_file_was_created", "Time_block_was_created"])
    
    def dbsinfo(self, dataset):
        
        res = self._session.get("https://cmsweb.cern.ch/dbs/prod/global/DBSReader/files?detail=1&dataset="+dataset)
        resjson = json.loads(res.content)
        out = []
        for _instance in resjson:
            out.append(
                            {
                                "Dataset": _instance["dataset"],
                                "Is_valid": _instance["is_file_valid"],
                                "File_name": _instance["logical_file_name"],
                                "File_checksum": _instance["check_sum"],
                                "last_modified_by": _instance ["last_modified_by"]
                                
                            }
                        )
            
        df = pandas.io.json.json_normalize(out)
        return df
    
    def load_html(self, url):
        uClient = request.urlopen(url)
        web_site = uClient.read()
        uClient.close()
        page = soup(web_site, "html.parser")
        return page
    
    def jsonmethod(self, method, **params):
        return self.getjson(url=self.jsonurl.join(method), params=params)

def get_datasets(web):
    datasets = []
    for table in web.findAll('table'):
        tr = table.findAll('tr')
        for i in range(len(tr)):
            if i > 0:
                casilla = tr[i].findAll('td')
                if (len(casilla[0].findAll('a')) > 0):
                    datasets.append(str(casilla[1].text))
                else:
                    datasets.append(str(casilla[0].text))
    return datasets

def main(sesion, web):
    datasets = get_datasets(web)
    print(datasets)
    print(len(datasets))
    invalidate_in_phedex = []
    invalidate_in_dbs = []
    dataset_empty_dbs = []
    dataset_empty_phedex = []
    for _dataset in datasets:
        phedex = sesion.data(dataset = _dataset)
        dbs = sesion.dbsinfo(dataset = _dataset)
        if dbs.empty or phedex.empty:
            if dbs.empty:
                dataset_empty_dbs.append(_dataset)
            if phedex.empty:
                dataset_empty_phedex.append(_dataset)
        else:
            dbs_valid = dbs.loc[dbs['Is_valid'] == 1]
            if len(phedex['File_name']) == len(dbs_valid['File_name']):
                pass
            elif len(phedex['File_name']) > len(dbs_valid['File_name']):
                invalidated_in_dbs_by_unified = dbs.loc[dbs['last_modified_by'].str.contains('unified')]
                invalidated_in_dbs_by_unified = invalidated_in_dbs_by_unified.loc[invalidated_in_dbs_by_unified['Is_valid'] == 0]
                phedex['invalidated_by_unified_in_dbs'] = phedex["File_name"].isin(invalidated_in_dbs_by_unified["File_name"])
                array = phedex.loc[phedex["invalidated_by_unified_in_dbs"] == True, 'File_name'].to_numpy()
                for i in range(len(array)):
                    invalidate_in_phedex.append(array[i])
            elif len(phedex['File_name']) < len(dbs_valid['File_name']):
                dbs_valid["in_phedex"] = dbs_valid["File_name"].isin(phedex["File_name"])
                array = dbs_valid.loc[dbs_valid["in_phedex"] == False, 'File_name'].to_numpy()
                for i in range(len(array)):
                    invalidate_in_dbs.append(array[i])
    with open('invalidate_in_dbs.txt', 'w') as f:
        for item in invalidate_in_dbs:
            f.write("%s\n" % item)
    with open('invalidate_in_phedex.txt', 'w') as f:
        for item in invalidate_in_phedex:
            f.write("%s\n" % item)
    with open('dataset_empty_dbs.txt', 'w') as f:
        for item in dataset_empty_dbs:
            f.write("%s\n" % item)  
    with open('dataset_empty_phedex.txt', 'w') as f:
        for item in dataset_empty_phedex:
            f.write("%s\n" % item)
    
if __name__ == '__main__':
    sesion = x509RESTSession()
    web_info = sesion.load_html(url='https://cms-unified.web.cern.ch/cms-unified/assistance.html')
    main(sesion, web_info)
