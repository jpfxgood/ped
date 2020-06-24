# Copyright 2013-2014 James P Goodwin bkp@jlgoodwin.com
""" module to implement shared functions for local file systems for the bkp/rstr tool """

import shutil
import os
import time
from io import StringIO
import threading
import sys

file_safe_path_lock = threading.Lock()

def strip_protocol( path ):
    """ strip off file:// from start of path """
    if path.startswith("file://"):
        return path[7:]
    else:
        raise Exception("strip_protocol: Missing protocol prefix.",path)
    
def safe_path( path ):
    """ make sure that the target path exists """
    try:
        file_safe_path_lock.acquire()
        d = os.path.dirname(path)
        if not os.path.exists(d):
            os.makedirs(d)           
    finally:
        file_safe_path_lock.release()
    return path
    
def file_utime( remote_path, times ):
    """ set the file time on the target to the times specified """
    os.utime(strip_protocol(remote_path), times )
    
def file_get( remote_path, local_path ):
    """ copy from remote_path to local_path """
    shutil.copy2(strip_protocol(remote_path),safe_path(local_path))

def file_put( local_path, remote_path ):
    """ copy from local_path to remote_path """
    shutil.copy2(local_path,safe_path(strip_protocol(remote_path)))
    
def file_ls( remote_path, recurse=False ):
    """ perform ls on the path, recurse to subdirectories if recurse is true """
    output = ""
    stream = StringIO()
    remote_path = strip_protocol(remote_path)
    
    if os.path.isdir(remote_path):
        for root,dirs,files in os.walk(remote_path):
            if not recurse:
                for d in dirs:
                    print("                           DIR file://%s/"%os.path.join(os.path.abspath(root),d), file=stream)
            for f in files:
                fp = os.path.join(os.path.abspath(root),f)
                st = os.stat(fp)
                mtime = time.localtime(st.st_mtime)
                print("%04d-%02d-%02d %02d:%02d %9d   file://%s"%(mtime.tm_year,mtime.tm_mon,mtime.tm_mday,mtime.tm_hour,mtime.tm_min,st.st_size,fp), file=stream)
            if not recurse:
                break
    else:
        fp = os.path.abspath(remote_path)
        st = os.stat(fp)
        mtime = time.localtime(st.st_mtime)
        print("%04d-%02d-%02d %02d:%02d %9d   file://%s"%(mtime.tm_year,mtime.tm_mon,mtime.tm_mday,mtime.tm_hour,mtime.tm_min,st.st_size,fp), file=stream)
        
            
    output = stream.getvalue()
    stream.close()
    return output
            
    
def file_del( remote_path, recurse=False ):
    """ perform del on path, recurse and delete subdirectory contents if recurse is true """
    remote_path = strip_protocol(remote_path) 
    if os.path.isdir(remote_path):
        for root,dirs,files in os.walk(remote_path, not recurse):
            for f in files:
                os.remove(os.path.join(os.path.abspath(root),f))
            if recurse:
                for d in dirs:
                    os.rmdir(os.path.join(os.path.abspath(root),d))
            else:
                break
    else:
        os.remove(os.path.abspath(remote_path))
    return ""
    

def file_stat( remote_path ):
    """ perform stat on the remote path and return tuple of ( mtime, size ) or (-1,-1) if doesn't exist """
    remote_path = strip_protocol(remote_path)
    try:
        st = os.lstat(remote_path)
        return (st.st_mtime,st.st_size)
    except:
        pass
    return (-1,-1)


