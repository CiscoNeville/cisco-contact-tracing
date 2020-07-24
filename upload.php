<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
		<title>Prime Infrastructure Contact Tracer</title>
		<meta name="author" content="Neville Aga" />
		<!-- Date: 2020-06-05 -->
        <link type="text/css" rel="stylesheet" href="style.css" />
    </head>

   <body>

<?php
if (isset($_POST['submit'])) {
	$file = $_FILES['userfile'];

	$fileName = $_FILES['userfile']['name'];
	$fileTmpName = $_FILES['userfile']['tmp_name'];
	$fileSize = $_FILES['userfile']['size'];
	$fileError = $_FILES['userfile']['error'];
	$fileType = $_FILES['userfile']['type'];

	$fileExt = explode('.', $fileName);
	$fileActualExt = strtolower(end($fileExt));

	$allowed = array('csv');

#	print "<p> filename is $fileName </p>" ;
#	print "<p> file size is $fileSize </p>" ;


	if (in_array($fileActualExt, $allowed)) {
		if ($fileError === 0) {
			if ($fileSize < 100000000) {
				$fileNameNew = uniqid('', true).".".$fileActualExt;
				$fileDestination = '/var/www/html/uploads/'.$fileName;
				move_uploaded_file($fileTmpName, $fileDestination);
				header("Location: home.php?uploadSuccess=$fileName");
				echo "file tmp name is $fileTmpName <br>";
				echo " file destination is $fileDestination <br>";

				echo "uploaded";
			} else {
				echo "Your file is too big!";
			}
		} else {
			echo "There was an error uploading your file!  Check your file size. Max allowed right now is 80 Mb";
		}
	} else {
		echo "<h2>   &nbsp &nbsp &nbsp &nbsp <img src=\"small_bw_cisco_logo.png\" style=\"vertical-align:bottom\">  &nbsp Prime Infrastucture Proximity Tracing Tool</h2>   <h1>Error</h1>   <h3>You can only upload .csv files to this site.<br><br> The file has to be an report from a Cisco Prime Infrastructure server, and it has to be in the format described in <a href=\"http://blog.agafamily.com/?p=422\">  blog.agafamily.com/?p=422 </a><br> Please go back and try again</h3>";
	}

}
?>

</body>
</html>
