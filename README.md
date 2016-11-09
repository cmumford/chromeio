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

Categories:
===========
Cache                  : 56359128 (53.7 MB) (55.4%)
Temp                   : 17829990 (17.0 MB) (17.5%)
IndexedDB              : 15484215 (14.8 MB) (15.2%)
Cookies                : 4760784 (4.5 MB) (4.7%)
Other                  : 3425280 (3.3 MB) (3.4%)
Sync Data              : 2260232 (2.2 MB) (2.2%)
Extensions             : 565680 (552.4 KB) (0.6%)
Sqlite temp            : 543372 (530.6 KB) (0.5%)
Local storage          : 246784 (241.0 KB) (0.2%)
GCM Store              : 97904 (95.6 KB) (0.1%)
Filesystem             : 68006 (66.4 KB) (0.1%)
Safe Browsing          : 25712 (25.1 KB) (0.0%)
GPU Cache              : 6512 (6.4 KB) (0.0%)
Media Cache            : 5920 (5.8 KB) (0.0%)
Session storage        : 2448 (2.4 KB) (0.0%)
Bookmarks              : 0 (0) (0.0%)
CRX Install            : 0 (0) (0.0%)
Favicons               : 0 (0) (0.0%)
Font Cache             : 0 (0) (0.0%)
Index Journal          : 0 (0) (0.0%)
JumpList Icons         : 0 (0) (0.0%)
Local State            : 0 (0) (0.0%)
PNACL                  : 0 (0) (0.0%)
Preferences            : 0 (0) (0.0%)
Shortcuts              : 0 (0) (0.0%)
Sync Extension Settings: 0 (0) (0.0%)
Total                  : 101681967 (97.0 MB)

Over 0:16:47, Chrome is
  reading 35815.1 Bps (2.9 GB/day)
  writing 100975.1 Bps (8.1 GB/day)

IndexedDB:
==========
Default-https_docs.google.com_0.indexeddb.leveldb           : 15484215 (14.8 MB) (15.2%)
</pre>
