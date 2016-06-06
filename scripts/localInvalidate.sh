fileName=$1
siteName=$2
echo "~/TransferTeam/phedex/FileDeleteTMDB -db ~/param/DBParam:Prod/OPSNARAYANAN -list lfn:${fileName} -node $siteName"
~/TransferTeam/phedex/FileDeleteTMDB -db ~/param/DBParam:Prod/OPSNARAYANAN -list lfn:${fileName} -node $siteName
