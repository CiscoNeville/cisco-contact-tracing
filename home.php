<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
	<head>
		<!-- Global site tag (gtag.js) - Google Analytics -->
		<script async src="https://www.googletagmanager.com/gtag/js?id=UA-57061804-2"></script>
		<script>
		  window.dataLayer = window.dataLayer || [];
		  function gtag(){dataLayer.push(arguments);}
		  gtag('js', new Date());

		  gtag('config', 'UA-57061804-2');
		</script>

		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
		<title>Prime Infrastructure Contact Tracer</title>
		<meta name="author" content="Neville Aga" />
		<!-- Date: 2020-06-05 -->
        <link type="text/css" rel="stylesheet" href="style.css" />
    </head>

   <body>


<script>
document.getElementById("file").onchange = function() {
	document.getElementById("fileUploadForm").submit();
}

</script>


<div class="header">
<h2>   &nbsp &nbsp &nbsp &nbsp <img src="small_bw_cisco_logo.png" style="vertical-align:bottom">  &nbsp Prime Infrastucture Proximity Tracing Tool</h2>
</div>

&nbsp
<br><br><br>

<!--banner and menu-->
	<?php
	$banner = '/var/www/html/banner-and-menu.html';
	$data = file($banner);
	foreach ($data as $line) {
		echo "$line";
	}
	 ?>

<h3>When you need to quickly and accurately find out who has been in close physical contact with a particular person on your campus, use this tool.</h3>

<p>This tool uses AP and RSSI data from a Cisco wireless infrastructure to identify people that have come into close physical contact with a given person. In a COVID-19 scenario if administration comes to
information technology and says "We just learned that Dr. X tested COVID-19 positive. I know he has been on campus the last 3 days. Who all did he expose while here?" this script will give an accurate comprehensive answer to that question. </p>

<p>To get started with this script, upload your <a href="http://blog.agafamily.com/?p=422">Prime Infrastructure Client Detail report</a> below. Once that data is uploaded you can use the buttons below to fine tune how close and how much time
was spent by the COVID spreader around COVID receivers. By default this looks for instances where the Spreader was connected to the same Access Point with an RSSI difference of 3dBm (corresponds roughly to 6 feet apart)
at the same time as a Receiver was connected. It then sorts out all the Receivers that the Spreader has come into contact with by time spent and listing where (which APs) the majority of the contact occurred. </p>

<p>For the script to run in a reasonable time (several seconds) limit your input file to under 10Mb. You can do that by exporting a shorter time window from the client detail report in prime (e.g., generate 3 reports each covering 1 day, instead of 1 report covering 3 days). The script will accept input files up to 80Mb in size.</p>

<br>
 <hr>





<table border="0px" cellpadding="4px" cellspacing="1px" >

<?php
if (empty($_GET[uploadSuccess])) {

  echo '<tr><td>';
	echo '<form action="upload.php" id="fileUploadForm" method="POST" enctype="multipart/form-data">';
	echo		'<input type="hidden" name="MAX_FILE_SIZE" value="800000000">';
	echo		'<input type="file" id="file" name="userfile" onchange="form.submit()"   >';
	echo    '<button type="submit" name="submit">Upload selected file </button> ';
#	echo    '<input type="submit" value="Upload Selected file">';
	echo  '&nbsp &nbsp &nbsp &nbsp &nbsp &nbsp &nbsp &nbsp Don\'t have a prime infrastructure deployment? Use this <a href="/sample_data.php">sample input file</a>';
	echo 	'</form>';



} else {

  echo '<tr><td>';
  echo "<form action=\"http://ciscoProximityTracer.com\"> ";
 	echo "Using the file <b> $_GET[uploadSuccess] </b> &nbsp &nbsp &nbsp &nbsp " 	;
 	echo "<input type=\"submit\" value=\"Use a different file\" ></form>";
  echo "</td></tr>";

  echo '<tr><td> <form action="/cgi-bin/PICT2.cgi" method="post" target="iframe_a">  ';
	echo '<label for="Logfile"> </label>';
	echo "<input type=\"hidden\" id=\"Logfile\" name=\"Logfile\" size=\"40\" value=\"$_GET[uploadSuccess]\"  >";
	echo "</td></tr>";
}
?>

<tr class=\"border_bottom\"> <td>
  <label for="SpreaderMac">Spreader MAC address:</label>
  <input type="text" id="SpreaderMac" name="SpreaderMAC">  format is hh:hh:hh:hh:hh:hh <br><br>
</td></tr>

<tr><td></td></tr>
<tr bgcolor="#FFF8F0"><td><i>-The below fields are optional and are used to fine tune visualizations between the spreader and receivers-</i></td></tr>

<tr bgcolor="#FFF8F0"><td>Max RSSI difference: <select name="RSSIdiff">
	<option value="0">0 - Exact Same RSSI values (less than 1 foot apart)</option>
	<option value="1">1dBm (approx 2' apart)</option>
	<option value="2">2dBm (approx 3' apart)</option>
	<option value="3" selected>3dBm (approx 6' apart)</option>
	<option value="5">5dBm  (approx 12' apart)</option>
	<option value="10">10dBm (approx 20' apart)</option>
	<option value="20">20dBm (approx 40' apart or separated by a wall</option>
	</select>
</td></tr>


<tr bgcolor="#FFF8F0"><td>Time resolution (higher time interval = faster compute)<select name="TimeResolution">
	<option value="5">5 seconds</option>
	<option value="60">1 minute</option>
	<option value="300" selected>5 minutes (default)</option>
	<option value="1800">30 minutes</option>
	<option value="3600">1 hour</option>
	</select>
</td></tr>



<tr bgcolor="#FFF8F0"><td>
  <label for="OffsetStart">Time after logfile start to start analysis (seconds)</label>
  <input type="number" value="0" id="OffsetStart" name="OffsetStart">  use a value of 0 to search through the entire logfile<br><br>
</td></tr>

<tr><td></td></tr>



<tr><td><b>	<input type="submit" value="Trace contact points with Spreader" /><br>	</b> </td></td></tr>

	</table>



	</form>

<hr>

 <iframe src="" name="iframe_a" style="border:none" width="1200" height="680"></iframe>

<p> PI proximity tracer tool by Neville Aga, <a href="https://www.twitter.com/CiscoNeville">@CiscoNeville</a> and <a href="mailto:neaga@cisco.com?subject=Feedback / question on your ciscoProximityTracer.com tool">neaga@cisco.com</a></p>



	</body>
</html>
