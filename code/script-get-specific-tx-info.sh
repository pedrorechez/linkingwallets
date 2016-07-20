#!/bin/bash

current_folder=$(pwd)

### Extract btc and xrp transactions
tx_per_account_folder=$current_folder'/tx-per-account'
tx_raw_info_folder=$current_folder'/tx-raw-info'
all_currencies=("BTC" "LTC" "TRC" "NMC")


for currency in "${all_currencies[@]}"
do

	for file in $(ls -d -1 $tx_per_account_folder/*)
	do	
		cd $tx_raw_info_folder
		out_file=$(echo $file | tail -c 35)
		mkdir $out_file
		cd $out_file


		echo "reading file $file"
		#Issue and redeem tx for $currency
		cat $file | grep "$currency" | grep "issued" > $current_folder/tmp_issued.txt
		cat $file | grep "$currency" | grep "redeemed" > $current_folder/tmp_redeemed.txt


		#Issue $currency
		it=1
		mkdir $currency
		cd $currency
		mkdir issued
		cd issued
		while read line 
		do

		  link=$(echo -e $line | cut -d ' ' -f6)
		  echo $link

		  mkdir $it
		  cd $it
		   wget 'https://dividendrippler.com/'$link --no-check-certificate  
		  cd ..
		  it=$(($it+1))
		done < $current_folder/tmp_issued.txt


		#Redeem $currency
		it=1
		cd $tx_raw_info_folder
		cd $out_file
		cd $currency
		mkdir redeemed
		cd redeemed
		while read line 
		do

		  link=$(echo -e $line | cut -d ' ' -f6)
		  echo $link

		  mkdir $it
		  cd $it
		   wget 'https://dividendrippler.com/'$link --no-check-certificate  
		  cd ..
		  it=$(($it+1))
		done < $current_folder/tmp_redeemed.txt

		rm $current_folder/tmp_issued.txt
		rm $current_folder/tmp_redeemed.txt
	done

done

