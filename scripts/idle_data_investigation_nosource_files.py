from urllib2 import Request, urlopen
import ssl
import json
import pandas as pd
from pandas.io.json import json_normalize
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime, timedelta
import re

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)



def search_nosource_files(block):
    '''
    serch replicas for a given block and return the files that have no replica at all "[]" in replica field. The returned value is a panda data frame
    '''
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas'
    params = {"block": block}
    replicas_info = requests.get(url=url, params= params, verify=False).content
    replicas_json = json.loads(replicas_info)
    replicas_table = json_normalize(replicas_json['phedex']['block'][0]['file'])
    num_files_in_block = len(replicas_table)
    no_source_files_table = replicas_table.loc[replicas_table.astype(str)['replica'] == "[]"]
    num_nosource_files_in_block = len(no_source_files_table)
    return { 'df': no_source_files_table, 'num_files_in_block': num_files_in_block, 'num_nosource_files_in_block': num_nosource_files_in_block }

def site_nosource_files_df(site):
    '''
    check the data service blockarrive for blocks with status basis = -6
    basis -6 means: at least one file in the block has no source replica remaining
    having those
    '''
    url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockarrive"
    params = {"to_node": site}
    block_arrive_info = requests.get(url=url, params= params, verify=False).content


    block_arrive_info_json = json.loads(block_arrive_info)
    blocks_arrive_table = json_normalize(block_arrive_info_json['phedex']['block'])
    block_arrive_destination_df = pd.DataFrame()

    for i in range(len(blocks_arrive_table)):
        destination_info = json_normalize(block_arrive_info_json['phedex']['block'][i]['destination'])
        block_arrive_destination_df = block_arrive_destination_df.append(destination_info)
    block_arrive_destination_df.index = range(len(blocks_arrive_table))

    block_arrive_whole_table = pd.concat([blocks_arrive_table,block_arrive_destination_df], axis=1)
    #Blocks with -6 basis
    blocks_with_nosource_files = block_arrive_whole_table.loc[block_arrive_whole_table['basis'] == -6]['name']
    blocks_with_nosource_files = blocks_with_nosource_files.iloc[:, 0]
    blocks_with_nosource_files = blocks_with_nosource_files.tolist()

    nosource_files_site_df = pd.DataFrame()
    blocks_info = pd.DataFrame()
    for i in blocks_with_nosource_files:
        nosource_files_info = search_nosource_files(i)
        nosource_files_df = nosource_files_info['df']
        nosource_files_df['block'] = i
        nosource_files_site_df = nosource_files_site_df.append(nosource_files_df, ignore_index=True)
        df_tmp = pd.DataFrame(data= [[i, nosource_files_info['num_files_in_block'], nosource_files_info['num_nosource_files_in_block']]])
        blocks_info = blocks_info.append(df_tmp)

    nosource_files_site_df['dataset'] = nosource_files_site_df['block'].apply(dataset_from_blockname)
    blocks_info['dataset'] = blocks_info.iloc[:, 0].apply(dataset_from_blockname)
    blocks_info.columns = ['block', 'num_files_in_block', 'num_nosource_files_in_block', 'dataset']
    #print(nosource_files_site_df)
    nosource_files_site_df['datetime_create'] = nosource_files_site_df['time_create'].apply(datetime.fromtimestamp)
    nonosource_files_site_size = nosource_files_site_df['bytes'].sum()
    num_files = len(nosource_files_site_df)
    print(site + " has " + str(num_files) + " no source files. Total size related to them: " + str(nonosource_files_site_size * (10**(-12))) + " TB")
    return {'df': nosource_files_site_df, 'block_names': blocks_with_nosource_files, 'blocks_info': blocks_info}


def write_nosource_files_site (site, file_type, list_files):
    filename = "nosource_files_" + file_type + "_" + site + ".txt"

    with open(filename, "w") as f:
        f.write("\n".join(list_files))

def write_nosource_block_list (site, file_type, list_blocks):
    filename = "nosource_blocks_" + file_type + "_" + site + ".txt"

    with open(filename, "w") as f:
        f.write("\n".join(list_blocks))

def write_nosource_dataset_list (site, file_type, list_datasets):
    filename = "nosource_datasets_" + file_type + "_" + site + ".txt"

    with open(filename, "w") as f:
        f.write("\n".join(list_datasets))

def write_deletions_json (site, deletions_json_list):
    filename = "nosource_blocks_deletions_jsons" + site + ".txt"

    with open(filename, "w") as f:
        deletions_json_list = map(str, deletions_json_list)
        f.write("\n".join(deletions_json_list))

def search4deletions (block):
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/deletions'
    params = {"block": block}
    deletions_info = requests.get(url=url, params= params, verify=False).content
    deletions_json = json.loads(deletions_info)
    return(deletions_json)
    #replicas_table = json_normalize(deletions_json['phedex']['block'][0]['file'])
    #no_source_files_table = replicas_table.loc[replicas_table.astype(str)['replica'] == "[]"]

def dataset_from_blockname(blockname):
    return re.search('(.+)#', blockname).group(1)


def datasets_count_hash(blocks_file_list):
    datasets_count = {}
    for i in blocks_file_list:
        dataset = dataset_from_blockname(str(i))
        datasets_count[dataset] = datasets_count.get(dataset, 0) + 1
    return datasets_count


def num_blocks(dataset):
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockreplicas'
    params = {"dataset": dataset}
    replicas_info = requests.get(url=url, params= params, verify=False).content
    replicas_json = json.loads(replicas_info)
    replicas_table = json_normalize(replicas_json['phedex']['block'])
    return len(replicas_table)

