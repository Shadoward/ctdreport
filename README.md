# Python CTD Interactif Report Equinor Format

## Introduction
This python script will read a csv file exported from a CTD ".pos" file and create a CTD interactif report in the Equinor data format.

## Setup
Several modules need to be install before using the script. You will need:
+ `$ pushd somepath\ctdreport`
+ `$ pip install .`

## Pre Processing
Before you start using the python scritp you will need to prepare the files. Please follow the steps below:
+ Process and clean the data using CTD convertion and VBAProc;
+ Convert the .pos file in .csv file with only the good data;
+ Fill the ctdList.csv with the needed information, adding the csv file name without extension in the colunm FileName. A example of the file can be found in the tests folder. IMPORTANT: *Please do not use comma (,) in any colunms.*
+ If you have severals CTD file put them in one folder.

## Usage
```
usage: ctdreport.py [-h] ctdFolder ctdCSV

Create HTML CTD Report.

positional arguments:
  ctdFolder   ctdFolder (str): CTD folder path. This is the path where the files to process are.
  ctdCSV      ctdCSV (str): CTD csv list path. This is the CTD csv file path with all the needed information are for each CTD.

optional arguments:
  -h, --help  show this help message and exit

Example:
 To create the html interactif report from CTD csv data use python ctdreport.py c:/temp/ctd/ c:/temp/ctdList.csv
```

## Export products
* HTML Interactif Report
* CSV file with all information needed for the metadata

## TO DO:
+ Add SSDM option
