#!/usr/bin/env python

import codecs
import csv
import datetime
import glob
import locale
from operator import attrgetter, itemgetter
import os
import re
import sys
import time
from time import mktime
from datetime import datetime

# This script counts disk I/O on Windows. Use the Process Monitor tool to
# capture all I/O for a given process (chrome.exe). Then save out the main
# view to one CSV file, and then the File Summary to a second CSV
# file. Use this program to categorize the results.
#
# python chromeio.py [<file_filter.csv>] [<log_file.csv>]
#
# The two data file names are hard-coded below, but can be specified on the
# command line.

output_csv = False
# Process Monitor -> File -> Save... (to CSV) to this file.
procmon_log_name = 'ProcessMonitorLogfile.csv'
# Process Monitor -> Tools -> File Summary... -> Save to this file.
procmon_file_filter_name = 'ProcessMonitorFileFilter.csv'

if sys.argv > 1:
    procmon_file_filter_name = sys.argv[1]

if sys.argv > 2:
    procmon_log_name = sys.argv[2]

sort_by = 'written'
if sort_by == 'written':
    sort_title = 'Written'
else:
    sort_title = 'Read'

class Category(object):
    def __init__(self, name, total=None):
        self.name = name
        self.total = total
        self.read = 0
        self.written = 0

    def Increment(self, read, written):
        self.read += read
        self.written += written

    @staticmethod
    def GetFriendlySize(num_bytes):
        if num_bytes > 1024*1024:
            return "%.1f MB" % (num_bytes / 1024.0 / 1024.0)
        elif num_bytes > 1024:
            return "%.1f KB" % (num_bytes / 1024.0)
        else:
            return "%d" % num_bytes

    @staticmethod
    def GetBytesString(amount):
        return "%ld (%s)" % (amount, Category.GetFriendlySize(amount))

    @staticmethod
    def GetAmountString(amount, total):
        return "%s (%.1f%%)" % (Category.GetBytesString(amount),
                                100.0 * amount / total)

    @staticmethod
    def GetBothAmounts(read, written, total_read, total_written):
        return "R[%s], W[%s]" % (Category.GetAmountString(read, total_read),
                               Category.GetAmountString(written, total_written))

    def Print(self, name_col_width):
        if self.total:
            print "%s: %s" % (self.name.ljust(name_col_width),
                          Category.GetBothAmounts(self.read, self.written, total.read, total.written))
        else:
            print "%s: %s" % (self.name.ljust(name_col_width),
                              Category.GetBytesString(self.written))

    def PrintCsv(self):
        print "%s,%ld" % (self.name, self.written)

def is_leveldb_file(fname):
    b = os.path.basename(fname)
    base, ext = os.path.splitext(path)
    return 'MANIFEST' in b or ext == '.ldb' or ext == '.dbtmp'

def is_cookies_file(fname):
    b = os.path.basename(fname)
    return 'Cookies' in b

total = Category("Total")
null_category = Category("Null") # Never printed
cache = Category("Cache", total)
font_cache = Category("Font Cache", total)
cookies = Category("Cookies", total)
gpu_cache = Category("GPU Cache", total)
extensions = Category("Extensions", total)
idb = Category("IndexedDB", total)
local_state = Category("Local State", total)
local_storage = Category("Local storage", total)
media_cache = Category("Media Cache", total)
other = Category("Other", total)
preferences = Category("Preferences", total)
session_storage = Category("Session storage", total)
sqlite_temp = Category("Sqlite temp", total)
sync_data = Category("Sync Data", total)
sync_extension_settings = Category("Sync Extension Settings", total)
sync_app_settings = Category("Sync App Settings", total)
local_app_settings = Category("Local App Settings", total)
temp = Category("Temp", total)
shortcuts = Category("Shortcuts", total)
safe_browsing = Category("Safe Browsing", total)
index_journal = Category("Index Journal", total)
file_system = Category("Filesystem", total)
gcm_store = Category("GCM Store", total)
jump_list_icons = Category("JumpList Icons", total)
favicon = Category("Favicons", total)
pnacl = Category("PNACL", total)
bookmarks = Category("Bookmarks", total)
crx_install = Category("CRX Install", total)
visited_links = Category("Visited Links", total)
web_data = Category("Web Data", total)
history = Category("History", total)
quota_manager = Category("Quota Manager", total)
network_action_predictor = Category("Network Action Predictor", total)
current_sessions = Category("Current Sessions", total)
current_tabs = Category("Current Tabs", total)

