
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


BIGGEST_LEDGER = 2894321 # January 2015 ledger
SMALLEST_LEDGER = 32570 # CCS smallest ledger 
#BIGGEST_LEDGER = 14468739 # We are not setting it to -1, we will set it to a max value manually, otherwise, due to paginations, there could be some inconsistancies in the results retrieved. We set it up to the ledger in July 6th. close_time_human": "2015-Jul-06 09:14:30
#SMALLEST_LEDGER = 11446789 #CCS Biggest ledger + 1
RESULTS_PER_PAGE = 2000 # number of results per page
MAX_RETRIES_PER_ACCOUNT = 10
MAX_CONSECUTIVE_ERRORS = 10
SLEEP_PER_CALL = 1 # before calling any url
start_time = "2014-06-18T00:00:00"
finish_time = "2014-06-18T23:59:59"




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
        marker = "a"
        retries = 0
        call_number = 0
        cons_gateway_errors = 0 # number of consecutive bad gateway errors we got. we will multiply this with the wait time to make sure we eventually get the answer
        is_first_call = 1 # this is the first call, if retrieved successfully, we will use another URL format -- notce that it is different from call_number
        account_dictionary = dict()
        account_dictionary["account"] = account
        while 1: # iterate over all the pages for this account

            retries += 1
            if retries >= MAX_RETRIES_PER_ACCOUNT:
                print "Exceeded the quota for max retries for account %s. Breaking." % account
                break

            call_number += 1

            if is_first_call == 1:
                 url = "https://data.ripple.com/v2/accounts/" 
            else:
                 url = "https://data.ripple.com/v2/accounts?marker=%s" % (marker)
            
            
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
                #transactions = data_decoded["transactions"]
                if "marker" in data_decoded.keys():
                   print "Found marker! %s" % data_decoded["marker"]
                   if marker == data_decoded["marker"]:
                       print "No new marker in this page. So this sould be the last page." 
                       print "SUCCESS: %s" % account
                       break
                   marker = data_decoded["marker"]
                else:
					print "Marker is not found"
					marker = "a"
                
				
                print "Total transactions in this page are: %d" % data_decoded["count"]

                for i in data_decoded["accounts"]:
					account = i["account"]
					fileOut.write(account)
					fileOut.write("\n")


                #if len(transactions) > 0: print "Last transaction in this page was executed at: ", transactions[-1]["payment"]["timestamp"]
                #if len(transactions) > 0: print "Last transaction in this page was executed at: ", transactions[-1]["tx"]["executed_time"]


                #if len(transactions) < RESULTS_PER_PAGE - 10:
                if marker == "a":
                    print "No marker in this page. So this sould be the last page." 
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

