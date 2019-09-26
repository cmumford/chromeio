#!/usr/bin/env python

import codecs
import csv
import datetime
import glob
import locale
from operator import itemgetter, methodcaller
import os
import re
import sys
import time
from time import mktime
from datetime import datetime

# This script counts disk I/O on Windows. Use the Process Monitor tool to
# capture all I/O for a given process (chrome.exe). Then save out the main
# view to a CSV file. Use this program to categorize the results.
#
# python chromeio.py <log_file.csv>
#

output_csv = False
# Process Monitor -> File -> Save... (to CSV) to this file.
if len(sys.argv) < 2:
    print >> sys.stderr, "Must supply the Process Monitor log file"
    sys.exit(1)

procmon_log_name = sys.argv[1]

sort_by = 'Written'
if sort_by == 'Written':
    sort_title = 'Written'
else:
    sort_title = 'Read'

class Amount(object):
    @staticmethod
    def ToString(bytes):
        if bytes >= 1024*1024*1024:
            return "%.1fGB" % (float(bytes) / 1024 / 1024 / 1024)
        if bytes >= 1024*1024:
            return "%.1fMB" % (float(bytes) / 1024 / 1024)
        if bytes >= 1024:
            return "%.1fKB" % (float(bytes) / 1024)
        return "%dB" % bytes

    @staticmethod
    def PerDay(bytes, duration):
        seconds_per_day = 86400
        bytes_per_sec = bytes / duration.seconds
        bytes_per_day = bytes_per_sec * seconds_per_day
        return "%s/day" % Amount.ToString(bytes_per_day)

class FileTotals(object):
    def __init__(self, path, read, written):
        self.path = path
        self.read = read
        self.written = written

    def Increment(self, read, written):
        self.read += read
        self.written += written

    def Read(self):
        return self.read

    def Written(self):
        return self.written

class Category(object):
    def __init__(self, name, total=None):
        self.name = name
        self.files = {}
        self.total = total

    def AppendFileTotals(self, file_totals):
        if file_totals.path in self.files:
            # Append to existing entry
            existing_entry = self.files[file_totals.path]
            existing_entry.read += file_totals.read
            existing_entry.written += file_totals.written
        else:
            self.files[file_totals.path] = file_totals

    def Increment(self, path, read, written):
        if path in self.files:
            self.files[path].Increment(read, written)
        else:
            self.files[path] = FileTotals(path, read, written)

    def ExtractPath(self, path):
        return self.files.pop(path, None)

    @staticmethod
    def GetBytesString(amount):
        return "%ld=%s" % (amount, Amount.ToString(amount))

    @staticmethod
    def GetAmountString(amount, total, duration):
        percentage = 0
        # Avoid divide-by-zero errors.
        if total > 0:
          percentage = 100.0 * amount / total
        return "%s=%.1f%%=%s" % (Category.GetBytesString(amount),
                                percentage,
                                Amount.PerDay(amount, duration))

    @staticmethod
    def GetBothAmounts(read, written, total_read, total_written, duration):
        return "R[%s], W[%s]" % (Category.GetAmountString(read, total_read, duration),
                               Category.GetAmountString(written, total_written, duration))

    def Print(self, name_col_width, duration):
        if self.total:
            print "%s: %s" % (self.name.ljust(name_col_width),
                          Category.GetBothAmounts(self.Read(), self.Written(),
                                                  total.Read(), total.Written(),
                                                  duration))
        else:
            print "%s: %s" % (self.name.ljust(name_col_width),
                              Category.GetBytesString(self.Written()))

    def Written(self):
        total_written = 0
        for f in self.files:
            total_written += self.files[f].Written()
        return total_written

    def Read(self):
        total_read = 0
        for f in self.files:
            total_read += self.files[f].Read()
        return total_read

    def Empty(self):
        for f in self.files:
            info = self.files[f]
            if info.Read() or info.Written():
                return False
        return True

    def PrintCsv(self):
        print "%s,%ld" % (self.name, self.Written())

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
web_data = Category("Web Data", total)
history = Category("History", total)
visited_links = Category("Visited Links", total)
quota_manager = Category("Quota Manager", total)
network_action_predictor = Category("Network Action Predictor", total)
current_session = Category("Current Session", total)
current_tabs = Category("Current Tabs", total)
ev = Category("EV", total)
service_worker = Category("Service Worker", total)
custom_dictionary = Category("Custom Dictionary", total)
user_policy = Category("User Policy", total)
top_sites = Category("Top Sites", total)
transport_security = Category("Transport Security", total)

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
    web_data,
    history,
    visited_links,
    quota_manager,
    network_action_predictor,
    current_session,
    current_tabs,
    ev,
    service_worker,
    custom_dictionary,
    user_policy,
    top_sites,
    transport_security,
    other
]

