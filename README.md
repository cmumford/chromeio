# chromeio

Script to analyze File I/O for the Chrome web browser. This script is _mostly_
platform agnostic. However, it is currently designed to read output produced by
Process Monitor, so at present this is a Windows only tool.

## Prerequisites

1. Install [Process Monitor](http://technet.microsoft.com/en-us/sysinternals/bb896645.aspx).
2. Install [Python](https://www.python.org/).

## Gathering File I/O

1. Start Process Monitor. You will be presented with a "Process Monitor Filter"
   dialog. In order to only filter Chrome events you will want to add a filter
   rule: "Process Name + contains + chrome".
2. Press the OK button to begin capturing I/O events.
3. Uncheck File&#8594;Capture Events to cease the capture process.

## Analyzing I/O

Once you have a capture to analyze you will need to export the log as a CSV file.

1. Make sure "Time of Day" is the first column.
2. File &#8594; Save (CSV).

Now that you have the CSV file you are ready to run this tool.

    python chromeio <path/to/Logfile.CSV>

Here is an example report:

<pre>
python chromeio.py path/to/Logfile.CSV

Counted files (Written):
=============================
Total counted: 0

Categories (Written):
==========================
Cache                   : R[129.0MB=70.3%=  2.2GB/day], W[179.7MB=29.4%=  3.1GB/day]
Sync Data               : R[913.4KB= 0.5%= 15.6MB/day], W[149.0MB=24.4%=  2.5GB/day]
Other                   : R[211.3KB= 0.1%=  3.5MB/day], W[117.3MB=19.2%=  2.0GB/day]
Temp                    : R[    0 B= 0.0%=    0 B/day], W[ 80.7MB=13.2%=  1.4GB/day]
Extensions              : R[ 30.6MB=16.7%=535.0MB/day], W[ 33.8MB= 5.5%=590.3MB/day]
Cookies                 : R[    0 B= 0.0%=    0 B/day], W[ 18.0MB= 3.0%=314.5MB/day]
Web Data                : R[    0 B= 0.0%=    0 B/day], W[ 14.6MB= 2.4%=254.4MB/day]
History                 : R[    0 B= 0.0%=    0 B/day], W[  8.8MB= 1.4%=152.8MB/day]
Quota Manager           : R[    0 B= 0.0%=    0 B/day], W[  4.5MB= 0.7%= 79.2MB/day]
GCM Store               : R[    0 B= 0.0%=    0 B/day], W[  3.7MB= 0.6%= 63.9MB/day]
Current Session         : R[    0 B= 0.0%=    0 B/day], W[144.2KB= 0.0%=  2.4MB/day]
Safe Browsing           : R[    0 B= 0.0%=    0 B/day], W[121.6KB= 0.0%=  2.1MB/day]
Top Sites               : R[    0 B= 0.0%=    0 B/day], W[ 40.5KB= 0.0%=675.0KB/day]
GPU Cache               : R[    0 B= 0.0%=    0 B/day], W[ 19.1KB= 0.0%=253.1KB/day]
IndexedDB               : R[  1.9MB= 1.0%= 32.9MB/day], W[ 10.4KB= 0.0%=168.8KB/day]
Local storage           : R[    0 B= 0.0%=    0 B/day], W[  9.5KB= 0.0%= 84.4KB/day]
Filesystem              : R[ 63.9KB= 0.0%=  1.1MB/day], W[  1.2KB= 0.0%=    0 B/day]
Session storage         : R[    0 B= 0.0%=    0 B/day], W[  988 B= 0.0%=    0 B/day]
Service Worker          : R[ 20.8MB=11.4%=363.9MB/day], W[    0 B= 0.0%=    0 B/day]
Total                   : 640080430=610.4MB

Over 1:22:28, Chrome is:
  Reading 38900.3 Bps (3.1 GB/day)
  Writing 129361.4 Bps (10.4 GB/day)

IndexedDB:
==========
Profile 1-https_mail.google.com_0.indexeddb.leveldb         : R[    0 B= 0.0%=    0 B/day], W[  5.5KB= 0.0%= 84.4KB/day]
Default-https_drive.google.com_0.indexeddb.leveldb          : R[  1.9MB= 1.0%= 32.9MB/day], W[  4.4KB= 0.0%=    0 B/day]
Profile 1-chrome-extension_fpblyyyeebhea_0.indexeddb.leveldb: R[  2.1KB= 0.0%=    0 B/day], W[  458 B= 0.0%=    0 B/day]
</pre>
