#!/usr/bin/perl
#
#
use strict;
#use warnings;
use Data::Dumper;
use Time::Piece;
use Time::Seconds;
use CGI ':standard';
use DateTime::Duration;
use DateTime::Format::Duration;

my $q = CGI -> new;

# get MAC address of consideration on cli in hh:hh:hh:hh:hh:hh format
my $inFile = $q->param("Logfile");
my $inputMAC = $q->param("SpreaderMAC");
$inputMAC =~ s/^\s+|\s+$//g;  #trim whitespace from before or after mac in input
$inputMAC = lc($inputMAC);  #make the input MAC lower case
my $analysisResolution = $q->param("TimeResolution"); # 300 is data points every 5 minutes
my $RSSIAbsDiffTolerance = $q->param("RSSIdiff");   #RSSI differenece above this will not be considered interactions between the 2 clients
my $StarttimeSecAfterFirstLogTimestamp = $q->param("OffsetStart");   #0 considers the whole log file


#Read in input log
$inFile = '/var/www/html/uploads/'.$inFile;   #file goes in this directory
my @words;
my @lines;
open (INFILE, "<", $inFile) or die "Can't open the file $inFile";
while (my $line = <INFILE>) {
    chomp ($line);
    push (@lines, $line);
}
close (INFILE);
#remove first 7 lines of logfile, putting that data into variables for report headers
my $ReportTitle = $lines[0];
my $ReportingPeriod = $lines[3];
#print "$ReportTitle \n  $ReportingPeriod \n  $ColumnHeaders \n";

#Parse the csv to find what row the column headers are in. can vary based on how they submit a report
my $i = 0;
my $rowContainingHeaders;
for (@lines) {
  if ($lines[$i] =~ 'Client Sessions') { #The row prior to the header row will say 'Client Sessions' only
    $rowContainingHeaders = $i + 1;  #want to get the row below 'Client Sessions' line
  }
  $i++;
}
#if it can't find a 'Client Sessions' line stop and throw an error.
unless (defined $rowContainingHeaders) {
  print header();
  print start_html(-title => " fatal error - bad input file",  -style=>{-src=>'/style.css'});
  print "<body style=background-color:#d7fefe>";
  print "<h2> Error - the input csv file does not appear to be a client sessions report.<br>This tool requires a Prime Infrastructure client sessions report with the fields as specified in the instructions.<br><br>From the PI home screen, choose Reports -> Report Launch Pad -> Client -> Client Sessions.<br><br> Go back and try again</h2>";
  print '<p>ciscoProximityTracer.com is tested with Prime Infrastructure 3.6. If you are using a differnt verion and submitted a Client Sessions report and still get this error, please notify neaga@cisco.com</p>';
die;
}

#if the headers are not the exact needed fields stop and throw error. todo
my $ColumnHeaders = $lines[$rowContainingHeaders];   #usually line number 6
my @ColumnHeaderFields = split /,/, $ColumnHeaders;
unless (($ColumnHeaderFields[0] eq 'Client Username') && ($ColumnHeaderFields[1] eq 'Client IP Address') && ($ColumnHeaderFields[2] eq 'Client MAC Address')  && ($ColumnHeaderFields[3] eq 'Association Time')  && ($ColumnHeaderFields[4] eq 'AP Name')&& ($ColumnHeaderFields[5] eq 'Session Duration') && ($ColumnHeaderFields[6] =~ 'RSSI')  ){
  print header();
  print start_html(-title => " fatal error - bad input file",  -style=>{-src=>'/style.css'});
  print "<body style=background-color:#d7fefe>";
  print "<h2> Error - the input csv file appears to be a client sessions report, but does not contain the correct fields in the correct order.<br>This tool requires a Prime Infrastructure client sessions report with the fields as specified in the instructions.<br><br>The fields must be Client Username, Client IP address, Client MAC Address, Association Time, AP Name, Session Duration, and RSSI, all in that order.<br><br> Go back and try again</h2>";
  print '<p>ciscoProximityTracer.com is tested with Prime Infrastructure 3.6. If you are using a differnt verion and submitted a valid Client Sessions report with exactly the above fields and still get this error, please notify neaga@cisco.com</p>';
  print "<p>$ColumnHeaderFields[0] $ColumnHeaderFields[1] $ColumnHeaderFields[2] $ColumnHeaderFields[3] $ColumnHeaderFields[4] $ColumnHeaderFields[5] $ColumnHeaderFields[6]   </p>";
die;
}