categories = [
    bookmarks,
    cache,
    cookies,
    crx_install,
    extensions,
    favicon,
    file_system,
    font_cache,
    gcm_store,
    gpu_cache,
    idb,
    index_journal,
    jump_list_icons,
    local_state,
    local_storage,
    media_cache,
    pnacl,
    preferences,
    safe_browsing,
    session_storage,
    shortcuts,
    sqlite_temp,
    sync_data,
    sync_extension_settings,
    sync_app_settings,
    local_app_settings,
    temp,
    visited_links,
    web_data,
    history,
    quota_manager,
    network_action_predictor,
    current_sessions,
    current_tabs,
    other
]

idb_origin_categories = {}

def AddIDBOriginIO(origin, bytes_read, bytes_written):
    if origin in idb_origin_categories:
        category = idb_origin_categories[origin]
    else:
        category = Category(origin, total)
        idb_origin_categories[origin] = category
    category.Increment(bytes_read, bytes_written)

def GetCategory(path):
    base, ext = os.path.splitext(path)
    b = os.path.basename(path)
    if 'etilqs' in path:
        return sqlite_temp
    elif b.startswith('pnacl') or 'PnaclTranslationCache' in path:
        return pnacl
    elif 'Index-journal' == b:
        return index_journal
    elif 'Safe Browsing' in b:
        return safe_browsing
    elif '\\JumpListIcons\\' in path or b == 'JumpListIconsOld':
        return jump_list_icons
    elif 'IndexedDB' in path:
        return idb
    elif 'Favicons' in path:
        return favicon
    elif 'Bookmarks' in path:
        return bookmarks
    elif b == 'Preferences' or b == 'Secure Preferences':
        return preferences
    elif b == 'Local State':
        return local_state
    elif 'Shortcuts' in b:
        return shortcuts
    elif '\\CRX_INSTALL' in path:
        return crx_install
    elif '\\Extensions\\' in path or \
         '\\Extension Rules' in path or \
         '\\Extension State\\' in path or \
         '\\Local Extension Settings\\' in path or \
         '\\Managed Extension Settings\\' in path:
        return extensions
    elif '\\GCM Store\\' in path:
        return gcm_store
    elif '\\Cache\\' in path:
        return cache
    elif '\\File System\\' in path:
        return file_system
    elif '\\Media Cache\\' in path or '\\MEDIA CACHE\\' in path:
        return media_cache
    elif 'ChromeDWriteFontCache' in path:
        return font_cache
    elif '\\GPUCache\\' in path:
        return gpu_cache
    elif '\\Sync Data\\' in path:
        return sync_data
    elif '\\Sync Extension Settings\\' in path:
        return sync_extension_settings
    elif '\\Sync App Settings\\' in path:
        return sync_app_settings
    elif '\\Local App Settings\\' in path:
        return local_app_settings
    elif '\\Session Storage\\' in path:
        return session_storage
    elif '\\Local Storage\\' in path:
        return local_storage
    elif '\\Visited Links' in path:
        return visited_links
    elif '\\Web Data' in path:
        return web_data
    elif '\\History' in path:
        return history
    elif '\\QuotaManager' in path:
        return quota_manager
    elif '\\Network Action Predictor' in path:
        return network_action_predictor
    elif '\\Current Session' in path:
        return current_sessions
    elif '\\Current Tabs' in path:
        return current_tabs
    elif is_cookies_file(path):
        return cookies
    elif ext == '.tmp' or ext == '.temp' or "\\Temp\\" in path:
        return temp
    else:
        return other

