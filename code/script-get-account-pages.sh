#!/bin/sh

out_folder="./account-pages"
accounts="accounts-attack.txt"

while read acc 
do
 file="$out_folder/account?_=$acc"
 url="https://dividendrippler.com/account?_=$acc"
 curl $url -o $file
 echo "$file crawled"

done <$accounts

