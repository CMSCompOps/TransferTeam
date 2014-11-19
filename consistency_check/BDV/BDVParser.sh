#!/bin/bash

src=/afs/cern.ch/user/m/mtaze/TransferTeam/consistency_check/BDV
node=""
db=""
test="size"
day=10
check_finished=false
verbose=false
out=""

function usage
{
    echo "-d | --db      : The usual PhEDEx db configuration file"
    echo "-n | --node    : PhEDEx node name (use _Buffer for T1 tape endpoints)"
    echo "-t | --test    : Limit report to select only this type of failing blocks (default: size)"
    echo "-l | --day     : Limit report to tests updated so many days ago (default: 10)"
    echo "-c | --check   : If flag is set, it will only check whether BDV completed"
    echo "-o | --output  : Output directory"
    echo "-v | --verbose : verbose output"
}


# parse the command line arguments
TEMP=`getopt -o d:n:t:l:o:cvh --long db:,node:,test:,day:,output:,check,verbose,help -n "$FUNCNAME" -- "$@"`
eval set -- "$TEMP";
while [ $# -gt 0 ]
do
    case "$1" in
        (-d|--db)   db="$2"; shift 2;;
        (-n|--node) node="$2"; shift 2;;
        (-t|--test) test="$2"; shift 2;;
        (-l|--day)  day="$2"; shift 2;;
        (-c|--check) check_finished=true; shift ;;
        (-v|--verbose) verbose=true; shift;;
        (-o|--output) out="$2"; shift 2;;
        (-h|--help) usage; exit 0;;
        (--) shift; break;;
        (*)  echo >&2 "error!"; exit 1;;
    esac
done

# check required arguments
[ -z $db ] && { echo >&2 "Please specify DBParam with -d(--db) option!"; exit 1; }
[ -z $node ] && { echo >&2 "Please specify node name with -n(--node) option!"; exit 1; }
[ -z $out ] && { out="./"$node; }

# create node directory
mkdir -p $out

# create output files
out_blocklist="$out"/"${node:6}_BDV_block_list.txt"
out_lfnlist="$out"/"${node:6}_BDV_LFN_list.txt"
out_local="$out"/"${node:6}_BDV_local_invalidation.txt"
out_global="$out"/"${node:6}_BDV_global_invalidation.txt"
out_report="$out"/"${node:6}_BDV_report.txt"


# get injection report
$src/BlockDownloadVerify-report.pl --db $db --node $node --day $day > $out_report

# check injection finished
unfinished=`cat $out_report | grep -i $node | egrep -c -v "Fail /|OK /"`
[ $unfinished -gt 0 ] && { echo >&2 "!!!Some injection status are different than Fail and OK, Injection is not completed yet"; }

# script run only to check whether BDV finished
[ $check_finished == true ] && exit 0;

# remove old files before start to append them
rm -f $out_lfnlist $out_global $out_local
touch $out_global $out_local

# get failed blocks
cat $out_report | grep 'Fail /' | grep " $test " | tr -s ' ' | cut -d ' ' -f 13 | sort | uniq | egrep -iv "test|backfill|penguins|bunnies" > $out_blocklist

# get failed files in these blocks
counter=0
total=`wc -l < $out_blocklist`
for blk in `cat $out_blocklist`
do
    [ $verbose == true ] && { counter=$(($counter+1)); echo -ne "\rCollecting LFN info ($counter/$total)"; }
    $src/BlockDownloadVerify-report.pl --db $db --node $node --day $day  --block $blk --detail | grep '^Block' | tr -s ' ' | cut -d ' ' -f3 | cut -d '=' -f2 | sort | uniq >> $out_lfnlist
done
echo

# check failed block exists
[ -s $out_lfnlist ] || { echo -e "All blocks are consistent"; exit 0; }

# create local&global invalidation lists
counter=0
total=`wc -l < $out_lfnlist`
for lfn in `cat $out_lfnlist`
do
    [ $verbose == true ] && { counter=$(($counter+1)); echo -ne "\rSorting by invalidation type ($counter/$total)"; }

    # if node is T1_XXX_Buffer, then ignore both T1_XXX_MSS, T1_XXX_Buffer
    if [[ $node == T1_*_Buffer ]]
    then
        ignore=$node"|"${node/_Buffer/_MSS}
    else
        ignore=$node
    fi
 
    replicaCount=`python $src/checkReplica.py --lfn $lfn | tr -s ' ' | cut -d ' ' -f4 | tr ',' '\n' | egrep -vi $ignore | grep -c "^T"`
	[ $replicaCount -gt 0 ] && echo $lfn >> $out_local || echo $lfn >> $out_global
done 

echo -e "\nInvalidation files have been created at:"
echo "Local Invalidation: $out_local (`wc -l < $out_local`)"
echo "Global Invalidation: $out_global (`wc -l < $out_global`)"
