import requests, json, os
def siteLifeStatus (site='T2_US_Florida', dbid=9475, gte="now-2h/h",lt="now") :
    '''
    gets a site life status during last 2 hours
    '''
    url = "https://monit-grafana.cern.ch/api/datasources/proxy/"+str(dbid)+"/_msearch"
    index_name = "monit_prod_cms_raw_aaa-ng*"       # XRD Collector Monitoring
    index_name = "monit_prod_cmssst_*"              # Site Status
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
    payload_query["query"]["bool"]["filter"]["range"]["metadata.timestamp"]["lt"] = lt
    #print(payload_query)
    payload = json.dumps(payload_index_props) + " \n" + json.dumps(payload_query) + "\n"
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer {}'.format(os.environ["GRAFANA_VIEWER_TOKEN"])
    }
    result = requests.request("POST", url, headers=headers, data = payload).json()
    

    #print ( 'Number of Responses ', len ( result["responses"] ) )
    response = result["responses"] 
    #print ( 'Total hits ',r['hits']['total']['value'] )
    siteStatus={}
    for hit in r['hits']['hits'] :
        #print ("Site ",hit['_source']['data']['name'], " Status ",hit['_source']['data']['status'])
        siteStatus[hit['_source']['data']['name']] = hit['_source']['data']['status']
    return siteStatus[site]

