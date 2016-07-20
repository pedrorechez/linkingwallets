##################################
##################################
## Title: Script to perform heuristics over Ripple data
## Author: Pedro Moreno-Sanchez
## Email: pmorenos@purdue.edu
## Paper: Listening to Whispers of Ripple: Linking Wallets and Deanonymizing Transactions in the Ripple Network
## Website: http://crypsys.mmci.uni-saarland.de/projects/LinkingWallets
##################################

import networkx as nx
import json
import matplotlib.pyplot as plt
import numpy as np
import sqlite3 as lite
import ast
from collections import defaultdict
from matplotlib.patches import Rectangle
import time
import datetime
import operator
from pylab import *
import glob
from scipy.stats import poisson
import math
import itertools
import statsmodels as sm

####################
#Global variables
####################
POISSON_THRESHOLD = 0.27 #Threshold extracted from the KL divergence of Bitstamp, Ripplefox and Snapswap and Poisson distribution with \lambda =1 

##Currency exchanges
CURRENCY_TO_USD = {
	
	"USD" : 1.0,
	"ARS" : 0.064,
	"AUD" : 0.71,
	"BRL" : 0.25,
	"BTC" : 434.74,
	"CHF" : 1.00,
	"CNY" : 0.15,
	"CZK" : 0.040,
	"DKK" : 0.15,
	"EUR" : 1.09,
	"GBP" : 1.39,
	"HKD" : 0.13,
	"ILS" : 0.26,
	"INR" : 0.015,
	"JPY" : 0.0088,
	"SEK" : 0.12,
	"XRP" : 0.0079,
	"CAD" : 0.74,
	"RUB" : 0.013,
	"LTC" : 3.45,
	"MXN" : 0.055,
	"NOK" : 0.12,
	"NZD" : 0.66,
	"PLN" : 0.25,
	"SGD" : 0.71,
	"SLL" : 0.00025,
	"THB" : 0.028,
	"ZAR" : 0.0617,
	"KRW" : 0.00080,
	"NMC" : 0.42
}




def kl(dist, nelem):
#Kullback-Leibler divergence D(P || Q) for discrete distributions

#Parameters
#----------
#p, q : array-like, dtype=float, shape=n
#Discrete probability distributions.
	
	
	it = 1
	my_lambda = 1.0
	poisson =  []
	while it <= nelem: 
		poisson.append( exp(-1 * my_lambda) * my_lambda**it / math.factorial(it) )
		it+=1
		
	p = np.asarray(poisson, dtype=np.float)
	q = np.asarray(dist, dtype=np.float)

	return np.sum(np.where(p != 0, p * np.log(p / q), 0))




##Procedure to extract the potential hot-cold wallets links
##Each line in the input file: TRUST_LINES_FILE must have the format:
## {"result":{"account":"r11bsqzfg9qhiQnVNzWfMLTzC9hMTVaUu","ledger_current_index":14938426,"lines":[],"validated":false},"status":"success","type":"response"}
##As extracted from Ripple server	
def extract_non_xrp_cold_hot_wallets_links():
	extract_raw_lines = 0
	
	if extract_raw_lines:
		#first I need to extract the lines in raw with no checks
		fileOut = open(TRUST_LINES_RAW_FILE, 'w')
		for line in open(TRUST_LINES_FILE, 'r'):
			data = json.loads(line)
			for link in data['result']['lines']:
				fileOut.write('["%s", %s]\n' % (str(data['result']['account']), json.dumps(link)))
	
	
	
	
	#calculate the possible cold -hot wallets links
	dic = defaultdict(list)
	dic2 = defaultdict(list)
	dic3 = defaultdict(list)
	dic4 = defaultdict(list)
	
	
	revdic = defaultdict(list)
	revdic2 = defaultdict(list)
	revdic3 = defaultdict(list)
	revdic4 = defaultdict(list)
	
	fileOut = open(NON_XRP_RAW_COLD_HOT_WALLETS_FILE, 'w')	
	#fileOut = open("text.txt", 'w')	
	
	print 'reading trust lines'
	for line in open(TRUST_LINES_RAW_FILE, 'r'):
		data = json.loads(line)
		
		#getting info for cw, hw entries
		dic[str(data[0])].append(float(data[1]["limit"])) #To the receiver of the link, we add the trust limit
		dic2[str(data[0])].append(float(data[1]["limit_peer"])) #To the receiver of the link, we add the trust limit
		dic3[str(data[0])].append(line)
		dic4[str(data[0])].append(float(data[1]["balance"]))

		#getting info for hw, cw entries
		revdic[str(data[1]["account"])].append(float(data[1]["limit"])) #To the receiver of the link, we add the trust limit
		revdic2[str(data[1]["account"])].append(float(data[1]["limit_peer"])) #To the receiver of the link, we add the trust limit
		revdic3[str(data[1]["account"])].append(line)
		revdic4[str(data[1]["account"])].append(float(data[1]["balance"]))
	
	print 'first round'
	#Check direction cw, hw
	for key in dic.keys():
		limit=0
		limit_peer=0
		balance_ok = 1
		for v in dic[key]:
			limit += v
		for v in dic2[key]:
			limit_peer += v
		if limit == 0 and limit_peer > 0:
			for v in dic3[key]:
				info = json.loads(v)
				if info[1]["limit_peer"] != '0' and info[1]["limit"] == '0':
					#print info[1]["balance"]
					fileOut.write(''+info[0]+' '+info[1]["account"]+'\n')

	print 'second round'
	#Check direction hw, cw
	for key in revdic.keys():
		limit=0
		limit_peer=0
		
		for v in revdic[key]:
			limit += v
		for v in revdic2[key]:
			limit_peer += v
		if limit_peer == 0 and limit > 0:
			for v in revdic3[key]:
				info = json.loads(v)
				if info[1]["limit_peer"] == '0' and info[1]["limit"] != '0':
					fileOut.write(''+info[1]["account"]+' '+info[0]+'\n')
	


