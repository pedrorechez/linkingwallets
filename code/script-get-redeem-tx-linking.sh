#!/bin/bash


#### Extract transactions from account pages
current_folder=$(pwd)
tx_raw_info_folder=$current_folder'/tx-raw-info'
all_currencies=("BTC" "LTC" "TRC" "NMC")


parser=$current_folder'/parser-dvdrippler-redeem-details.pl'

all_linking_files=($current_folder'/linked-accounts-redeem-btc.txt' $current_folder'/linked-accounts-redeem-ltc.txt' $current_folder'/linked-accounts-redeem-trc.txt' $current_folder'/linked-accounts-redeem-nmc.txt')


currency_it=0 


for currency in "${all_currencies[@]}"
do
	linking_file=${all_linking_files[$currency_it]}
	currency_it=$(($currency_it+1))
	it=0
	cd $tx_raw_info_folder
	for dir in $(ls -d $PWD/*)
	do
		
		folder_issue=$dir'/'$currency'/issued'
		folder_redeem=$dir'/'$currency'/redeemed'
	 
		#cd $folder_issue
		cd $folder_redeem
		for directory in $(ls -d $PWD/*)
		do
			cd $directory
			echo "I am in $directory"
			rm *d*.* #Delete if there are different copies of the file
			cp *d* tmp.html

			perl $parser tmp.html out-tmp.txt $currency
			btc_addr_gw=$(cut -d $'\t' -f 2 out-tmp.txt)
			xrp_addr_user=$(cut -d $'\t' -f 4 out-tmp.txt)
			
			btc_link=$(cut -d $'\t' -f 3 out-tmp.txt)
			if [ "$currency" != "BTC" ]
			then
				tmp_hash=$(echo $btc_link | tail -c 65)
				btc_link="https://bchain.info/$currency/tx/$tmp_hash"
			fi
			#wget $btc_link --no-check-certificate
			curl -k $btc_link > tmp.txt
			#file=$(echo $btc_link | tail -c 65)
			file=tmp.txt
			
			if [ "$currency" != "BTC" ]
			then
				grep -o "'addr':'[0-9a-zA-Z]*" $file | sed "s/'addr':'//g" > extracted-btc-addresses.txt
			else
				grep -o '/address/[0-9a-zA-Z]*' $file | sed 's/\/address\///g' > extracted-btc-addresses.txt
			fi
			echo "Check output!!"
			echo "---------------"
			echo "Iteration number $it"
			it=$(($it+1))
			echo "I am in $directory"
			echo "The btc link is $btc_link"
			echo "The btc addresses available are"
			cat extracted-btc-addresses.txt
			echo "The btc address of the gw is $btc_addr_gw"
			#echo "Accept? (y/n)"
			#read answer
			#echo "Answer is $answer"
			#number_of_lines=$(wc -l extracted-btc-addresses.txt | cut -d ' ' -f 1)
			number_of_lines=$(wc -l extracted-btc-addresses.txt | tr -s $'\t' " " | cut -d ' ' -f 2) #changed for MAC

			#if [ "$currency" == "LTC" -o "$currency" == "NMC" ]
			#then
			#	mv extracted-btc-addresses.txt tmp2.txt
			#	number_of_lines=$(($number_of_lines - 4))
			#	head -n $number_of_lines tmp2.txt > extracted-btc-addresses.txt 
			#fi
			if [ $number_of_lines -lt 4 ] 
			then
				echo "Transfering to $linking_file. Addresses := $number_of_lines"
				while read addr
				do
					if [ "$addr" == "$btc_addr_gw" ]
					then
						#echo -e "rfYv1TXnwgDDK4WQNbFALykYuEBnrR4pDX\t$btc_addr_gw"
						echo -e "$xrp_addr_user\t$btc_addr_gw" >> $linking_file
					else
						#echo -e "$xrp_addr_user\t$addr"
						echo -e "rfYv1TXnwgDDK4WQNbFALykYuEBnrR4pDX\t$addr"	 >> $linking_file	
					fi
				done <extracted-btc-addresses.txt
			else
				echo "Output rejected. Addresses := $number_of_lines"
			fi
			#xrp_link=$(cut -d $'\t' -f 5 out-tmp.txt)
			#wget $xrp_link --no-check-certificate
		#	rm tmp.html

		done
		
	done
done

