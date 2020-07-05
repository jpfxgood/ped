# Copyright 2013-2014 James P Goodwin bkp@jlgoodwin.com
""" module to implement shared functions for ssh file systems for the bkp/rstr tool """
import os
import sys
import socket
import traceback
import stat
import time
from ped_ssh_dialog.file_mod import safe_path
from ped_core.editor_common import EditFile
import threading
from io import StringIO
import paramiko
import socket


thread_local = threading.local()

safe_path_lock = threading.Lock()
transport_lock = threading.Lock()
safe_path_cache = {}
host_keys = {}

ssh_log_name = EditFile.get_backup_dir(EditFile.default_backuproot)+"/ssh_mod.log"
paramiko.util.log_to_file(ssh_log_name)

def strip_protocol( path ):
    """ strip off the ssh:// from start of path """
    if path.startswith("ssh://"):
        return path[6:]
    else:
        raise Exception("strip_protocol: Missing protocol prefix.",path)

def split_hostpath( remote_path ):
    """ split off the hostname from an ssh://hostname:port/path name and return tuple (hostname, port, path) """
    remote_path = strip_protocol( remote_path )
    host,path = remote_path.split("/",1)
    path = "/"+path
    parts = host.split(":",1)
    if len(parts) < 2:
        host = parts[0]
        port = 22
    else:
        host = parts[0]
        port = int(parts[1])
    return (host,port,path)


def lookup_hostkey( hostname ):
    """ return the hostkey for a host if we have one in the local host keys table returns (hostkey, hostkeytype) """
    # get host key, if we know one
    hostkeytype = None
    hostkey = None
    global host_keys

    if not host_keys:
        try:
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                # try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
                host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                host_keys = {}

    if hostname in host_keys:
        hostkeytype = list(host_keys[hostname].keys())[0]
        hostkey = host_keys[hostname][hostkeytype]
    return ( hostkey, hostkeytype )



def ssh_transport( hostname, port, username, password, force = False ):
    """ acquire a transport to use SFTP over """
    t = None
    transport_pool = getattr(thread_local, "transport_pool", None)
    if transport_pool == None:
        thread_local.transport_pool = {}

    if (not force) and (( hostname, port, username, password ) in transport_pool):
        t = transport_pool[( hostname, port, username, password )]
    else:
        try:
            t = paramiko.Transport((hostname, port ))
            t.set_keepalive(5)
            t.connect( username=username, password=password, hostkey= lookup_hostkey( hostname )[0])
            t.use_compression(True)
            transport_pool[(hostname,port,username,password)] = t
        except:
            if t:
                if (hostname,port,username,password) in transport_pool:
                    del transport_pool[(hostname,port,username,password)]
                del t
            raise
    return t

def sftp_open( hostname, port, username, password ):
    """ get an open SFTP session object for a given hostname, username, password """
    sftp = None
    try:
        transport_lock.acquire()
        sftp = paramiko.SFTPClient.from_transport(ssh_transport( hostname, port, username, password))
    except:
        sftp = paramiko.SFTPClient.from_transport(ssh_transport( hostname, port, username, password, True))
    finally:
        transport_lock.release()
    return sftp


def sftp_safe_path( sftp, path ):
    """ make sure target sub directories exist """
    try:
        safe_path_lock.acquire()
        parts = path.split('/')[1:-1]
        pkey = "/".join(parts)
        if not pkey in safe_path_cache:
            spath = ''
            for p in parts:
                spath = spath + '/' + p
                try:
                    st = sftp.stat( spath )
                except:
                    sftp.mkdir(spath)
                    st = sftp.stat( spath )

                if not stat.S_ISDIR( st.st_mode ):
                    raise Exception("sftp_safe_path: path element is not a directory!",spath)
            safe_path_cache[pkey] = True
    finally:
        safe_path_lock.release()

    return path

def ssh_utime( remote_path, times, get_config = None ):
    """ set the modified time for a remote file using sftp """
    host, port, path = split_hostpath( remote_path )
    sftp = sftp_open( host, port, get_config()['ssh_username'], get_config()['ssh_password'] )
    try:
        sftp.utime( path, times )
    finally:
        sftp.close()


def ssh_get( remote_path, local_path, get_config = None ):
    """ copy from remote path to local_path using sftp """
    host, port, path = split_hostpath( remote_path )
    sftp = sftp_open( host, port, get_config()['ssh_username'], get_config()['ssh_password'] )
    try:
        sftp.get( path, safe_path(local_path) )
    finally:
        sftp.close()

