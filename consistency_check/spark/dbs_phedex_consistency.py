#!/usr/bin/env spark-submit
from __future__ import print_function
import argparse
import json
import os

from pyspark import SparkConf, SparkContext, StorageLevel
from pyspark.sql import SparkSession, Column
from pyspark.sql.functions import col
import pyspark.sql.functions as fn
import pyspark.sql.types as types
from pyspark.sql import DataFrame
import datetime


# stolen from CMSSpark
import schemas

class OptionParser():
    def __init__(self):
        "option Parser"
        self.parser = argparse.ArgumentParser(prog='consistency')
        msg = "phedex dataset option: it takes 'missing' or 'present'"
        self.parser.add_argument("--phedex",action="store",dest="phedex_status",default=None,help=msg,required=True)
        msg = "DBS dataset status"
        self.parser.add_argument("--dbs",action="store",dest="dbs_status",default=None,help=msg,required=True)
        msg= "Output path in HDFS for result"
        self.parser.add_argument("--out", action="store", dest="out_path",default=None,help=msg,required=True)

def run_consistency(args):

    conf = SparkConf().setMaster("yarn").setAppName("CMS Working Set")
    sc = SparkContext(conf=conf)
    spark = SparkSession(sc)
    print("Initiated spark session on yarn, web URL: http://ithdp1101.cern.ch:8088/proxy/%s" % sc.applicationId)

    avroreader = spark.read.format("com.databricks.spark.avro")
    csvreader = spark.read.format("com.databricks.spark.csv").option("nullValue","null").option("mode", "FAILFAST")
    dbs_files = csvreader.schema(schemas.schema_files()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/current/FILES/part-m-00000")
    dbs_blocks = csvreader.schema(schemas.schema_blocks()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/current/BLOCKS/part-m-00000")
    dbs_datasets = csvreader.schema(schemas.schema_datasets()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/current/DATASETS/part-m-00000")

    yesturday = datetime.date.today() - datetime.timedelta(days=1)
    phedex_time_stamp = yesturday.strftime("%Y-%m-%d")  ## specifying date for phedex replicas

    if args.phedex_status == 'present' and args.dbs_status == 'invalid':
        phedex_path = "/project/awg/cms/phedex/block-replicas-snapshots/csv/time=" + str(phedex_time_stamp) + "_*/part-m-00000"
        phedex_block_replicas = csvreader.schema(schemas.schema_phedex()).load(phedex_path)
        '''
        for reference dbs d_dataset_access_type_id:
             1 :  valid
             2 :  invalid
             42 : Deprecated
             41 : Production
             81 : Deleted
        '''
        out = args.out_path + "/invalid_dbs_present_phedex"
        invalid_dbs_present_phedex = (dbs_datasets
                .filter(col('d_dataset_access_type_id')=='2')
                .join(dbs_blocks,col('d_dataset_id')==col('b_dataset_id'))
                .join(phedex_block_replicas,col('d_dataset')==col('dataset_name'))
                .filter(col('dataset_name').isNotNull())
                .withColumn('input_campaign', fn.regexp_extract(col('d_dataset'), "^/[^/]*/((?:HI|PA|PN|XeXe|)Run201\d\w-[^-]+|CMSSW_\d+|[^-]+)[^/]*/", 1))
                .select('input_campaign','d_dataset','d_last_modified_by')    # you can select more columns for detail info
                .distinct())
        invalid_dbs_present_phedex.write.format("com.databricks.spark.csv").option("header", "true").save(out)
        invalid_dbs_present_phedex.groupby("input_campaign").agg((fn.count(fn.col("d_dataset")))).show()
    elif args.phedex_status == 'present' and args.dbs_status == 'deleted':
        phedex_path = "/project/awg/cms/phedex/block-replicas-snapshots/csv/time=" + str(phedex_time_stamp) + "_*/part-m-00000"
        phedex_block_replicas = csvreader.schema(schemas.schema_phedex()).load(phedex_path)
        out = args.out_path + "/deleted_dbs_present_phedex"
        deleted_dbs_present_phedex = (dbs_datasets
                .filter(col('d_dataset_access_type_id')=='81')
                .join(dbs_blocks,col('d_dataset_id')==col('b_dataset_id'))
                .join(phedex_block_replicas,col('d_dataset')==col('dataset_name'))
                .filter(col('dataset_name').isNotNull())
                .withColumn('input_campaign', fn.regexp_extract(col('d_dataset'), "^/[^/]*/((?:HI|PA|PN|XeXe|)Run201\d\w-[^-]+|CMSSW_\d+|[^-]+)[^/]*/", 1))
                .select('input_campaign','d_dataset')    # you can select more columns for detail info
                .distinct())
        deleted_dbs_present_phedex.write.format("com.databricks.spark.csv").option("header", "true").save(out)
        deleted_dbs_present_phedex.groupby("input_campaign").agg(fn.count(fn.col("d_dataset"))).show()
    elif args.phedex_status == 'missing' and args.dbs_status == 'valid':
        # to be on the safe side : adding time difference for block replicas injected
        d = phedex_time_stamp  - datetime.timedelta(days=30)   # should add argumentparser option
        phedex_path = "/project/awg/cms/phedex/block-replicas-snapshots/csv/time=" + str(d) + "_*/part-m-00000"
        phedex_block_replicas = csvreader.schema(schemas.schema_phedex()).load(phedex_path)
        out = args.out_path + "/valid_dbs_missing_phedex"
        valid_dbs_missing_phedex = (dbs_datasets
                .filter(col('d_dataset_access_type_id')=='1')
                .join(dbs_blocks,col('d_dataset_id')==col('b_dataset_id'))
                .join(phedex_block_replicas,col('d_dataset')==col('dataset_name'))
                .filter(col('block_name').isNotNull() & col('node_id').isNull())
                .withColumn('input_campaign', fn.regexp_extract(col('d_dataset'), "^/[^/]*/((?:HI|PA|PN|XeXe|)Run201\d\w-[^-]+|CMSSW_\d+|[^-]+)[^/]*/", 1))
                .select('input_campaign','block_name')
                .distinct())
        valid_dbs_missing_phedex.write.format("com.databricks.spark.csv").option("header", "true").save(out)
        valid_dbs_missing_phedex.groupby("input_campaign").agg(fn.count(fn.col("block_name"))).show()


if __name__ == '__main__':
    optmgr = OptionParser()
    args = optmgr.parser.parse_args()
    run_consistency(args)
