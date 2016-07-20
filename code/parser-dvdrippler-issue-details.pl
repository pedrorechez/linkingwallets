

##################################################################
# CONFIGURATION
##################################################################

defined ($ARGV[0]) || die "Trace file is needed as first argument.\n";
defined ($ARGV[1]) || die "Output file is needed as second argument.\n";
defined ($ARGV[2]) || die "Currency is needed as third argument.\n";

$traze_file = $ARGV[0];  # Fichero de trazas a parsear correspondiente a la interfaz inalámbrica del nodo móvil (se pasa como 1er argumento)
$output_file = $ARGV[1];
$currency = $ARGV[2];


$index = 0;
$read_btc_link=0;
$read_xrp_link=0;
# Open trace file
open(IN, $traze_file) || die "Cannot open file $trace_file\n"; 

print ("Loading data from file $traze_file...\n");


while (defined($line = <IN>)) {	
	chop($line);

	if ($line =~ /<div class=\"amount>\"><span class=\"chainid\">$currency<\/span>\s+([^<]+)<\/div>/) {
#		print ("Amount $1\n");
		$amount = $1;
	}
	elsif ($line =~ /<div class=\"addr\"><span class=\"chainid\">$currency<\/span>\s+([^<]+)<\/div>/) {
#		print ("Incoming BTC address $1 \n");
		$btc_address = $1;
		$read_btc_link = 1;
	}
	elsif ($line =~ /<div><a href=\"([^\"]+)">/ ) {
		if ($read_btc_link) {		
#			print ("BTC link is $1 \n");
			$btc_link = $1;
			$read_btc_link = 0;
		}
		elsif ($read_xrp_link) {
#			print ("XRP link is $1 \n");
			$xrp_link = $1;
			$read_xrp_link = 0;
		}
	}
	elsif ($line =~ /<div class=\"ripple addr strong\">[^>]+>([^<]+)</) {
#		print ("Outgoing XRP address $1 \n");
		$xrp_address = $1;
		$read_xrp_link = 1;
	}
}

close IN;
	
print ("Parse finished\n");

print ("Number of links = $index \n");
print ("\n\n\n");


open (OUT, "> $output_file");
#print(OUT  "Storing data\n");

#for ($i=0; $i<$index; $i++) {

	#Store the tuples src dst tx_amount
	#printf (OUT "%s\t%s\t%.18f\n", $source[$i], $destination[$i], $tx_value[$i]);
#	print ("$ledger[$i]\t$sender[$i]\t$receiver[$i]\t$amount[$i]\n");
	printf (OUT "%s\t%s\t%s\t%s\t%s\n", $amount, $btc_address, $btc_link, $xrp_address, $xrp_link);
	#Store the tuples src dst tx_amount ledger type
#	printf (OUT "%s\t%s\t%.18f\t%ld\t%d\n", $source[$i], $destination[$i], $tx_value[$i], $ledger[$i], $type[$i]);

#}

close OUT;



