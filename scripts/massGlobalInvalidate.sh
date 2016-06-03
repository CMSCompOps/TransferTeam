fileName=$1

sed 's/^/lfn:/' ${fileName} > lfn${fileName}

~/TransferTeam/phedex/FileDeleteTMDB -db ~/param/DBParam:Prod/OPSNARAYANAN -list lfn${fileName} -invalidate
~/TransferTeam/dbs/DBS3SetFileStatus.py --url=https://cmsweb.cern.ch/dbs/prod/global/DBSWriter --status=invalid --recursive=False --files=${fileName}
