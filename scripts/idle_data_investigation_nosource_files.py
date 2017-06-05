#!/usr/bin/env python

'''
This scripts produces a list of of files was no source (no replica) and are identified by taking
a look to blocks asociated with basis value of -6 (at least one file in the block has no source
 replica remaining).

This files keep piling as idle data from subscriptions to diferent sites
(https://cmsweb.cern.ch/phedex/prod/Activity::QueuePlots?graph=idle&entity=dest&dest_filter=T0%7CT1%7CT2_CH_CERN&no_mss=true&period=l12h&upto=&.submit=Update).

The script recovers all the blocks realted to specific site subscriptions, then retrieves the responsible files.
It checks their creation date. Produces a report of the datasets involve and in with extent (files with non source/ total files in the dataset ).

A list of the files separated for each "type" ( whether they are 'data', 'mc' ... ) is generated.
This list is intended to be used to proced with global invalidation or further investigation, depending the type.
If all the files of a block or dataset have no source. A file with a list of for such blocks and a file with a list for such datasets is generated.
This lists can facilitate the invalidation process to be performe in bulk instead of by files.
Aditionally a list of non source files is generated, excluding the files that are included in the block list or datasets list.
The later also to considering the case in which a bulk invalidation wants to be performed.
Finally, deletions subscriptions for the involve blocks are performed. A file concateneting the information pulled is generated.
 Until it haven't present the case of finding a deletion request related.
 In the case this starts happening the script funtionallity should be extended.
'''

import json
import pandas as pd
from pandas.io.json import json_normalize
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime, timedelta
import re

# Silent warnings of insecure request from requests library
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def dataset_from_blockname(blockname):
    '''
    prety simple function to get the dataset name having the block name
    '''
    return re.search('(.+)#', blockname).group(1)


def check_datetime_Xweeks_older(timestamp, nweeks):
    '''
    checks if timestamp is older than certain amount of weeks
    '''
    time_limit = datetime.now() - timedelta(weeks=nweeks)
    return datetime.fromtimestamp(timestamp) <= time_limit


def get_nosource_files_info(block):
    '''
    Seerch replicas for a given block and return the files that have no replica at all "[]" in replica field.
    The returned value is a dictionary having a panda data frame with the metainfo of the block,
    the count of non  source files and the total number of files for the block
    Only the files with a creation time of more than 1 week are reported
    '''
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas'
    params = {"block": block}
    replicas_info = requests.get(url=url, params=params, verify=False).content
    replicas_json = json.loads(replicas_info)
    replicas_table = json_normalize(
        replicas_json['phedex']['block'][0]['file'])

    # Discards row entries of files with a creation date of one week or less
    replicas_table = replicas_table[replicas_table['time_create'].apply(
        check_datetime_Xweeks_older, nweeks=1) == True]

    num_files_in_block = len(replicas_table)
    no_source_files_table = replicas_table.loc[
        replicas_table.astype(str)['replica'] == "[]"]
    num_nosource_files_in_block = len(no_source_files_table)

    return {'df': no_source_files_table,
            'num_files_in_block': num_files_in_block,
            'num_nosource_files_in_block': num_nosource_files_in_block}