def ssh_put( local_path, remote_path, get_config = None, verbose = False ):
    """ copy to remote path from local_path using sftp """
    host, port, path = split_hostpath( remote_path )
    sftp = sftp_open( host, port, get_config()['ssh_username'], get_config()['ssh_password'] )

    def put_progress( bytes_transferred, bytes_remaining ):
        if "last_transferred" not in put_progress.__dict__:
            put_progress.last_transferred = 0
        if bytes_transferred - put_progress.last_transferred > 1000000:
            sys.stderr.write("ssh_put: %s %12d %12d\r"%(os.path.basename(local_path),bytes_transferred,bytes_remaining))
            put_progress.last_transferred = bytes_transferred

    try:
        if not verbose:
            sftp.put( local_path, sftp_safe_path(sftp,path) )
        else:
            sftp.put( local_path, sftp_safe_path(sftp,path), put_progress )

    finally:
        sftp.close()


def ssh_ls( remote_path, recurse=False, get_config= None, verbose=False ):
    """ list directories and files perhaps recursively using sftp """
    host, port, path = split_hostpath( remote_path )
    sftp = sftp_open( host, port, get_config()['ssh_username'], get_config()['ssh_password'] )
    try:
        output = ""
        stream = StringIO()

        try:
            st = sftp.lstat(path)
        except IOError:
            return output

        if stat.S_ISDIR( st.st_mode):
            dirs = []
            dirs.append( path )
            while dirs:
                dir = dirs.pop()
                if verbose:
                    print("Processing ", dir, file=sys.stderr)
                try:
                    entries = sftp.listdir(dir)
                except IOError:
                    continue

                for entry in entries:
                    fp = os.path.join(dir,entry)
                    # don't do hidden
                    if entry.startswith("."):
                        continue

                    if verbose:
                        print("Is dir ?", fp, file=sys.stderr)
                    try:
                        st = sftp.lstat(fp)
                    except IOError:
                        continue

                    # don't follow links
                    if stat.S_ISLNK( st.st_mode ):
                        continue

                    if stat.S_ISDIR( st.st_mode ):
                        if recurse:
                            dirs.append( fp )
                        else:
                            print("                           DIR ssh://%s:%s%s/"%(host,port,fp), file=stream)
                    else:
                        mtime = time.localtime(st.st_mtime)
                        print("%04d-%02d-%02d %02d:%02d %9d   ssh://%s:%s%s"%(mtime.tm_year,mtime.tm_mon,mtime.tm_mday,mtime.tm_hour,mtime.tm_min,st.st_size,host,port,fp), file=stream)
        else:
            mtime = time.localtime(st.st_mtime)
            print("%04d-%02d-%02d %02d:%02d %9d   ssh://%s:%s%s"%(mtime.tm_year,mtime.tm_mon,mtime.tm_mday,mtime.tm_hour,mtime.tm_min,st.st_size,host,port,path), file=stream)

        output = stream.getvalue()
        stream.close()
    finally:
        sftp.close()
    return output

def ssh_del( remote_path, recurse=False, get_config= None ):
    """ remove files or directories perhaps recursively using sftp """
    host, port, path = split_hostpath( remote_path )
    sftp = sftp_open( host, port, get_config()['ssh_username'], get_config()['ssh_password'] )
    try:
        st = sftp.stat(path)
        if stat.S_ISDIR( st.st_mode):
            dirs = []
            remove_dirs = []
            dirs.append( path )
            while dirs:
                dir = dirs.pop()
                entries = sftp.listdir(dir)
                for entry in entries:
                    fp = os.path.join(dir,entry)
                    st = sftp.stat(fp)
                    if stat.S_ISDIR(st.st_mode) and recurse:
                        dirs.append( fp )
                        remove_dirs.append(fp)
                    else:
                        sftp.remove(fp)
            while remove_dirs:
                dir = remove_dirs.pop()
                sftp.rmdir(dir)

        else:
            sftp.remove(path)
    finally:
        sftp.close()
    return ""


def ssh_test( remote_path, verbose = False, get_config= None ):
    """ test to make sure that we can access the remote path """

    try:
        host, port, path = split_hostpath( remote_path+"/." )

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host,port))
        data = s.recv(1024)
        if verbose:
            print("ssh_test: ", data, file=sys.stderr)
        s.close()
        return True
    except:
        if verbose:
            print(traceback.format_exc(), file=sys.stderr)
        return False

def ssh_stat( remote_path, get_config= None ):
    """ return tuple (mtime, size) for a file return (-1,-1) if no file """
    host, port, path = split_hostpath( remote_path )
    sftp = sftp_open( host, port, get_config()['ssh_username'], get_config()['ssh_password'] )
    try:
        st = sftp.lstat(path)
        return (st.st_mtime,st.st_size)
    except:
        pass
    finally:
        sftp.close()
    return (-1,-1)