@lines = @lines [ $rowContainingHeaders + 1 .. $#lines ];   #data usually in 7 through EOF
my $numberOfLines = scalar @lines;

#determine the starttime and endtime by parsing input and using earliest start / end time in input
my $EarliestSessionStartTime = "2453890000"  ;   # this is roughly May 19, 2050;
my $LatestSessionStartTime = "0" ;  #This is Jan 1, 1970
my $i=0;
for (@lines) {
    @words = split /,/, $lines[$i];
    my $timeWithoutTimezone = substr ($words[3], 0, -9) . substr ($words[3], -4);  # Takes out the 3 digit timezone like CDT or MST
    my $t1 = Time::Piece->strptime("$timeWithoutTimezone","%a %b %d %k:%M:%S %Y");
    my $sessionStartTime = $t1->epoch;
    if ($sessionStartTime < $EarliestSessionStartTime){
        $EarliestSessionStartTime = $sessionStartTime;
    }
    if ($sessionStartTime > $LatestSessionStartTime){
         $LatestSessionStartTime = $sessionStartTime;
     }
    $i++;
}
my $logStartTime = $EarliestSessionStartTime;
my $hrLogStartTime = localtime $logStartTime;

my $logDuration = $LatestSessionStartTime - $EarliestSessionStartTime;
my $endTime = $logStartTime + $logDuration;
my $hrEndTime = localtime $endTime;

my $hrLogDuration = Time::Seconds->new($logDuration)->pretty;

my $startTime = $logStartTime + $StarttimeSecAfterFirstLogTimestamp;
my $hrStartTime = localtime $startTime;
my $analysisDuration = $endTime - $startTime;


my ($SpreaderMacAddress, $SpreaderAPName, $SpreaderRSSI, $ReceiverMacAddress, $ReceiverAPName, $ReceiverRSSI, $RSSIDiff);
my ($SpreaderAP, $ReceiverMACAddress, $ReceiverAP);
my ($SessionStartTimeRelative, $SessionEndTimeRelative, $ctRelative);  #when you want human readable analysis to start at at 0, not Jan 1970
my $j = 1;   #start with ClientMacs[1], not of [0]
my (@considerTime, @ConsiderTimeRelative); #relative to start of log or start of analysis?  Start of analysis, I think
my ($ClientUsername, $ClientIPAddress, $ClientMacAddress, $APName, $SessionDuration, $RSSI, $AssociationTime);

my (@Timeslice,@ReceiverArray,@ClientMacs);
my (%Client, %ClientH, %ClientUsernameFromMac);


sub duration_to_hms {
  my ($duration) = @_;
  my $formatter = DateTime::Format::Duration->new(
#    if ($duration >= 3600){
#    pattern => "%H hours %M minutes",
#} else {
#    pattern => "%M minutes",
#}
    pattern => "%H hours %M minutes",
    normalize => 1,
  );
  return $formatter->format_duration($duration);
}




#create the @considerTime array
for(my $i = 0; $i <= $analysisDuration/$analysisResolution; $i++){
    push (@considerTime,$startTime+$analysisResolution*$i);
    push (@ConsiderTimeRelative,$analysisResolution*$i);
#    print("$i   $considerTime[$i]    $ConsiderTimeRelative[$i] \n");
    @Timeslice[$i*$analysisResolution] = [];  #create an empty array or hash. really not sure. but @Timeslice[4200] will be created

}
#push (@Timeslice[3],"this is zero\n");
#push (@Timeslice[3],"this is one\n");
#push (@Timeslice[3],"this is two\n");
#push (@Timeslice[3],"this is three\n");
#push (@Timeslice[3],"this is four\n");
#print $Timeslice[3][2];




#Go through the logfile and tag each entry with what distinct point(s) that entry convers in @considerTime
$i=0;
for (@lines) {
    @words = split /,/, $lines[$i];
        $ClientUsername = $words[0];
        $ClientIPAddress = $words[1];
        $ClientMacAddress = $words[2];
        $AssociationTime = $words[3];
        $APName = $words[4];
        $SessionDuration = $words[5];
        $RSSI = $words[6];
        chomp $RSSI;  #last element in line may have a carriage return. need to remove
#print "$i    ->$words[0]<- , ->$words[1]<-  , ->$words[2]<-  ,  ->$words[3]<-  ,  ->$words[4]<-  , ->$words[5]<- , ->$words[6]<-\n";

    $ClientUsernameFromMac{$ClientMacAddress} = $ClientUsername;
    my $AssociationTimeWithoutTimezone = substr ($AssociationTime, 0, -9) . substr ($AssociationTime, -4);  # Takes out the 3 digit timezone like CDT or MST
    my $t1 = Time::Piece->strptime("$AssociationTimeWithoutTimezone","%a %b %d %k:%M:%S %Y");
    my $sessionStartTime = $t1->epoch;
    #parse the session duration. if min and sec, convert to sec.
    my $sessionDurationSeconds;
    if ($SessionDuration =~ "min"){
        my @w2 = split / /, $SessionDuration;
        $sessionDurationSeconds = $w2[0]*60 + $w2[2];
    } else {
        my @w2 = split / /, $SessionDuration;
        $sessionDurationSeconds = $w2[0]
    }
    my $sessionEndTime = $t1->epoch + $sessionDurationSeconds;
#print "session start time is " , $sessionStartTime , "   session end time is $sessionEndTime   duration is $sessionDurationSeconds\n";
    $SessionStartTimeRelative = $sessionStartTime - $startTime ;
    $SessionEndTimeRelative = $sessionEndTime - $startTime;
#print "$i    ->$ClientMacAddress<- , ->$SessionStartTimeRelative<-  , ->$SessionEndTimeRelative<-  ,  ->$APName<-  ,  ->$RSSI<-\n";

#for each hit, add the data to a new array for that time
for (@ConsiderTimeRelative) {
    if (($SessionStartTimeRelative <= $_) && ($SessionEndTimeRelative >= $_))  {
        push @{@Timeslice[$_]},"$i,$ClientMacAddress,$SessionStartTimeRelative,$SessionEndTimeRelative,$APName,$RSSI";
    }
}

    #create a hash of all Client Macs seen, used later when building hit array
    if (exists $Client{"$ClientMacAddress"})  {
 #       print "The key $ClientMacAddress already existed in the hash. j is $j. nothing further to do\n";
    } else {
        $Client{"$ClientMacAddress"} = $j;
#        print "The key $ClientMacAddress did not exist in the hash before, but now it does. j is $j.\n";
        $ClientH{"$j"} = $ClientMacAddress;
        $j++;

    }


$i++;
}
#at this point you will have something like $Timeslice[42000][2] = 10178,08:3a:88:02:5c:ad,40465,42239,AAP36-Evan_Bedroom,-57
#  print "$Timeslice[42000][2] \n";







my $TotalNumberOfClientMacs = scalar keys %Client;
#print "In this logfile there were a total of $TotalNumberOfClientMacs Client Mac Addresses\n";
#print "$_\n" for keys %hash;
#print '$Client{00:90:c2:f4:b3:8a}  is ' , "$Client{'00:90:c2:f4:b3:8a'}\n";
#print '$ClientH{32}  is ' , "$ClientH{32}\n";
$j=1; #Reset j


#create the blank @ReceiverArray  array of arrays
for(my $i = 1; $i <= $TotalNumberOfClientMacs; $i++){
    @ReceiverArray[$i] = [];  #create an empty array of arrays.   @ReceiverArray[7] will be created
}




#now loop from the beginning , find #inputMAC at each time slice
for (@ConsiderTimeRelative) {
        for my $index ( 0..$#{ $Timeslice[$_] } ) {
        #print "\t", $Timeslice[$_][$index], "\n";

            if ($Timeslice[$_][$index] =~ $inputMAC) {#my inputMAC was alive at this timeslice. get details

            my @w3 = split /,/, $Timeslice[$_][$index];
                      #$index2 = $w3[0];
                      #$ClientMacAddress = $w3[1];
                      #$AssociationStartTime = $w3[2];
                      #$AssociationEndTime = $w3[3];
                      $SpreaderAP = $w3[4];
                      $SpreaderRSSI = $w3[5];
#                print "\t", "At Timeslice $_ Spreader was at $SpreaderAP with RSSI = $SpreaderRSSI" , "\n";

 #Since found, find other MAC(s) at the same AP, similar RSSI -- add that data point to an array for the desitination MAC
                for my $index3 ( 0..$#{ $Timeslice[$_] } ) {

                if ($Timeslice[$_][$index3] !~ $inputMAC) { #obviously dont get inputMAC again
                my @w4 = split /,/, $Timeslice[$_][$index3];
                                 #$index2 = $w3[0];
                                 $ReceiverMACAddress = $w4[1];
                                 #$AssociationStartTime = $w3[2];
                                 #$AssociationEndTime = $w3[3];
                                 $ReceiverAP = $w4[4];
                                 $ReceiverRSSI = $w4[5];
              #  print "\t", "At Timeslice $_ Receiver $ReceiverMACAddress was at $ReceiverAP with RSSI = $ReceiverRSSI" , "\n";

                my $AbsRssiDiff = abs($SpreaderRSSI - $ReceiverRSSI);
     #Now, put this in an array if the spreader and receiver are on the same AP here within RSSI tolerance
                if (($SpreaderAP eq $ReceiverAP)  && ($AbsRssiDiff <= $RSSIAbsDiffTolerance)){
#    print "\t", "At Timeslice $_ Receiver $ReceiverMACAddress was at $ReceiverAP with RSSI difference = $AbsRssiDiff" , "\n";


                       push @{@ReceiverArray[$Client{$ReceiverMACAddress}]},"$ReceiverAP";

                        #Remember, $Client{00:90:c2:f4:b3:8a}  is 32
                        # and $ClientH{32}  is  00:90:c2:f4:b3:8a
                    }

                }
                }
            }
    }
 #   print "\n";
}
#At this point you will have something like $ReceiverArray[10][1] = "AAP35-Garage"
#and @ReceiverArray[10] = [AAP35-Garage,AAP35-Garage,AAP35-Garage,AAP33-Master_Bedroom,AAP35-Garage]

#print "$ReceiverArray[10][0]\n";
#print "$ReceiverArray[10][1]\n";
#print "$ReceiverArray[10][2]\n";
#print "@{@ReceiverArray[16]} \n";   #have to dereference the array of arrays
#for(my $i = 1; $i <= $TotalNumberOfClientMacs; $i++){
#   print "$i - $ClientH{$i} ->  @{@ReceiverArray[$i]} \n";
#}


#Sort all arrays based on number of hits (seconds in contact)
my @ContactPoints;
my @Unsorted;

for(my $i = 1; $i <= $TotalNumberOfClientMacs; $i++){
    $ContactPoints[$i] = scalar @{@ReceiverArray[$i]};
#    print "$i - $ClientH{$i} ->  $ContactPoints[$i] \n";
    $Unsorted[$i] = "$ContactPoints[$i],$i";  #This produces something like 237,16 #meaning that mac[16] was at the same place as spreader for 237 timeslices
}

#Figure out all the APs that go with each Receiver, find the total count of unique APs and the most common AP
my %counts;
my @NumAPs;
my $MostCommonAP;
for(my $i = 1; $i <= $TotalNumberOfClientMacs; $i++){
    $counts{$_}++ for @{@ReceiverArray[$i]};
    $MostCommonAP = (\%counts);
#    print Dumper(\%counts);
    my %h = %$MostCommonAP;
    my @SortedAPs = reverse sort { $h{$a} <=> $h{$b} } keys %h;
 #   print "@heights \n";
  #  print "higest is $SortedAPs[0]\n\n\n\n";
    undef %h;
    $NumAPs[$i] = scalar keys %counts;
    $Unsorted[$i] = $Unsorted[$i] . ",$NumAPs[$i]" . ",$SortedAPs[0]";   #adding to end of string so 237,16 becomes 237,16,7,AAP33-Master_Bedroom meaning at 7 distinct APs and AAP33 is most common
    undef %counts;
}

#print "at 16 --- $NumAPs[16] --- and $Unsorted[16] \n";


my @SortedOrder = reverse sort { "$a" <=> "$b" } @Unsorted;   #warning throws issue about being non-numberic. but still works
#print "@SortedOrder \n";





#print it out
my $k=0;

##########################################
print header();
print start_html(-title => " results",  -style=>{-src=>'/style.css'});

print "<body style=background-color:#e7fefe>";

print '<!-- Global site tag (gtag.js) - Google Analytics -->';
print '<script async src="https://www.googletagmanager.com/gtag/js?id=UA-57061804-2"></script>';
print '<script>';
print ' window.dataLayer = window.dataLayer || [];   ';
print ' function gtag(){dataLayer.push(arguments);}  ';
print '  gtag(\'js\', new Date());   ';
print '  gtag(\'config\', \'UA-57061804-2\');  ';
print '</script>';



print "<i>";
print "<p style=color:red>";

print " Using input file of $inFile<br>";
print " Using analysis resolution of $analysisResolution seconds<br>";
print " Using maximum RSSI difference of $RSSIAbsDiffTolerance<br>";
print " Using time offset of $StarttimeSecAfterFirstLogTimestamp seconds after first input logfile timestamp<br>";

print " Log begins at $hrLogStartTime<br>";
print " Log ends at   $hrEndTime<br>";
print "  Total log duration $hrLogDuration<br><br>";

print "</p>";
print "</i>";

print "<strong>Analyzing Spreader $inputMAC \[$ClientUsernameFromMac{$inputMAC}\] for the period $hrStartTime  through $hrEndTime</strong><br><br>";

for(@SortedOrder){
    my @w5 = split /,/, $_;
    my $TimeHits = $w5[0];
    my $MacNum = $w5[1];
    my $TotalNumberOfConcurrentAPs = $w5[2];
    my $MostCommonAP = $w5[3];
    my $TotalNumberOfConcurrentAPsMinusOne = $TotalNumberOfConcurrentAPs - 1;
    if ($TimeHits > 0)  { #don't bother if macs were never together
        my $TotalContactTime = $TimeHits * $analysisResolution ;
        my $hrTotalContactTime = DateTime::Duration->new(seconds => $TotalContactTime);
        my $hr2TotalContactTime = duration_to_hms($hrTotalContactTime);
        print "Total contact time of $hr2TotalContactTime ($TotalContactTime seconds) with $ClientH{$MacNum}  \[$ClientUsernameFromMac{$ClientH{$MacNum}}\] at $MostCommonAP";
        if ($TotalNumberOfConcurrentAPs >= 3) {
            print " and $TotalNumberOfConcurrentAPsMinusOne other APs <br>";
        } elsif ($TotalNumberOfConcurrentAPs == 2) {
            print " and 1 other AP <br>";
        } else {
            print "<br>";
        }
        $k++;
    }
}

print "<br><strong>In this logfile there were a total of $TotalNumberOfClientMacs Client Mac Addresses.  A total of $k of those clients came into contact with the spreader </strong> <br>";
print "</body>";
print end_html();
