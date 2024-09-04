#!/usr/bin/env python3
import sys
import os
import requests
import json

#def siteLifeStatus (site='T2_US_Florida', dbid=9475, gte="now-6h/h",lt="now") :
def siteLifeStatus (site='T2_US_Florida', what='sts15min', dbid=9980, gte="now-23h/h",lte="now") :
    '''
    gets a site life status during last 2 hours
    '''
    url = "https://monit-grafana.cern.ch/api/datasources/proxy/"+str(dbid)+"/_msearch"
    index_name = "monit_prod_cms_raw_aaa-ng*"       # XRD Collector Monitoring
    index_name = "monit_prod_cmssst_*"              # 9475 Site Status
    index_name = "monit_prod_cmssst_raw_ssbmetric-*"              # 9980 Site Status    
    payload_index_props = {
        "search_type": "query_then_fetch",
        "index": [ index_name ],
        "ignore_unavailable":True
    }
    payload_query = {
      "query": {
        "bool": {
          "must": [
            {
              "match_phrase": {
                "metadata.type": "ssbmetric"
              }
            },
            {
              "match_phrase": {
                "metadata.type_prefix": "raw"
              }
            },
            {
              "match_phrase": {
                "metadata.monit_hdfs_path": "sts15min"
              }
            }
          ],
          "filter": {
            "range": {
              "metadata.timestamp": {
                "gte": "===START_TIME===",
                "lt": "===END_TIME===",
                "format": "epoch_second"
              }
            }
          }
        }
      },
      "_source": {
        "includes": [
          "metadata.timestamp",
          "metadata.kafka_timestamp",
          "data.name",
          "data.status"
        ]
      },
      "size": 10000,
      "sort": [
        { "metadata.timestamp": "desc" }
      ]
    }
    payload_query["query"]["bool"]["filter"]["range"]["metadata.timestamp"]["gte"] = gte
    payload_query["query"]["bool"]["filter"]["range"]["metadata.timestamp"]["lt"] = lte
    # down15min or sts15min
    payload_query["query"]["bool"]["must"][2]["match_phrase"]["metadata.monit_hdfs_path"] = what
    #print(payload_query)
    payload = json.dumps(payload_index_props) + " \n" + json.dumps(payload_query) + "\n"
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer {}'.format(os.environ["GRAFANA_VIEWER_TOKEN"])
    }
    result = requests.request("POST", url, headers=headers, data = payload).json()
    

    #print ( 'Number of Responses ', len ( result["responses"] ) )
    response = result["responses"][0] 
    #print ( 'Total hits ',response['hits']['total']['value'] )
    siteStatus={}
    #print ( type ( response['hits']['hits'] ) )
    for hit in response['hits']['hits'] :
        #print ("Site ",hit['_source']['data']['name'], " Status ",hit['_source']['data']['status'])
        siteStatus[hit['_source']['data']['name']] = hit['_source']['data']['status']
    return siteStatus[site]

if __name__ == "__main__":
   if len(sys.argv) > 2 :
      site = sys.argv[1]
      what = sys.argv[2]
      status = siteLifeStatus(site=site, what=what)
      print (status)
      sys.exit(0)
   if len(sys.argv) > 1 :
      site = sys.argv[1]
      status = siteLifeStatus(site=site)
      print (status)
      sys.exit(0)
   status = siteLifeStatus()
   print (status)