def site_nosource_files_df(site):
    '''
    check the data service blockarrive for blocks with status basis = -6
    basis -6 means: at least one file in the block has no source replica remaining
    It returns a dictionary with a dataframe containing the metainformation of with files with no source of all blocks and
    a dataframe with the metainfomation at the block level of all theh blocks with -6 statue for the evaluated site
    '''
    # Get the info of blockarrive for the site parsed in a panda dataframe
    # panda dataframe with the info at block level: blocks_arrive_table
    url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/blockarrive"
    params = {"to_node": site, "basis": -6}
    block_arrive_info = requests.get(
        url=url, params=params, verify=False).content

    block_arrive_info_json = json.loads(block_arrive_info)
    blocks_arrive_table = json_normalize(
        block_arrive_info_json['phedex']['block'])

    # Get the info for non-source files and how many of all the files in the block have non-source
    # nosource_files_df: have the information of the non-source file. At file level
    # blocks_info_df: have the information at block level that block_arrive
    # table has and additionally the count of ns files
    ns_files_list = []
    blocks_info_df = pd.DataFrame()
    for blockname in blocks_arrive_table['name']:
        nosource_files_info = get_nosource_files_info(blockname)
        nosource_files_df = nosource_files_info['df']
        nosource_files_df['blockname'] = blockname
        ns_files_list.append(nosource_files_df)
        df_tmp = pd.DataFrame(data=[[nosource_files_info[
                              'num_files_in_block'], nosource_files_info['num_nosource_files_in_block']]])
        blocks_info_df = blocks_info_df.append(df_tmp, ignore_index=True)

    nosource_files_df = pd.concat(ns_files_list)
    nosource_files_df['datetime_create'] = nosource_files_df[
        'time_create'].apply(datetime.fromtimestamp)
    nosource_files_df['dataset'] = nosource_files_df[
        'blockname'].apply(dataset_from_blockname)

    blocks_info_df.columns = [
        'num_files_in_block', 'num_nosource_files_in_block']
    blocks_info_df = pd.concat([blocks_arrive_table, blocks_info_df], axis=1)

    return {'files_info': nosource_files_df, 'blocks_info': blocks_info_df}


def count_file_type(ns_files_df):
    '''
    From a non-source files dataframe get the number of files that
    are 'data', 'mc' or 'other' types.
    '''
    count_file_type = {}
    for filepath in ns_files_df['name']:
        if re.search('^/store/data', filepath):
            count_file_type['data'] = count_file_type.get('data', 0) + 1
        elif re.search('^/store/mc', filepath):
            count_file_type['mc'] = count_file_type.get('mc', 0) + 1
        else:
            count_file_type['others'] = count_file_type.get('others', 0) + 1
    return count_file_type


def datasets_count_hash(blocks_file_list):
    '''
    From a list of the blocks identified with basis -6
    Produces a dictionary listing the involve datasets as keys and the num of blocks (with basis -6) as values
     '''
    datasets_count = {}
    for i in blocks_file_list:
        dataset = dataset_from_blockname(str(i))
        datasets_count[dataset] = datasets_count.get(dataset, 0) + 1
    return datasets_count


def counts_for_dataset(dataset):
    '''
    For a dataset, retrieves relevant summary information, i.e.,
    returns total number of files and total number of blocks
    '''
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/data'
    params = {"dataset": dataset, "level": 'block'}
    data_info = requests.get(url=url, params=params, verify=False).content
    data_json = json.loads(data_info)
    data_table = json_normalize(data_json['phedex']['dbs'][
                                0]['dataset'][0]['block'])
    return {'num_files': data_table['files'].sum(), 'num_blocks': len(data_table)}


def dataset_kind_is(dataset):
    '''
    From dataset name returns the type of file it contains: 'data',  'mc'....
    '''
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas'
    params = {"dataset": dataset}
    replicas_info = requests.get(url=url, params=params, verify=False).content
    replicas_json = json.loads(replicas_info)
    replicas_sample_table = json_normalize(
        replicas_json['phedex']['block'][0]['file'])
    return (str(replicas_sample_table['name'][0]).split("/")[2])


def check_filetype(filepath, file_type):
    '''
    check if a file is of a specific category: 'mc',  'data' and 'other'
    '''
    return bool(re.search('^/store/' + file_type, filepath))


def write_nosource_files_site(site, file_type, list_files):
    filename = "nosource_files_" + file_type + "_" + site + ".txt"

    with open(filename, "w") as f:
        f.write("\n".join(list_files))


def write_nosource_block_list(site, file_type, list_blocks):
    filename = "nosource_blocks_" + file_type + "_" + site + ".txt"

    with open(filename, "w") as f:
        f.write("\n".join(list_blocks))


def write_nosource_dataset_list(site, file_type, list_datasets):
    filename = "nosource_datasets_" + file_type + "_" + site + ".txt"


def search_deletions(block):
    url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/deletions'
    params = {"block": block}
    deletions_info = requests.get(url=url, params=params, verify=False).content
    deletions_json = json.loads(deletions_info)
    return(deletions_json)


