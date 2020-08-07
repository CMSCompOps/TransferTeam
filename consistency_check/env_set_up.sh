source ~/TransferTeam/scripts/setup.sh
cd /afs/cern.ch/user/o/ogarzonm/Fork_TransferTeam/TransferTeam/consistency_check/ 
python3 -m venv env
source ./env/bin/activate
pip3 install update pandas
pip3 install requests
python3 File_mismatch_WS.py
python Check_dbs_invalidations_file.py
source ~/TransferTeam/scripts/setup_in_rucio.sh
awk '{system("rucio list-file-replicas cms:"$1)}' check_in_dbs.txt > files_in_rucio_test.txt
cut -f3 -d '|' files_in_rucio_test.txt > files_in_rucio.txt
sed -i 's/ //g' files_in_rucio.txt
diff check_in_dbs.txt files_in_rucio.txt | grep /store/ > files_not_yet_in_rucio.txt
