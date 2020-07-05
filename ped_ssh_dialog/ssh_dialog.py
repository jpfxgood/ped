# Copyright 2009 James P Goodwin ped tiny python editor
""" module that implements file open/new dialog for the ped editor """
import curses
from ped_ssh_dialog import ssh_mod
from ped_ssh_dialog.ssh_mod import ssh_log_name
import curses.ascii
import sys
import re
import os
from ped_dialog import dialog
from ped_core import keytab
from io import StringIO
from ped_dialog.confirm_dialog import confirm
from ped_dialog.message_dialog import message
import traceback

def get_dir_ssh( path, ssh_username, ssh_password, showhidden=False ):
    """ get a directory listing of a ssh remote path, for a particular username and password """
    def get_config():
        return { "ssh_username":ssh_username, "ssh_password":ssh_password }

    dir_list = ssh_mod.ssh_ls(path,False,get_config,False)
    dirnames = []
    filenames = []
    for item in StringIO(dir_list):
        item = item.strip()
        if item.startswith("DIR"):
            parts = item[4:].split("/")
            dirnames.append(parts[-2])
            continue
        (date,time,size,path) = re.split("\s+",item,3)
        parts = path.split("/")
        filenames.append(parts[-1])
    if not showhidden:
        dirnames = [d for d in dirnames if d[0] != "."]
        filenames = [f for f in filenames if f[0] != "." and f[-1] != "~" and not f.endswith(".bak")]
    dirnames.sort()
    filenames.sort()
    dirnames = ["<DIR> .."] + ["<DIR> "+d for d in dirnames]
    return((path,dirnames,filenames))


def get_dir(path,showhidden=False):
    """ get a directory listing of path, directories are prefixed with <DIR>
        if showhidden == False hidden files are not include, otherwise they are
        returns the directory path, the list of directories and list of files as a tuple"""
    (dirpath, dirnames, filenames) = next(os.walk(path))
    if not showhidden:
        dirnames = [d for d in dirnames if d[0] != "."]
        filenames = [f for f in filenames if f[0] != "." and f[-1] != "~" and not f.endswith(".bak")]
    dirnames.sort()
    filenames.sort()
    dirnames = ["<DIR> .."] + ["<DIR> "+d for d in dirnames]
    return (dirpath, dirnames, filenames)

class SSHFileListBox(dialog.ListBox):
    """ list box subclass for file lists, handles searching past the <DIR> prefix for incremental searches"""
    def find(self,searchfor):
        """ subclass the find method to find the string either with the dir prefix or without it """
        if not dialog.ListBox.find(self,"<DIR> "+searchfor):
            return dialog.ListBox.find(self,searchfor)
        else:
            return True