##Procedure to perform the clustering of Ripple wallets (heuristic 2)
##NON_XRP_RAW_COLD_HOT_WALLETS_FILE must be created from 
##extract_non_xrp_cold_hot_wallets procedure

def heuristic2_perform_clustering():
	#read the possible cold-hot wallets links
	possible_cold_hot_wallets_pairs = defaultdict(set)
	possible_cold_wallets = set()
	possible_hot_wallets = set()
	
	##Flags for the different functionalities
	extract_payments_cold_to_hot = 0
	calculate_distributions = 0
	check_consistency = 0
	check_divergence = 0
	perform_clustering = 0
	check_periodic_payments = 0
	
	
	if extract_payments_cold_to_hot:
		if extract_payments_cold_to_hot:
			fileOut = open(NON_XRP_COLD_TO_HOT_WALLET_PAYMENTS, 'w')
			
			for line in open(NON_XRP_RAW_COLD_HOT_WALLETS_FILE, 'r'):
				(cold_wallet, hot_wallet) = line.split(' ')
				cw = cold_wallet
				possible_cold_wallets.add(cw)
				hw = hot_wallet.strip()
				possible_hot_wallets.add(hw)
				possible_cold_hot_wallets_pairs[cw].add(hw)
			
			
			#read the transactions and annotate to how many hot wallets every cold wallet is sending money to
			paid_cold_hot_wallets_pairs = defaultdict(set)
			for line in open(TX_FILE_SANITIZED, 'r'):
				(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = line.split(',')
				if currency!='XRP' and src in possible_cold_wallets and dest in possible_hot_wallets:
					if dest in possible_cold_hot_wallets_pairs[src]:
						fileOut.write(src+' '+dest+'\n')
						
			
	if calculate_distributions:
		#Now, extract the distribution of payments for each cold wallet
		#First, get a dictionary of the form cw, [hw1, hw1, hw2, hw3, hw1...]
		dic = defaultdict(list)
		my_it=0
		for line in open(NON_XRP_COLD_TO_HOT_WALLET_PAYMENTS, 'r'):
			data = line.split(' ')
			dic[data[0]].append(data[1].strip())
			
		
		
		#second calculate the distributions
		fileOut = open(NON_XRP_COLD_TO_HOT_WALLET_PAYMENT_DISTRIBUTION, 'w')
		for cw in dic.keys():
			dic2 = defaultdict()
			total = 0.0
			for hw in dic[cw]:
				if hw not in dic2.keys():
					dic2[hw] = 1
				else:
					dic2[hw] += 1
				total += 1
			#Now we have for each cw, the list of all payed hw and how many times. 
			#Now we need to calculate the distribution

			
			dic3 = defaultdict() #This dictionary will keep the distributions
			for hw in dic2.keys():
				dic3[hw] = (dic2[hw]/total)
			
			
			fileOut.write(cw+'-'+json.dumps(dic3)+'\n')
	
		
	##Check that potential hot-cold wallets links are actually 
	##being used as hot-cold wallets	
	if check_consistency:
		fileOut = open(CONSISTENCY_FILE, 'w')
		#parse all payments
		payments = defaultdict(set)
		
		print 'reading payments'
		for line in open(TX_FILE_SANITIZED, 'r'):
			(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = line.split(',')
			
			payments[src].add(dest)
		
		print 'reading links'
		#parse all links
		links = defaultdict(set)
		for line in open(NON_XRP_RAW_COLD_HOT_WALLETS_FILE, 'r'):
			(cold_wallet, hot_wallet) = line.split(' ')
			links[cold_wallet].add(hot_wallet.strip())
		
		
		
		print 'checking correctness'
		it = 0
		#read the distributions
		for line in open(NON_XRP_COLD_TO_HOT_WALLET_PAYMENT_DISTRIBUTION, 'r'):
			it +=1
			data = line.split('-')
			cw = data[0]
			hws = json.loads(data[1].strip())
			
			if len(links[cw]) < 2 * len(hws.keys()): #if potential hws are not serving other connected wallets
				print 'ommiting cold wallet', cw
				continue 
			
			for hw in hws.keys():
				if len( (links[cw].intersection(payments[hw])) ) > 0: #if the cold wallet is paying to hot wallets
					line_to_file = ''+str(cw)+ ' ' + str(hw) + ' ' + str(hws[hw]) + '\n'
					fileOut.write(line_to_file)
			
	
	##Perform the KL divergence test over the distribution of the resulting
	## hot-cold wallets pairs		
	if check_divergence:
		fileOut = open("test-divergence.txt", 'w')
		#parse all payments
		payments = defaultdict(set)
		
		print 'reading payments'
		for line in open(TX_FILE_SANITIZED, 'r'):
			(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = line.split(',')
			
			payments[src].add(dest)
		
		print 'reading links'
		#parse all links
		links = defaultdict(set)
		for line in open(NON_XRP_RAW_COLD_HOT_WALLETS_FILE, 'r'):
			(cold_wallet, hot_wallet) = line.split(' ')
			links[cold_wallet].add(hot_wallet.strip())
		
		
		
		print 'checking distance'
		it = 0
		#read the distributions
		for line in open(NON_XRP_COLD_TO_HOT_WALLET_PAYMENT_DISTRIBUTION, 'r'):
			it +=1
			data = line.split('-')
			cw = data[0]
			#print 'problem reading line', it
			hws = json.loads(data[1].strip())
			
			
			sorted_hw = sorted(hws.items(), key=operator.itemgetter(1), reverse=True) #from smallest to biggest
			
			if len(sorted_hw) == 1:
				print 'accepting cw because only 1 hw', cw
				fileOut.write(line)
				continue
			
			
			
			#Calculate the statistical distance
			my_dist = []
			
			for elem in sorted_hw:
				my_dist.append(float(elem[1]))
			
			divergence = kl(my_dist, len(sorted_hw))
			
			if divergence < 0:
				divergence = divergence * (-1) #take absolute value
			
			if divergence > POISSON_THRESHOLD:
				print 'ommiting cold wallet', cw, 'received divergence is', divergence
			else:
				print 'accepting cold wallet', cw, 'received divergence is', divergence
				fileOut.write(line)
				
	
				
	if perform_clustering:
		fileOut = open(NON_XRP_COLD_WALLET_HEURISTIC_RESULT, 'w')
		
		#Read the cold wallets that have been finally assigned in the clustering
		cw_set = set()
		for line in open(NON_XRP_COLD_WALLETS_AFTER_THRESHOLD, 'r'):
			cw_set.add(line.strip())
		
		
		#Print the final clustering
		for line in open(NON_XRP_COLD_WALLET_HEURISTIC_PRERESULT, 'r'):
			(cw, hw) = line.split(' ')
			if cw in cw_set:
				fileOut.write(cw + ' ' + hw.strip() + '\n')
	
			

	if check_periodic_payments:
		fileOut = open('test-times.txt', 'w')
		TIME_BIN_1_MONTH = 2592000
		TIME_BIN_2_MONTHS = 5184000
		TIME_BIN_3_MONTHS = 7776000
		it_accounts = 0
		for line in open(FILE_FILTERED_LINKS_AFTER_KL_DIVERGENCE):
			dic_times = defaultdict(list)
			data = line.split('-')
			cw = data[0]
			hw_set = set()
			hws = json.loads(data[1])
				
			if len(hws) == 1:
				for hw in hws.keys():
					fileOut.write(''+cw+' '+ hw+'\n')
				continue
			
			
			for elem in hws.keys():
				hw_set.add(elem)
				
			for line in open(TX_FILE, 'r'):
				(tx_hash, sdr, rcv, currency, amt1, amt2, ledger, src_tag, dst_tag, crawl_src, ts) = line.split(',')
				
				if sdr == cw and currency != "XRP":
					if rcv in hw_set:
						dic_times[rcv].append(int(ts))
						
			for hw in dic_times:
				dic_times[hw].sort()
				
				#Check that is active for at least three months
				#print 'time difference is', dic_times[hw][len(dic_times[hw])-1] - dic_times[hw][0]
				if dic_times[hw][len(dic_times[hw])-1] - dic_times[hw][0] < TIME_BIN_3_MONTHS:
						print 'dropping because of not active three months', hw
						continue
				
				correct_timing = 1
				for it in range(0, len(dic_times[hw]), 1) :
					if it==0:
						continue
					
					if dic_times[hw][it] - dic_times[hw][it-1] > TIME_BIN_3_MONTHS:
						correct_timing =0
				
				if correct_timing:
					fileOut.write(''+cw+' '+hw+'\n')	
		
##Load the results of the heuristics into a graph
def load_heuristic2(graph):
	fileIn = open(NON_XRP_COLD_WALLET_HEURISTIC_RESULT, 'r')
	for line in fileIn:
		accs = line.split(' ')
		graph.add_node(accs[0])
		graph.add_node(accs[1].strip())
		graph.add_edge(accs[0], accs[1].strip())
	fileIn.close()
	
def load_heuristic1(graph):
	
	files = [BTC_RIPPLE_LINKS, LTC_RIPPLE_LINKS, NMC_RIPPLE_LINKS]
	
	for my_file in files:
		fileIn = open(my_file, 'r')
		for line in fileIn:
			accs = line.split('\t')
			graph.add_edge(accs[0], accs[1].strip())
		fileIn.close()
	for line in open(TRC_RIPPLE_LINKS, 'r'):
		accs = line.split('\t')
		graph.add_edge(accs[0], 't' + accs[1].strip())



##Printing information about the clustering of crypto currencies
def clustering_crypto_currencies(graph):
	comp=sorted(nx.connected_components(graph), key = len, reverse=True)
	
	
	data = []
	for c in comp:
		print_c = 0
		c_trc = 0
		c_nmc = 0
		c_ltc = 0
		
		c_alc = 0
		c_btc = 0
		c_rip = 0
		for node in c:
			if node[0] == 't':
				c_trc += 1
				c_alc += 1
				print_c += 1
			elif node[0] =='N':
				c_nmc += 1
				c_alc += 1 
				print_c += 1
			elif node[0] == 'L':
				c_ltc += 1
				c_alc += 1
				print_c += 1
			elif node[0] == '1':
				c_btc += 1
				print_c += 1
			elif node[0] == 'r':
				c_rip +=1
				print_c += 1
			
		if print_c:
			print [c_rip>0, c_btc>0, c_ltc>0, c_trc>0, c_nmc>0]
			
			
###Procedure to calculate transactions that includes wallets
### linked by our heuristics		
def extract_tx_involving_clustered_accs(graph):
	
	comp=sorted(nx.connected_components(graph), key = len, reverse=True)
	
	print 'calculate known_wallets and unknown_clustered_wallets'
	known_wallets = set() #Wallets for which publicly known owner
	unknown_clustered_wallets = set() #Wallets that our clustering associates to a known user
	for line in open(KNOWN_COLD_HOT_WALLET_PAIRS, 'r'):
		gw_data = json.loads(line)#get known information
		known_wallets.add(gw_data[1]) #add the cold wallet for every entry
		tmp_w = []
		for entry in gw_data[2]:
			if entry[0] != "":
				tmp_w.append(entry[0]) 
				known_wallets.add(entry[0])
		
	#extract the unknown wallets which have been clustered by our heuristics
	for c in comp:
		for acc in c:
			if acc[0] == 'r' and acc not in known_wallets: #If the clustered account is not the cold wallet of one of the known hot wallets
				unknown_clustered_wallets.add(acc)
		
				
	print 'parsing database'
	fileIn = open(TX_CLUSTERING, 'r')
	
	output1 = open(PUBLICLY_DEANONYMIZED_TX_FILE, 'w')
	output2 = open(CLUSTERING_DEANONYMIZED_TX_FILE, 'w')			
	output3 = open(TOTAL_ANONYMOUS_TX_FILE, 'w')			
	it = 0
	for entry in fileIn:
		it += 1
		if it % 100000 == 0:
			print 'checked up to tx', it
		(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = entry.split(',')
		
		
		if src in unknown_clustered_wallets and dest in known_wallets:
			output2.write(entry)
		elif src in known_wallets and dest in unknown_clustered_wallets:
			output2.write(entry)
		elif src in known_wallets or dest in known_wallets:
			output1.write(entry)
		else:
			output3.write(entry)

	
###Procedure to extract transactions involving the gateways 
##according to the findings of our heuristics
def deanonymize_gateways(graph):				
	split_payments_into_covered_uncovered = 1
	
	comp=sorted(nx.connected_components(graph), key = len, reverse=True)
	
	gw_names=[]
	gw_cold_wallet=[]
	gw_known_hot_wallet=[]
	gw_unknown_hot_wallet=[]
	covered_acc = set()
	uncovered_acc = set()
	for line in open(KNOWN_COLD_HOT_WALLET_PAIRS, 'r'):
		gw_data = json.loads(line)#get known information
		gw_names.append(gw_data[0])
		gw_cold_wallet.append(gw_data[1])
		covered_acc.add(gw_data[1])
		tmp_w = []
		for entry in gw_data[2]:
			if entry[0] != "":
				tmp_w.append(entry[0]) 
				covered_acc.add(entry[0])
		gw_known_hot_wallet.append(set(tmp_w))
		
		tmp_w2 = []
		for c in comp:
			if gw_data[1] in c:#get unknown information. Check the cluster
				for acc in c:
					if acc != gw_data[1] and acc not in tmp_w:
						tmp_w2.append(acc)
						uncovered_acc.add(acc)
		
		gw_unknown_hot_wallet.append(set(tmp_w2))

	
	if split_payments_into_covered_uncovered:
		fileIn = open(TX_FILE_SANITIZED, 'r')
		
		output1 = open(GATEWAYS_COVERED_TX_FILE, 'w')
		output2 = open(GATEWAYS_NOT_COVERED_TX_FILE, 'w')			
		it = 0
		for entry in fileIn:
			it += 1
			if it % 100000 == 0:
				print 'checked up to tx', it
			(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = entry.split(',')
			if src in uncovered_acc or dest in uncovered_acc:
				output2.write(entry)
				#output1.write('\n')
			elif src in covered_acc or dest in covered_acc:
				output1.write(entry)
				#output2.write('\n')
					

	count_uncovered = []
	count_covered = []
	
	for it in range(len(gw_names)):
		count_covered.append(0)
		count_uncovered.append(0)
				
	print 'parsing covered.txt'			
	fileIn = open(GATEWAYS_COVERED_TX_FILE, 'r')
	my_it=0
	for line in fileIn:
		my_it += 1
		if my_it %10000 == 0:
			print 'parsed until line', my_it
		try:
			(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = line.split(',')
		except ValueError:
			print 'something wrong with line', my_it
			continue
		for it in range(len(gw_names)):
			if src in gw_unknown_hot_wallet[it] or dest in gw_unknown_hot_wallet[it]:
				count_uncovered[it] +=1
			elif src == gw_cold_wallet[it] or dest == gw_cold_wallet[it]:
				count_covered[it] +=1
			elif src in gw_known_hot_wallet[it] or dest in gw_known_hot_wallet[it]:
				count_covered[it] +=1
			
	
	
	print 'parsing uncovered tx'			
	fileIn = open(GATEWAYS_NOT_COVERED_TX_FILE, 'r')
	my_it = 0
	for line in fileIn:
		my_it += 1
		if my_it %10000 == 0:
			print 'parsed until line', my_it
		try:
			(tx_hash, src, dest, currency, amount_before, amount_after, ledger, src_tag, dest_tag, crawl_src, timestamp) = line.split(',')
		except ValueError:
			print 'something wrong with line', my_it
			continue
		for it in range(len(gw_names)):
			if src in gw_unknown_hot_wallet[it] or dest in gw_unknown_hot_wallet[it]:
				count_uncovered[it] += 1
			elif src == gw_cold_wallet[it] or dest == gw_cold_wallet[it]:
				count_covered[it] +=1
			elif src in gw_known_hot_wallet[it] or dest in gw_known_hot_wallet[it]:
				count_covered[it] +=1
			
				
	
	fileOut = open(GATEWAYS_KNOWN_VS_UNKNOWN_TX_NUMBERS, 'w')
	for it in range(len(gw_names)):
		line = ''+ str(gw_names[it]) + ' ' + str(count_covered[it]) + ' '+  str(count_uncovered[it]) + ' ' + str(count_covered[it]+count_uncovered[it]) +  '\n'
		fileOut.write(line)




if __name__ == "__main__":
	
	G=nx.Graph()
	load_heuristic1(G)
	load_heuristic2(G)
	
	
