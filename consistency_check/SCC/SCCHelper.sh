#!/bin/bash

src=/afs/cern.ch/user/m/mtaze/TransferTeam/consistency_check/SCC
out=/afs/cern.ch/user/m/mtaze/work/OUTPUT/SCC_output
db=""
node=""
dump=""
round=""
function usage
{
    echo "-d | --db     : The usual PhEDEx db configuration file"
    echo "-n | --node   : PhEDEx node name"
    echo "-i | --dump   : a file containing full LFNs as found in site storage, one lfn per line."
    echo "-r | --round  : Consistency Check Round label to use in output directory creation (e.g. May14)"
}


# parse the command line arguments
TEMP=`getopt -o d:n:i:r:h --long db:,node:,dump:,round:,help -n "$FUNCNAME" -- "$@"`
eval set -- "$TEMP";
while [ $# -gt 0 ]
do
    case "$1" in
        (-d|--db)   db="$2"; shift 2;;
        (-n|--node) node="$2"; shift 2;;
        (-i|--dump) dump="$2"; shift 2;;
        (-r|--round) round="$2"; shift 2;;
        (-h|--help) usage; exit 0;;
        (--) shift; break;;
        (*)  echo "error!"; exit 1;;
    esac
done

# check required arguments
[ -z $db ] && { echo >&2 "Please specify DBParam with -d(--db) option!"; exit 1; }
[ -z $node ] && { echo >&2 "Please specify node name with -n(--node) option!"; exit 1; }
[ -z $dump ] && { echo >&2 "Please specify path to the dump file with -i(--dump) option!"; exit 1; }
[ -z $round ] && { echo >&2 "Please specify round date(e.g. May14) with -r(--round) option!"; exit 1; }

# some safety checks before starting SCC
[ `grep -cv "^/store/" $dump` -eq 0 ] || { echo "All LFNs in the dump should start with \"/store\""; exit 5; }
[ `grep -Ecv "/store/mc|/store/data|/store/generator|/store/results|/store/hidata|/store/himc|/store/lumi|/store/relval" $dump` -eq 0 ] || { echo "Storage dump should only contain LFNs under these directories: \n/store/mc\n/store/data\n/store/generator\n/store/results\n/store/hidata\n/store/himc\n/store/lumi\n/store/relval"; exit 5; }
[ `grep -cv "\." $dump` -eq 0 ] || { echo "Some LFNs have no extension(.root, .tmp), these can be directory. Please remove files without extension from the dump before continue!"; exit 5; }

# create dir for site
out=$out"/"$round"/"$node"/"
mkdir -p $out

out_orphans="$out${node:6}_SCC_potential_orphan_list.txt"
out_status="$out${node:6}_SCC_status_list.txt"

# remove old files before start to append
rm -f $out_status

# get SE name from node name
se_name=`python $src/SCCUtils.py --node $node`
[ -z $se_name ] && { echo >&2 "Failed to find valid SE name"; exit 2; }

# get orphan list
$src/StorageConsistencyCheck -db $db -lfnlist $dump -se_name $se_name | grep '^/' > $out_orphans

# get DBS status of files&datasets
python $src/SCCUtils.py --node $node --list $out_orphans --output $out_status

echo -e "\nDBS status of the files&datasets have been stored at: $out_status"
