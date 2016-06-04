n=$(../commons/datasvc.py --service subscriptions --path phedex/dataset/subscription:node,percent_files  --options "dataset=${1}" | grep -v "${2}" | grep 100 | wc -l)
#echo $n
if [ "$n" -eq "0" ]; then
  echo ${1}
fi

