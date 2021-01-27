# zvh4 conversion utility powershell script
# Author: Kevin Krieger
# Date: Jan 2021
# Requires the InstrumentView.exe executable installed in C:\Program Files (x86)\Rohde-Schwarz\InstrumentView\
# There may be a way to get the path to the executable automatically, but I haven't figured it out.
#
# Usage: 
#
# .\zvh4_convert_to_csv.ps1 [path to dataset .set files] [pattern to convert to csv]
#
# Example: .\zvh4_convert_to_csv.ps1 D:\sas_20210127 sas-vswr*.set
#
# The output will print out the arguments you supplied, and then print out which files it is converting
# and the resulting file name and location.
#
# ** NOTE ** If this hangs, then make sure you don't have any InstrumentView.exe processes running by using:
# 	taskkill /F /IM InstrumentView.exe /T 
# from a cmd line. Then try again


$drive_path = $args[0]
$pattern = $args[1]
Write-Output "Path to files: $($drive_path)"
Write-Output "Pattern to convert: $($pattern)"
Write-Output "Converting to CSV..." "" 

Get-ChildItem $drive_path -Filter $pattern |
Foreach-Object {
	# Get the file full name
	$filename = $_.FullName
	
	# Get the file base name
	$filebase = $_.BaseName
	
	# Make a new name for csv output file
	$csvname = $drive_path + $filebase + ".csv"
	
	# Print the names
	Write-Output "Converting $($filename) to $($csvname)"
	#Write-Output $filebase 
	#Write-Output $csvname
	
	# Call the InstrumentView conversion tool, make sure you tell powershell to wait for each one to end with | Out-Null
	& 'C:\Program Files (x86)\Rohde-Schwarz\InstrumentView\InstrumentView.exe' -ConvertToCSV $filename $csvname | Out-Null

}	