idb_origin_categories = {}

def AddIDBOriginIO(origin, path, bytes_read, bytes_written):
    if origin in idb_origin_categories:
        category = idb_origin_categories[origin]
    else:
        category = Category(origin, total)
        idb_origin_categories[origin] = category
    category.Increment(path, bytes_read, bytes_written)

def GetCategory(path):
    base, ext = os.path.splitext(path)
    b = os.path.basename(path)
    if 'etilqs' in path:
        return sqlite_temp
    if b.startswith('pnacl') or b == 'nacl_validation_cache.bin' or 'PnaclTranslationCache' in path:
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
    elif b.startswith('Preferences') or b == 'Secure Preferences':
        return preferences
    elif '\\Local State' in path:
        return local_state
    elif 'Shortcuts' in b:
        return shortcuts
    elif '\\CRX_INSTALL' in path:
        return crx_install
    elif '\\Extensions\\' in path or \
         '\\Extension Rules' in path or \
         '\\Extension State\\' in path or \
         '\\Extension Activity' in path or \
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
    elif '\\Sync Data\\' in path or '\\Sync Data Backup\\' in path:
        return sync_data
    elif '\\Sync Extension Settings\\' in path:
        return sync_extension_settings
    elif '\\Sync App Settings\\' in path:
        return sync_app_settings
    elif '\\Local App Settings\\' in path:
        return local_app_settings
    elif '\\Session Storage\\' in path:
        return session_storage
    elif '\\Top Sites' in path:
        return top_sites
    elif '\\Local Storage\\' in path:
        return local_storage
    elif '\\Web Data' in path:
        return web_data
    elif '\\Visited Links' in path:
        return visited_links
    elif '\\History' in path:
        return history
    elif '\\QuotaManager' in path:
        return quota_manager
    elif '\\Network Action Predictor' in path:
        return network_action_predictor
    elif '\\Current Session' in path:
        return current_session
    elif '\\Current Tabs' in path:
        return current_tabs
    elif '\\Service Worker\\' in path:
        return service_worker
    elif '\\User Policy' in path:
        return user_policy
    elif 'Custom Dictionary' in path:
        return custom_dictionary
    elif b.startswith('TransportSecurity'):
        return transport_security
    elif 'ev_hashes_whitelist.bin' in path:
        return ev
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
    if 'Windows\\Prefetch' in file_path:
        return True
    return f in ['chrome.dll', 'chrome_child.dll', 'chrome_debug.log', '$LogFile', '$Mft']

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

def ParseDetail(detail):
    items = {}
    for item in detail.split(', '):
        if item == 'Paging I/O':
            items['Paging I/O'] = True
        elif item == 'Synchronous Paging I/O':
            items['Synchronous Paging I/O'] = True
        else:
            pair = item.split(': ')
            if len(pair) == 2:
                items[pair[0]] = pair[1]
            else:
                print >> sys.stderr, 'Cannot parse "%s"' % item
    return items

# Find a path summary and (if found) extract it from it's current category
# and return it.
def ExtractFileTotalsFromCategory(path):
    for category in categories:
        file_totals = category.ExtractPath(path)
        if file_totals:
            return file_totals
    return None

def IsTempFile(fname):
    if r'AppData\Local\Temp' in fname:
        return True
    b = os.path.basename(fname)
    if b.startswith('etilqs_'):
        return True
    (f, ext) = os.path.splitext(b)
    return ext == '.TMP' or ext == '.tmp'

# Change from "null_category" to one of the others to write out counts
# for each file in that category
counted_category = null_category
counted_category = preferences

