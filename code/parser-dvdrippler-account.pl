

##################################################################
# CONFIGURATION
##################################################################

defined ($ARGV[0]) || die "Trace file is needed as first argument.\n";
defined ($ARGV[1]) || die "Output file is needed as second argument.\n";

$traze_file = $ARGV[0];  # Fichero de trazas a parsear correspondiente a la interfaz inalámbrica del nodo móvil (se pasa como 1er argumento)
$output_file = $ARGV[1];


$read_line=0;
$index = 0;
# Open trace file
open(IN, $traze_file) || die "Cannot open file $trace_file\n"; 

print ("Loading data from file $traze_file...\n");


while (defined($line = <IN>)) {	
	chop($line);

	if ($line =~ /<td class=\"timestamp\">/) {
		if ($read_line == 0) {
			print("read a new transaction\n");
			$read_line=1;
		}
	}
	elsif ($line =~ /<td class=\"chainid\"><a href=\"([^\"]+)\">([^<]+)<\/a><\/td>/) {
		if ($read_line == 2) {
			$currency[$index] = $2;
			$link[$index] = $1;
#			print ("Currency := $2; Link := $1 \n");
			$read_line = 3;
		}
	}
	elsif ($line =~ /<td class=\"amount\"><a href=\".+\">([^<]+)<\/a><\/td>/) {
		if ($read_line == 3) {
#			print ("Amount := $1. Issued\n");
			$amount[$index] = $1;
			$issue_redeem[$index] = 'issued';
			$read_line = 4;
		}
		elsif ($read_line == 4) {
#			print ("Amount := $1. Redeemed\n");
			$amount[$index]=$1;
			$issue_redeem[$index] = 'redeemed';
			$read_line = 5;
		}
	}
	elsif ($line =~ /<td><\/td>/) {
		if ($read_line == 3 or $read_line == 4) {
#			print ("White space in line $read_line \n");
			$read_line = $read_line + 1;
		}
	}
	elsif ($line =~ /<td class=\"status\"><a href=[^>]+>([^<]+)<\/a><\/td>/) {
		if ($read_line == 5) {
#			print ("Transaction read completely. Status := $1 \n");
			$status[$index] = $1;
			$index = $index + 1;
			$read_line = 0;
		}
	}
	elsif ($line =~ /<a href=\"[c,r]d[^>]+>([^<]+)<\/a>/) {
		if ($read_line == 1) {
#			print ("Timestamp := $1 \n");
			$timestamp[$index] = $1;
			$read_line = 2;
		}
	}	
}

close IN;
	
print ("Parse finished\n");

print ("Number of links = $index \n");
print ("\n\n\n");


open (OUT, ">> $output_file");
#print(OUT  "Storing data\n");

for ($i=0; $i<$index; $i++) {

	#Store the tuples src dst tx_amount
	#printf (OUT "%s\t%s\t%.18f\n", $source[$i], $destination[$i], $tx_value[$i]);
#	print ("$ledger[$i]\t$sender[$i]\t$receiver[$i]\t$amount[$i]\n");
	printf (OUT "%s\t%s\t%s\t%s\t%s\t%s\n", $timestamp[$i], $currency[$i], $amount[$i], $status[$i], $link[$i], $issue_redeem[$i]);
	#Store the tuples src dst tx_amount ledger type
#	printf (OUT "%s\t%s\t%.18f\t%ld\t%d\n", $source[$i], $destination[$i], $tx_value[$i], $ledger[$i], $type[$i]);

}

close OUT;



