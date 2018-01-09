"""
Local storage reader for Electron/Chromium/Chrome formats.
With utilities used to find processes and local storage paths
"""

import sqlite3
import os
from typing import Tuple, Dict, Callable
import psutil

class RequirementException(Exception):
    """Some requirement was not met"""
    # All Hail POSIX
    pass

if not os.name == 'posix':
    raise RequirementException('This module requires a POSIX compatible operating system')

def search_processes(process_filter: Callable[[str, str], bool], any_user=False) -> psutil.Process:
    """Searches the process list with the filter applied and optionally of all users"""
    for proc in psutil.process_iter():
        if any_user or proc.username() == os.environ['USER']:
            try:
                exe = os.path.realpath(proc.exe())
                if process_filter(exe, os.path.basename(exe)):
                    yield proc
            except psutil.AccessDenied:
                # ignore
                pass

def list_open_files(proc: psutil.Process) -> str:
    """Reads files opened by the process"""
    fdir = f'/proc/{proc.pid}/fd'
    for _f in os.listdir(fdir):
        yield os.readlink(os.path.join(fdir, _f))

def find_local_storage(proc: psutil.Process) -> str:
    """Finds a singular local storage location for process"""
    for _f in list_open_files(proc):
        if 'Local Storage' in _f:
            return os.path.dirname(_f)
    return None

class LocalStorage:
    """Represents one LocalStorage file"""

    def __init__(self, site: str, storage: str, proto='https'):
        """Wrapper class for local storage"""
        self.storage = storage
        self.site = site
        self.proto = proto
        self.connection = None

    def connect(self) -> sqlite3.Connection:
        """Gets a SQLite connection for this LocalStorage file"""
        if self.connection:
            return self.connection
        for _f in os.listdir(self.storage):
            if _f.startswith(self.proto + '_' + self.site + '_') and _f.endswith('.localstorage'):
                self.connection = sqlite3.connect(os.path.join(self.storage, _f))
                return self.connection
        return None

    def read(self) -> Dict:
        """Fetches all values in the specified local storage for the specified site and protocol"""
        values = {}
        con = self.connect()
        for row in con.execute('SELECT * FROM ItemTable'):
            values[row[0]] = row[1]
        return values

    def read_iter(self) -> Tuple[str, str]:
        """Iterator for key-value tuples"""
        con = self.connect()
        for row in con.execute('SELECT * FROM ItemTable'):
            yield row

    def read_key(self, key: str) -> bytes:
        """Returns only the value for one key"""
        cur = self.connect().cursor()
        cur.execute('SELECT value FROM ItemTable WHERE key=?', (key,))
        try:
            return cur.fetchone()[0]
        except TypeError:
            return None

    def close(self):
        """Closes the currently open connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """Checks is there an established connection to the local storage file"""
        return bool(self.connection)

    def __getitem__(self, key):
        item =  self.read_key(key)
        if item:
            return item
        else:
            raise IndexError
