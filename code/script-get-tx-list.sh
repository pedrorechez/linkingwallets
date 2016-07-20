#!/bin/bash


#### Extract transactions from account pages
current_folder=$(pwd)
account_pages_folder='account-pages'
out_folder='tx-per-account'

for file in $(ls $account_pages_folder/*) 
do
	out_file=$(echo $file | tail -c 35)
	perl parser-dvdrippler-account.pl $file "$out_folder/$out_file"
done



