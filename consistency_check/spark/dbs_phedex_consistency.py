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
from datetime import date , timedelta
# stolen from CMSSpark
import schemas

class OptionParser():
    def __init__(self):
        "option Parser"
        self.parser = argparse.ArgumentParser(prog='consistency')
        msg= "Output path in HDFS for result"
        self.parser.add_argument("--out", action="store", dest="out_path",default=None,help=msg,required=True)

class run_consistency(object):
    def __init__(self, out):
        self.out = out
        conf = SparkConf().setMaster("yarn").setAppName("CMS Working Set")
        sc = SparkContext(conf=conf)
        self.spark = SparkSession(sc)
        avroreader = self.spark.read.format("com.databricks.spark.avro")
        csvreader  =  self.spark.read.format("com.databricks.spark.csv").option("nullValue","null").option("mode","FAILFAST")
        ## check if phedex_path exist or not on hdfs area and you can directly assign it
        phedex_path = "/project/awg/cms/phedex/block-replicas-snapshots/csv/time=" + str((date.today() - timedelta(days=2)).strftime("%Y-%m-%d")) + "_*/part-m-00000"
        self.phedex_block_replicas = csvreader.schema(schemas.schema_phedex()).load(phedex_path)
        self.dbs_files = csvreader.schema(schemas.schema_files()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/new/FILES/part-m-00000")
        self.dbs_blocks = csvreader.schema(schemas.schema_blocks()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/new/BLOCKS/part-m-00000")
        self.dbs_datasets = csvreader.schema(schemas.schema_datasets()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/new/DATASETS/part-m-00000")

    def invalid_dbs_present_phedex(self):
        '''

        Returns a dataframe with datasets which have "INVALID" status in DBS and are "PRESENT" in phedex

        :func: run_consistency.invalid_dbs_present_phedex()

        for reference dbs d_dataset_access_type_id:
             1 :  valid
             2 :  invalid
             42 : Deprecated
             41 : Production
             81 : Deleted
        '''
        invalid_dbs_present_phedex = (self.dbs_datasets
                .filter(col('d_dataset_access_type_id')=='2')
                .join(self.dbs_blocks,col('d_dataset_id')==col('b_dataset_id'))
                .join(self.phedex_block_replicas,col('d_dataset')==col('dataset_name'))
                .filter(col('dataset_name').isNotNull())
                .withColumn('input_campaign', fn.regexp_extract(col('d_dataset'), "^/[^/]*/((?:HI|PA|PN|XeXe|)Run201\d\w-[^-]+|CMSSW_\d+|[^-]+)[^/]*/", 1))
                .select('input_campaign','d_dataset','d_last_modified_by')    # you can select more columns for detail info
                .distinct())

        invalid_dbs_present_phedex.groupby("input_campaign").agg((fn.count(fn.col("d_dataset")))).show()
        return invalid_dbs_present_phedex.select("d_dataset")

    def deleted_dbs_present_phedex(self):
        '''
        Returns a dataframe with datasets which have "DELETED" status in DBS and "PRESENT" status in phedex

        :func: run_consistency.deleted_dbs_present_phedex()

        '''
        out = args.out_path + "/deleted_dbs_present_phedex"
        deleted_dbs_present_phedex = (self.dbs_datasets
                .filter(col('d_dataset_access_type_id')=='81')
                .join(self.dbs_blocks,col('d_dataset_id')==col('b_dataset_id'))
                .join(self.phedex_block_replicas,col('d_dataset')==col('dataset_name'))
                .filter(col('dataset_name').isNotNull())
                .withColumn('input_campaign', fn.regexp_extract(col('d_dataset'), "^/[^/]*/((?:HI|PA|PN|XeXe|)Run201\d\w-[^-]+|CMSSW_\d+|[^-]+)[^/]*/", 1))
                .select('input_campaign','d_dataset')    # you can select more columns for detail info
                .distinct())

        deleted_dbs_present_phedex.groupby("input_campaign").agg(fn.count(fn.col("d_dataset"))).show()
        return deleted_dbs_present_phedex.select("d_dataset")

    def valid_dbs_missing_phedex(self):
        '''
        Returns a dataframe with block name which have "VALID" status in DBS and are "MISSING" in phedex

        :func: run_consistency.valid_dbs_missing_phedex()

        '''
        out = args.out_path + "/valid_dbs_missing_phedex"
        valid_dbs_missing_phedex = (self.dbs_datasets
                .filter(col('d_dataset_access_type_id')=='1')
                .join(self.dbs_blocks,col('d_dataset_id')==col('b_dataset_id'))
                .join(self.phedex_block_replicas,col('d_dataset')==col('dataset_name'))
                .filter(col('block_name').isNotNull() & col('node_id').isNull())
                .withColumn('input_campaign', fn.regexp_extract(col('d_dataset'), "^/[^/]*/((?:HI|PA|PN|XeXe|)Run201\d\w-[^-]+|CMSSW_\d+|[^-]+)[^/]*/", 1))
                .select('input_campaign','block_name')
                .distinct())

        print("Please check the below list of datasets with phedex api calls , Its possible you encounter discrepency due to the time difference of dataset injection in both databases and snapshot stored on HDFS")
        valid_dbs_missing_phedex.groupby("input_campaign").agg(fn.count(fn.col("block_name"))).show()
        return valid_dbs_missing_phedex.select("block_name")



if __name__ == '__main__':
    optmgr = OptionParser()
    args = optmgr.parser.parse_args()
    con =  run_consistency(args.out_path)
    invalid_dbs_present_phedex = con.deleted_dbs_present_phedex()