def write_deletions_json(site, deletions_json_list):
    filename = "nosource_blocks_deletions_jsons" + site + ".txt"

    with open(filename, "w") as f:
        deletions_json_list = map(str, deletions_json_list)
        f.write("\n".join(deletions_json_list))


def check_idle_no_source(site):
    nosource_site_info = site_nosource_files_df(site)

    nosource_site_info = site_nosource_files_df(site)

    # file level df
    ns_files_info = nosource_site_info['files_info']
    # block level df
    ns_blocks_info = nosource_site_info['blocks_info']

    # Sum of the size reported for all the files with no source found
    # This with to help to compare with the plot of idle data for the site for
    # with the subscriptions has been investigated
    ns_files_size = ns_files_info['bytes'].sum()
    ns_files_size_TB = ns_files_size * (10 ** (-12))
    # Num of files
    num_ns_files = len(ns_files_info)

    print 'For blocks subscriptions to {}, {} files where found to have no source.'.format(site, num_ns_files)
    print 'Total size: {} TB'.format(ns_files_size_TB)

    # Files types diversity
    count_file_type_dic = count_file_type(ns_files_info)

    for file_type, count in count_file_type_dic.iteritems():
        print str(count) + " " + file_type + " at " + site

    # Datasets and corresponding number of blocks involve (basis -6)
    datasets_count = datasets_count_hash(ns_blocks_info['name'].tolist())

    # Get total number of files and total number of blocks
    datasets_total = {}
    for dataset in datasets_count:
        datasets_total[dataset] = counts_for_dataset(dataset)

    for file_type in count_file_type_dic.keys():
        print ('Type of files: ' + file_type)
        whole_blocks_ns = []
        whole_datasets_ns = []
        for dataset in datasets_count:
            if (dataset_kind_is(dataset) == file_type):
                n_files = datasets_total[dataset]['num_files']
                ns_blocks_info_subset = ns_blocks_info[
                    ns_blocks_info.dataset == dataset]
                num_ns_files = ns_blocks_info_subset.num_nosource_files_in_block.sum()
                num_ns_blocks = datasets_count[dataset]
                num_tot_blocks = datasets_total[dataset]['num_blocks']
                print 'Dataset: {}'.format(dataset)
                print 'Num of blocks with no source files: {}/{}'.format(num_ns_blocks, num_tot_blocks)
                print 'Num of no source files: {}/{}'.format(num_ns_files, n_files)
                print 'Num of no source files by block:'
                if (num_ns_blocks == num_tot_blocks and num_ns_files == n_files):
                    whole_datasets_ns.append(dataset)

                for idx, row in ns_blocks_info_subset.iterrows():
                    print ' {} {}/{}'.format(row['name'], row.num_nosource_files_in_block, row.num_files_in_block)
                    if (row.num_nosource_files_in_block == row.num_files_in_block and (num_ns_blocks != num_tot_blocks and num_ns_files != n_files)):
                        whole_blocks_ns.append(row['name'])
                print '=' * 100
        list_whole_ns_files = ns_files_info[ns_files_info.name.apply(
            check_filetype, file_type=file_type)]['name'].tolist()
        nosource_files_site_df = ns_files_info[~ns_files_info.dataset.isin(
            whole_datasets_ns) & ~ns_files_info.blockname.isin(whole_blocks_ns)]
        list_ns_files = ns_files_info['name'].tolist()
        list_ns_files = [ns_file for ns_file in list_ns_files if re.search(
            '^/store/' + file_type, ns_file)]

        write_nosource_block_list(site, file_type, whole_blocks_ns)
        write_nosource_dataset_list(site, file_type, whole_datasets_ns)
        write_nosource_files_site(site, file_type, list_ns_files)
        write_nosource_files_site(
            site, file_type + '_whole', list_whole_ns_files)

        deletions_json = []
        for j in ns_files_info.blockname:
            deletion_json = search_deletions(j)
            deletions_json.append(deletion_json)

        write_deletions_json(i, deletions_json)


def main():

    sites = [
        "T1_US_FNAL_Disk",
        "T2_CH_CERN",
        "T1_RU_JINR_Disk"
    ]

    for site in sites:
        check_idle_no_source(site)

main()
