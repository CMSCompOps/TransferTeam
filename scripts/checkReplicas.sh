#echo "testing"
n=$(../commons/datasvc.py --service subscriptions --path phedex/dataset/subscription:node,percent_files  --options "dataset=${1}" | grep -v "T2_BE_UCL" | grep 100 | wc -l)
#echo $n
if [ "$n" -eq "0" ]; then
  echo ${1}
fi

#echo $1
#../commons/datasvc.py --service subscriptions --path phedex/dataset/subscription:node,percent_files  --options "dataset=${1}" 