num_blocks('/BTagCSV/Run2016BBackfill-BACKFILL-v13/MINIAOD')


def num_files(dataset):
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas'
    params = {"dataset": dataset}
    replicas_info = requests.get(url=url, params= params, verify=False).content
    replicas_json = json.loads(replicas_info)
    blocks_level_table = json_normalize(replicas_json['phedex']['block'])
    replicas_table = pd.DataFrame()

    for i in range(len(blocks_level_table)):
        replicas_info = json_normalize(replicas_json['phedex']['block'][i]['file'])
        replicas_table = replicas_table.append(replicas_info)
    return len(replicas_table)

def dataset_isdata(dataset):
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas'
    params = {"dataset": dataset}
    replicas_info = requests.get(url=url, params= params, verify=False).content
    replicas_json = json.loads(replicas_info)
    replicas_sample_table = json_normalize(replicas_json['phedex']['block'][0]['file'])
    return (str(replicas_sample_table['name'][0]).split("/")[2])

def check_datetime_Xweeks_older (timestamp, nweeks):
    time_limit = datetime.now() - timedelta(weeks=nweeks)
    return datetime.fromtimestamp(timestamp) <= time_limit

def check_filetype (filepath, file_type):
    return bool(re.search('^/store/' + file_type, filepath))



def main():

    sites = [
        "T1_US_FNAL_Disk",
        "T2_CH_CERN",
        "T1_RU_JINR_Disk"
    ]

    for site in sites:
        #site = "T1_US_FNAL_Disk"
        nosite_nosource_files = site_nosource_files_df(site)
        nosource_files_site_df = nosite_nosource_files['df']
        nosource_files_site_df = nosource_files_site_df[nosource_files_site_df['time_create'].apply(check_datetime_Xweeks_older, nweeks=1) == True]
        list_files = (nosource_files_site_df['name']).tolist()
        #write_nosource_files_site(i, list_files)
        len(nosource_files_site_df)
        count_file_type = {}
        for filepath in list_files:
            if re.search('^/store/data', filepath):
                count_file_type['data'] =  count_file_type.get('data', 0) + 1
            elif re.search('^/store/mc', filepath):
                count_file_type['mc'] =  count_file_type.get('mc', 0) + 1
            else:
                count_file_type['others'] =  count_file_type.get('others', 0) + 1

        for file_type, count in count_file_type.iteritems():
            print str(count) + " " + file_type + " at " + site

        blocks_info =  nosite_nosource_files['blocks_info']

        datasets_count = datasets_count_hash(nosite_nosource_files['block_names'])

        datasets_total = {}
        for dataset in datasets_count:
            datasets_total[dataset] = num_blocks(dataset)

        #count_file_type.keys()[1]
        #nosource_files_site_df['name'].apply(check_filetype, file_type = count_file_type.keys()[0])
        #nosource_files_site_df[nosource_files_site_df.name.apply(check_filetype, file_type = count_file_type.keys()[1]) ==  True]['name']
#        nosource_files_site_df['name'][0]


        for file_type in count_file_type.keys():
            print ('Type of files: ' + file_type)
            whole_blocks_ns = []
            whole_datasets_ns = []
            for dataset in datasets_total:
                if (dataset_isdata(dataset) == file_type):
                    n_files = num_files(dataset)
                    blocks_info_subset = blocks_info[blocks_info.dataset == dataset]
                    num_ns_files = blocks_info_subset.iloc[:,2].sum()
                    num_ns_blocks = datasets_count[dataset]
                    num_tot_blocks = datasets_count[dataset]
                    print ('Dataset: ' + dataset)
                    print ('Num of blocks with no source files: ' + str(datasets_count[dataset]) + "/" + str(datasets_total[dataset]))
                    print ('Num of no source files: ' + str(num_ns_files) + "/" + str(n_files))
                    print ('Num of no source files by block:')
                    if (datasets_count[dataset] == datasets_total[dataset] and num_ns_files == n_files):
                        whole_datasets_ns.append(dataset)

                    for m in range(len(blocks_info_subset)):
                        print(" " + blocks_info_subset.iloc[m, 0] + " " + str(blocks_info_subset.iloc[m, 2]) + "/" + str(blocks_info_subset.iloc[m, 1]))
                        if (blocks_info_subset.iloc[m, 2] == blocks_info_subset.iloc[m, 1] and (datasets_count[dataset] != datasets_total[dataset] and num_ns_files != n_files)):
                            whole_blocks_ns.append(blocks_info_subset.iloc[m, 0])

            list_whole_ns_files = nosource_files_site_df[nosource_files_site_df.name.apply(check_filetype, file_type = file_type)]['name'].tolist()
            nosource_files_site_df = nosource_files_site_df[~nosource_files_site_df.dataset.isin(whole_datasets_ns) & ~nosource_files_site_df.block.isin(whole_blocks_ns)]
            list_ns_files = nosource_files_site_df['name'].tolist()
            list_ns_files = [ ns_file for ns_file in list_ns_files if re.search('^/store/' + file_type, ns_file)]

            write_nosource_block_list(site, file_type, whole_blocks_ns)
            write_nosource_dataset_list(site, file_type, whole_datasets_ns)
            write_nosource_files_site(site, file_type, list_ns_files)
            write_nosource_files_site(site, file_type + '_whole', list_whole_ns_files)
        '''
        deletions_json = []
        for j in nosite_nosource_files['block_names']:
            deletion_json = search4deletions(j)
            deletions_json.append(deletion_json)

        write_deletions_json(i, deletions_json)
        '''

main()