class SSHFileDialog(dialog.Dialog):
    """ dialog subclass that implements an ssh browsing experience, allowing you to put or get files
    to and from an ssh server location """
    def __init__(self,scr,title = "SSH File Dialog", remote_path="", ssh_username="", ssh_password="", local_path="."):
        """ takes a curses window scr, title for the border, and a remote starting path and credentials and a local starting path """
        max_y, max_x = scr.getmaxyx()
        dw = max_x - 4
        dh = max_y - 4
        self.prior_ssh = None
        self.prior_local = None
        y = 2
        self.ssh_username = dialog.Prompt("ssh_username",1,2,y,"SSH Username: ",dw-18,ssh_username)
        y += 1
        self.ssh_password = dialog.PasswordPrompt("ssh_password",2,2,y,"SSH Password: ",dw-18,ssh_password)
        y += 1
        self.ssh_current_dir = dialog.Prompt("ssh_dir",3,2,y,"SSH Path: ",dw-18,remote_path)
        y += 1
        self.ssh_file_list = SSHFileListBox("ssh_files",4,2,y,dh//3,dw-4,"SSH Directory Listing",0,[])
        y += dh//3
        self.ssh_file_name = dialog.Prompt("ssh_file",5,2,y,"SSH File: ",dw-18)
        y += 1
        self.current_dir = dialog.Prompt("local_dir",6,2,y,"Local Path: ",dw-18,local_path)
        y += 1
        self.file_list = SSHFileListBox("local_files",7,2,y,dh//3,dw-4,"Local Directory Listing",0,[])
        y += dh//3
        self.file_name = dialog.Prompt("local_file",8,2,y,"Local File: ",dw-18)
        y += 1
        x = 2
        iw = dw//4
        self.put_button = dialog.Button("Put",9,x,y,"PUT",dialog.Component.CMP_KEY_NOP)
        x += iw
        self.get_button = dialog.Button("Get",10,x,y,"GET",dialog.Component.CMP_KEY_NOP)
        x += iw
        self.open_button = dialog.Button("Open",10,x,y,"OPEN",dialog.Component.CMP_KEY_OK)
        x += iw
        self.cancel_button = dialog.Button("Cancel",11,x,y,"CANCEL",dialog.Component.CMP_KEY_CANCEL)
        dialog.Dialog.__init__(self,scr,"FileDialog",dh,dw, [ dialog.Frame(title),
                                                                self.ssh_username,
                                                                self.ssh_password,
                                                                self.ssh_current_dir,
                                                                self.ssh_file_list,
                                                                self.ssh_file_name,
                                                                self.file_list,
                                                                self.current_dir,
                                                                self.file_name,
                                                                self.put_button,
                                                                self.get_button,
                                                                self.open_button,
                                                                self.cancel_button
                                                            ])
        self.refresh()

    def refresh(self,force=False):
        """ populate all of the fields if something changed """
        values = self.getvalue()
        ssh_path = ""
        ssh_dirnames = []
        ssh_filenames = []
        set_values={}
        if values["ssh_username"] and values["ssh_password"] and values["ssh_dir"]:
            new_ssh = values["ssh_username"] + values["ssh_password"] + values["ssh_dir"]
            if new_ssh != self.prior_ssh or force:
                self.prior_ssh = new_ssh
                try:
                    (ssh_path,ssh_dirnames,ssh_filenames) = get_dir_ssh( values["ssh_dir"], values["ssh_username"], values["ssh_password"], False)
                    self.prior_ssh = new_ssh
                    set_values["ssh_files"] = (0, ssh_dirnames+ssh_filenames)
                except:
                    print(traceback.format_exc(), file=open(ssh_log_name,"a"))
                    confirm(self.win, "SSH Error! Try Again ?")
        local_path = ""
        local_dirnames = []
        local_filenames = []
        if values["local_dir"]:
            if self.prior_local != values["local_dir"] or force:
                try:
                    (local_path, local_dirnames,local_filenames) = get_dir(values["local_dir"],False)
                    os.chdir(local_path)
                    self.prior_local = values["local_dir"]
                    set_values["local_files"] = (0, local_dirnames+local_filenames)
                except:
                    print(traceback.format_exc(), file=open(ssh_log_name,"a"))
                    confirm(self.win, "File Error! Try Again ?")
        self.setvalue(set_values)


    def handle(self,ch):
        """ key handler for selection from the file and directory list,
            browsing another directory selecting a file or entering one """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = dialog.Dialog.handle(self,ch)
        if ch in [keytab.KEYTAB_TAB, keytab.KEYTAB_BACKTAB]:
            self.refresh()
        elif ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            if focus_field == self.file_list:
                (selection, items) = focus_field.getvalue()
                choice = items[selection]
                if choice.startswith('<DIR>'):
                    self.current_dir.setvalue(os.path.abspath(os.path.join(self.current_dir.getvalue(),choice[6:])))
                    self.current = focus_index
                    ret_ch = dialog.Component.CMP_KEY_NOP
                else:
                    self.file_name.setvalue(choice)
                    self.ssh_file_name.setvalue(choice)
                self.refresh()
            elif focus_field == self.current_dir and ch == keytab.KEYTAB_CR:
                self.refresh()
            elif focus_field == self.ssh_file_list:
                (selection, items) = focus_field.getvalue()
                choice = items[selection]
                if choice.startswith('<DIR>'):
                    dir = choice[6:]
                    curpath = self.ssh_current_dir.getvalue()
                    if dir == "..":
                        curpath = "/".join(curpath.split("/")[:-1])
                    else:
                        curpath = curpath + "/" + dir
                    self.ssh_current_dir.setvalue(curpath)
                    self.current = focus_index
                    ret_ch = dialog.Component.CMP_KEY_NOP
                else:
                    self.file_name.setvalue(choice)
                    self.ssh_file_name.setvalue(choice)
                self.refresh()
            elif focus_field == self.ssh_current_dir and ch == keytab.KEYTAB_CR:
                self.refresh()
            elif focus_field == self.put_button:
                try:
                    if not self.file_name.getvalue() or not self.ssh_file_name.getvalue():
                        confirm(self.win, "Source or destination filename not set, retry ?")
                    else:
                        message(self.win, "Putting File", "Transfering %s"%(self.file_name.getvalue()),False)
                        ssh_mod.ssh_put(os.path.join(self.current_dir.getvalue(),self.file_name.getvalue()),
                        self.ssh_current_dir.getvalue()+"/"+self.ssh_file_name.getvalue(),
                        lambda : { 'ssh_username': self.ssh_username.getvalue(), "ssh_password":self.ssh_password.getvalue() }, False)
                        self.refresh(True)
                except:
                    print(traceback.format_exc(), file=open(ssh_log_name,"a"))
                    confirm(self.win, "SSH Error! Try Again ?")
            elif focus_field == self.get_button:
                try:
                    if not self.file_name.getvalue() or not self.ssh_file_name.getvalue():
                        confirm(self.win, "Source or destination filename not set, retry ?")
                    else:
                        message(self.win, "Getting File", "Transfering %s"%(self.file_name.getvalue()),False)
                        ssh_mod.ssh_get(self.ssh_current_dir.getvalue()+"/"+self.ssh_file_name.getvalue(),
                        os.path.join(self.current_dir.getvalue(),self.file_name.getvalue()),
                        lambda : { 'ssh_username': self.ssh_username.getvalue(), "ssh_password":self.ssh_password.getvalue() })
                        self.refresh(True)
                except:
                    print(traceback.format_exc(), file=open(ssh_log_name,"a"))
                    confirm(self.win, "SSH Error! Try Again ?")
            elif focus_field == self.open_button:
                try:
                    if not self.file_name.getvalue() or not self.ssh_file_name.getvalue():
                        confirm(self.win, "Source or destination filename not set, retry ?")
                    else:
                        message(self.win, "Opening File", "Transfering %s"%(self.file_name.getvalue()),False)
                        ssh_mod.ssh_get(self.ssh_current_dir.getvalue()+"/"+self.ssh_file_name.getvalue(),
                        os.path.join(self.current_dir.getvalue(),self.file_name.getvalue()),
                        lambda : { 'ssh_username': self.ssh_username.getvalue(), "ssh_password":self.ssh_password.getvalue() })
                        self.refresh(True)
                except:
                    print(traceback.format_exc(), file=open(ssh_log_name,"a"))
                    confirm(self.win, "SSH Error! Try Again ?")



        return ret_ch

def sftpDialog( scr, title = "SFTP File Manager", remote_path="", ssh_username="", ssh_password="", local_path="."):
    d = SSHFileDialog( scr, title, remote_path=remote_path, ssh_username=ssh_username, ssh_password=ssh_password, local_path=local_path )
    values = d.main()
    if "local_file" in values:
        return (values["local_file"])
    else:
        return None

def main(stdscr):
    """ test main for the ssh file dialog """
    d = SSHFileDialog(stdscr)
    d.main()

if __name__ == '__main__':
    curses.wrapper(main)