duration = None
idb_origin_re = re.compile(r'.*\\([^\\]+)\\IndexedDB\\([^\\]+).*$')
# See comment below.
# with codecs.open(procmon_log_name, 'r', encoding='utf-8-sig') as csvfile:
with open(procmon_log_name, 'r') as csvfile:
    first_time = None
    last_time = None
    time_col_idx = None
    op_col_idx = None
    path_col_idx = None
    detail_col_idx = None
    result_col_idx = None
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    row_idx = 0
    for row in reader:
        row_idx += 1
        if row_idx == 1:
            # A hack to embed the encoding here, but reading properly (with
            # codecs) is about 10x slower. Reordering the columns in procmon
            # will break this.
            time_col_idx = row.index('\xef\xbb\xbf"Time of Day"')
            op_col_idx = row.index("Operation")
            path_col_idx = row.index("Path")
            detail_col_idx = row.index("Detail")
            result_col_idx = row.index("Result")
            continue
        last_time = row[time_col_idx]
        if first_time == None:
            first_time = last_time
        path = row[path_col_idx]
        if 'startup_complete.txt' in path:
            break
        if IgnoreFile(path):
            continue
        if row[result_col_idx] == 'SUCCESS':
            write_bytes = 0
            read_bytes = 0
            op = row[op_col_idx]
            if op == 'IRP_MJ_SET_INFORMATION':
                detail = ParseDetail(row[detail_col_idx])
                if 'Type' in detail and detail['Type'] == 'SetRenameInformationFile':
                    old_name = path
                    if True:
                        file_totals = ExtractFileTotalsFromCategory(old_name)
                        if file_totals:
                            # Move info totals for old file to new file
                            new_name = detail['FileName']
                            category = GetCategory(new_name)
                            file_totals.path = new_name
                            category.AppendFileTotals(file_totals)
            elif op == 'IRP_MJ_WRITE' or op == 'FASTIO_WRITE' or op == 'WriteFile':
                detail = ParseDetail(row[detail_col_idx])
                write_bytes = int(detail['Length'].replace(',', ''))
            elif op == 'IRP_MJ_READ' or op == 'FASTIO_READ' or op == 'ReadFile':
                detail = ParseDetail(row[detail_col_idx])
                read_bytes = int(detail['Length'].replace(',', ''))
            if read_bytes or write_bytes:
                total.Increment(path, read_bytes, write_bytes)
                category = GetCategory(path)
                category.Increment(path, read_bytes, write_bytes)
                if category == idb:
                    m = idb_origin_re.match(path)
                    if not m:
                        print path
                    assert m
                    name = '%s-%s' % (m.group(1), m.group(2))
                    AddIDBOriginIO(name, path, read_bytes, write_bytes)
    start = datetime.strptime(re.sub(r'\.\d+', '', first_time), "%I:%M:%S %p")
    end = datetime.strptime(re.sub(r'\.\d+', '', last_time), "%I:%M:%S %p")
    duration = end - start

print
print "Counted files (%s):" % sort_title
print "============================="
total_counted = 0
counted_files = []
for info in counted_category.files:
    counted_files.append(counted_category.files[info])
sorted_files = sorted(counted_files, key=methodcaller(sort_by), reverse=True)
for info in sorted_files:
    if sort_by == 'Written':
        amount = info.Written()
    else:
        amount = info.Read()
    total_counted += amount
    if amount:
        print "%ld B: %s" % (amount, info.path)
print "Total counted: %ld" % total_counted

if output_csv:
    for category in sorted(categories, key=methodcaller(sort_by), reverse=True):
        category.PrintCsv()
else:
    print
    print "Categories (%s):" % sort_title
    print "=========================="
    col_width = max(len(category.name) for category in categories)
    for category in sorted(categories, key=methodcaller(sort_by), reverse=True):
        if sort_by == 'Written':
            amount = category.Written()
        else:
            amount = category.Read()
        if not category.Empty():
            category.Print(col_width, duration)
    total.Print(col_width, duration)
    print
    seconds_per_day = 86400
    write_bytes_per_sec = float(total.Written()) / duration.seconds
    write_gb_per_day = (write_bytes_per_sec * seconds_per_day) / 1024.0/1024.0/1024.0
    read_bytes_per_sec = float(total.Read()) / duration.seconds
    read_gb_per_day = (read_bytes_per_sec * seconds_per_day) / 1024.0/1024.0/1024.0
    print "Over %s, Chrome is:" % duration
    print "  Reading %.1f Bps (%.1f GB/day)" % \
            (read_bytes_per_sec, read_gb_per_day)
    print "  Writing %.1f Bps (%.1f GB/day)" % \
            (write_bytes_per_sec, write_gb_per_day)

    print
    print "IndexedDB:"
    print "=========="
    for category in sorted(idb_origin_categories.values(), key=methodcaller(sort_by), reverse=True):
        category.Print(60, duration)
