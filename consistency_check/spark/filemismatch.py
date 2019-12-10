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
import time


# stolen from CMSSpark
import schemas

class OptionParser():
    def __init__(self):
        "option Parser"
        self.parser = argparse.ArgumentParser(prog='consistency')
        msg = "Files mismatch since last  n days : default in past 7 days"
        self.parser.add_argument("--days",action="store",dest="timestamp",default=7,help=msg,type=int)
        msg= "Output path in HDFS for result"
        self.parser.add_argument("--out", action="store", dest="out_path",default=None,help=msg,required=True)

def fileMismatch(args):
    conf = SparkConf().setMaster("yarn").setAppName("CMS Working Set")
    sc = SparkContext(conf=conf)
    spark = SparkSession(sc)
    print("Initiated spark session on yarn, web URL: http://ithdp1101.cern.ch:8088/proxy/%s" % sc.applicationId)

    avroreader = spark.read.format("com.databricks.spark.avro")
    csvreader = spark.read.format("com.databricks.spark.csv").option("nullValue","null").option("mode", "FAILFAST")
    dbs_files = csvreader.schema(schemas.schema_files()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/current/FILES/part-m-00000")
    dbs_datasets = csvreader.schema(schemas.schema_datasets()).load("/project/awg/cms/CMS_DBS3_PROD_GLOBAL/current/DATASETS/part-m-00000")

    current = time.time()
    past_n_days = args.timestamp
    delta_t = current  - past_n_days*60*60*24

    if args.out_path:
        out = args.out_path + "filemismatch"
        working_set = (dbs_files
             .filter(col('f_is_file_valid')=='0')
             .filter(col('f_last_modification_date') >= delta_t)
             .join(dbs_datasets,col('f_dataset_id')==col('d_dataset_id'))
             .filter(col('d_dataset_access_type_id')=='1')
             .select('d_dataset','d_last_modified_by','f_logical_file_name')    # you can select more columns for detail info
             .distinct())
        working_set.select('f_logical_file_name').repartition(1).write.format("com.databricks.spark.csv").option("header", "true").save(out)
        working_set.groupby('d_dataset').agg((fn.count(fn.col("f_logical_file_name").isNotNull()))).show()
if __name__ == '__main__':
    optmgr = OptionParser()
    args = optmgr.parser.parse_args()
    fileMismatch(args)
