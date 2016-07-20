
from urlparse import urlparse
import os
import array
import struct
import uuid
import hashlib
import base64
import threading
import time
import logging
import traceback
import sys
import json
import urllib2
import requests


#BIGGEST_LEDGER = 11446788 # CCS biggest ledger
#SMALLEST_LEDGER = 32570 # CCS smallest ledger 
#BIGGEST_LEDGER = 14468739 # WWW biggest ledger 
#SMALLEST_LEDGER = 11446789 #WWW smallest ledger
BIGGEST_LEDGER = 17410130 # next
SMALLEST_LEDGER = 14468740 # next
RESULTS_PER_PAGE = 20 # number of results per page
MAX_RETRIES_PER_ACCOUNT = 10
MAX_CONSECUTIVE_ERRORS = 10
SLEEP_PER_CALL = 1 # before calling any url


def single_call():
	offset = 0
	url = "https://history.ripple.com/v1/accounts/%s/transactions?type=Payment&ledger_min=%d&ledger_max=%d&result=tesSUCCESS&offset=%d" % ("rKMvZZKzwwVRqdbPT2bF6qXueKhxTLNPJa", SMALLEST_LEDGER, BIGGEST_LEDGER, 0)
	response = urllib2.urlopen(url)
	data = response.read()
	data_decoded = json.loads(data)

	#if data_decoded["success"] != True: continue
	if data_decoded["result"] != "success": 
		print 'result is error'
		exit()
	#transactions = data_decoded["payments"]
	transactions = data_decoded["transactions"]
	offset += len(transactions)
	print "Total transactions in this page are: %d" % len(transactions)
	
	for tx in transactions:
		print tx["tx"]["Account"], tx["tx"]["Destination"]
	exit()


def main():



    fileIn = sys.argv[1]
    fileOut = open(sys.argv[2], "w", 0)

    accounts = list()
    for line in open(fileIn): accounts.append(line.strip())
   

    for account in accounts:


        print "\n\n\nStarting for account: %s" % account
        end_ledger = BIGGEST_LEDGER # If provided, exclude payments from ledger versions newer than the given ledger. (max ledger value)
        start_ledger = SMALLEST_LEDGER # If provided, exclude payments from ledger versions older than the given ledger. (min_ledger value)
        exclude_failed = "true"
        page = 1 # The page number for the results to return, if more than results_per_page are available. The first page of results is page 1, the second page is number 2, and so on. Defaults to 1.

        offset=0 #The history server API uses offset to iterate over the different transactions of an account
        retries = 0
        call_number = 0
        cons_gateway_errors = 0 # number of consecutive bad gateway errors we got. we will multiply this with the wait time to make sure we eventually get the answer
        is_first_call = 1 # this is the first call, if retrieved successfully, we will use another URL format -- notce that it is different from call_number

        while 1: # iterate over all the pages for this account

            retries += 1
            if retries >= MAX_RETRIES_PER_ACCOUNT:
                print "Exceeded the quota for max retries for account %s. Breaking." % account
                break

            call_number += 1

            # if is_first_call == 1:
            #     url = "https://api.ripple.com/v1/accounts/%s/payments?results_per_page=%d&exclude_failed=%s&page=%d" % (account, RESULTS_PER_PAGE, exclude_failed, page)
            # else:
            #     url = "https://api.ripple.com/v1/accounts/%s/payments?results_per_page=%d&start_ledger=%d&end_ledger=%d&exclude_failed=%s&page=%d" % (account, RESULTS_PER_PAGE, start_ledger, end_ledger, exclude_failed, page)
            
            
            url = "https://history.ripple.com/v1/accounts/%s/transactions?type=Payment&ledger_min=%d&ledger_max=%d&result=tesSUCCESS&offset=%d" % (account, start_ledger, end_ledger, offset)
            print "Call number: %d" % call_number
            print "URL: %s" % url

            try:
                response = urllib2.urlopen(url)
                data = response.read()
                is_first_call = 0 # if data is retrieved successfully, then make the change so that URL with ledger numbers is used from now on
                cons_gateway_errors = 0 # this call was executed fine. So reset the consecutive errors
                
                data_decoded = json.loads(data)

                #if data_decoded["success"] != True: continue
                if data_decoded["result"] != "success": continue
                #transactions = data_decoded["payments"]
                transactions = data_decoded["transactions"]
                offset += len(transactions)
                print "Total transactions in this page are: %d" % len(transactions)


                fileOut.write(json.dumps(data_decoded))
                fileOut.write("\n")


                #if len(transactions) > 0: print "Last transaction in this page was executed at: ", transactions[-1]["payment"]["timestamp"]
                if len(transactions) > 0: print "Last transaction in this page was executed at: ", transactions[-1]["tx"]["executed_time"]


                if len(transactions) < RESULTS_PER_PAGE - 10:
                    print "Not complete %d transactions in this page. Only got %d instead. So this sould be the last page." % (RESULTS_PER_PAGE, len(transactions))
                    print "SUCCESS: %s" % account
                    break
                

                """
                    Data of this page is saved, decide next ledgers
                """

                # since this call was execute properly,
                retries -=1 # decrement the RETRIES since this try was executed successfully

               # all_ledgers_of_transactions = []
               # for t in transactions:
               #     ledger_number = int(t["ledger"])
                    # print ledger_number
               #     all_ledgers_of_transactions.append(ledger_number)

               # end_ledger = min(all_ledgers_of_transactions) - 1 # get the next max ledger
                

                print "\n"
                sys.stdout.flush()
            except:
                # e = str(traceback.print_exc())
                e = str(sys.exc_info()[0]) + ' ' + str(sys.exc_info()[1])
                print "Error is:", e
                sys.stdout.flush()
                
                
                if "HTTP Error 5" in e or "Name or service not known" in e: # a gateway error starting with 5 (501, 502, 504)
                    cons_gateway_errors += 1
                    if cons_gateway_errors > MAX_CONSECUTIVE_ERRORS: break # if these many consecutive errors, then just move on
                    sleep_time = cons_gateway_errors * 60
                    print "%d consecutive gateway errors. So sleeping for %d" % (cons_gateway_errors, sleep_time)
                    time.sleep(sleep_time)

                continue



if __name__ == "__main__":
    main()