def GetDirSize(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def IgnoreFile(file_path):
    (d, f) = os.path.split(file_path)
    return f in ['chrome.dll', 'chrome_debug.log', '$LogFile', '$Mft']

def GetNumLevelDBOpens(log_dir):
    files = {}
    reg = re.compile("^(.*): (\\d+)$")
    for log_file in glob.glob("%s\\leveldb_*_open.log" % log_dir):
        with open(log_file, "r") as f:
            for line in f.readlines():
                m = reg.match(line)
                if m:
                    db = m.group(1)
                    num = int(m.group(2))
                    if db in files:
                        files[db] = files[db] + 1
                    else:
                        files[db] = 1
    return files

def PrintStats():
    dbs = GetNumLevelDBOpens('D:\\src')
    for f in sorted(dbs.keys()):
        print "%s: %d" % (f, dbs[f])
    print "Total: %d db's" % len(dbs)
    dir_size = GetDirSize(r'D:\src\out\Release\${HOME}\.chrome_dev')
    print "Chrome dir size: %ld, %.1f MB" % (dir_size, dir_size/1024.0/1024.0)

duration = None
rename_map = {}
with codecs.open(procmon_log_name, 'r', encoding='utf-8-sig') as csvfile:
    first_time = None
    last_time = None
    time_col_idx = None
    op_col_idx = None
    path_col_idx = None
    detail_col_idx = None
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    row_idx = 0
    rename_re = re.compile('.*FileName: (.+)$')
    for row in reader:
        row_idx += 1
        if row_idx == 1:
            time_col_idx = row.index("Time of Day")
            op_col_idx = row.index("Operation")
            path_col_idx = row.index("Path")
            detail_col_idx = row.index("Detail")
            continue
        last_time = row[time_col_idx]
        if first_time == None:
            first_time = last_time
        if row[op_col_idx] == 'SetRenameInformationFile':
            old_name = row[path_col_idx]
            data = row[detail_col_idx]
            m = rename_re.match(data)
            if m:
                new_name = m.group(1)
                rename_map[old_name] = new_name
            else:
                # A file was renamed, but we couldn't find out what to!
                assert False

    start = datetime.strptime(re.sub(r'\.\d+', '', first_time), "%I:%M:%S %p")
    end = datetime.strptime(re.sub(r'\.\d+', '', last_time), "%I:%M:%S %p")
    duration = end - start

counted_files = {}

# Change from "null_category" to one of the others to write out counts
# for each file in that category
counted_category = null_category
counted_category = extensions

with open(procmon_file_filter_name, 'r') as csvfile:
    idb_origin_re = re.compile(r'.*\\([^\\]+)\\IndexedDB\\([^\\]+).*$')
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    num_ops = 0
    path_col_idx = None
    read_bytes_col_idx = None
    write_bytes_col_idx = None
    for row in reader:
        num_ops += 1
        # First two rows are summary data
        if num_ops == 1:
            path_col_idx = row.index("Path")
            read_bytes_col_idx = row.index("Read Bytes")
            write_bytes_col_idx = row.index("Write Bytes")
            continue
        if num_ops == 2:
            continue
        path = row[path_col_idx]
        if IgnoreFile(path):
            continue
        read_bytes = int(row[read_bytes_col_idx].replace(',', ''))
        write_bytes = int(row[write_bytes_col_idx].replace(',', ''))
        if write_bytes == 0 and write_bytes == 0:
            continue
        total.Increment(read_bytes, write_bytes)

        non_renamed_temp_files = set()
        category = GetCategory(path)
        if category == temp:
            if path in rename_map:
                path = rename_map[path]
                category = GetCategory(path)
            else:
                non_renamed_temp_files.add(path)
        if category == counted_category:
            if sort_by == 'written':
                amount = write_bytes
            else:
                amount = read_bytes
            if path in counted_files:
                counted_files[path] += amount
            else:
                counted_files[path] = amount
        category.Increment(read_bytes, write_bytes)
        if category == idb:
            m = idb_origin_re.match(path)
            if not m:
                print path
            assert m
            name = '%s-%s' % (m.group(1), m.group(2))
            AddIDBOriginIO(name, read_bytes, write_bytes)

if len(counted_files):
    print
    print "Counted files (%s):" % sort_title
    print "============================="
    total_counted = 0
    sorted_files = sorted(counted_files.items(), key=itemgetter(1), reverse=True)
    for path, amount in sorted_files:
        total_counted += amount
        print "%ld B: %s" % (amount, path)
    print "Total counted: %ld" % total_counted

if output_csv:
    for category in sorted(categories, key=attrgetter(sort_by), reverse=True):
        category.PrintCsv()
else:
    print
    print "Categories (%s):" % sort_title
    print "=========================="
    col_width = max(len(category.name) for category in categories)
    for category in sorted(categories, key=attrgetter(sort_by), reverse=True):
        category.Print(col_width)
    total.Print(col_width)
    print
    seconds_per_day = 86400
    write_bytes_per_sec = float(total.written) / duration.seconds
    write_gb_per_day = (write_bytes_per_sec * seconds_per_day) / 1024.0/1024.0/1024.0
    read_bytes_per_sec = float(total.read) / duration.seconds
    read_gb_per_day = (read_bytes_per_sec * seconds_per_day) / 1024.0/1024.0/1024.0
    print "Over %s, Chrome is:" % duration
    print "  Reading %.1f Bps (%.1f GB/day)" % \
            (read_bytes_per_sec, read_gb_per_day)
    print "  Writing %.1f Bps (%.1f GB/day)" % \
            (write_bytes_per_sec, write_gb_per_day)

    print
    print "IndexedDB:"
    print "=========="
    for category in sorted(idb_origin_categories.values(), key=attrgetter(sort_by), reverse=True):
        category.Print(60)
