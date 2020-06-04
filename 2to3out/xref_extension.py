# Copyright 2014 James P Goodwin ped tiny python editor
""" extension to integrate the xref tool  """
import os
import sys
import re
import subprocess
import io
import traceback
from stream_select import StreamSelectComponent
import dialog
from file_browse import FileBrowseComponent
import keytab
import curses
import json
import threading
import time

def sh_escape(s):
    return "'"+s.replace("'","'\\''")+"'"

class XrefRefreshThread( threading.Thread ):
    def __init__( self, xref_dialog ):
        self.xref_dialog = xref_dialog
        self.refresh = xref_dialog.config['refresh'][0]
        self.refresh_time = float(xref_dialog.config['interval'])
        self.last_refresh = 0.0
        threading.Thread.__init__(self)
        self.daemon = True
        

    def run( self ):
        while ( True ):
            t = time.time()
            self.refresh = self.xref_dialog.config['refresh'][0]
            self.refresh_time = float(self.xref_dialog.config['interval'])
            if t-self.last_refresh > self.refresh_time:
                if self.refresh:
                    self.last_refresh = t
                    self.do_refresh()
            time.sleep( self.refresh_time/10.0 )
                
    def do_refresh(self):
        """ run xref in the background to refresh given the configured paramters """
                                               
        config = self.xref_dialog.config          
                   
        self.refresh = config['refresh'][0]
        self.refresh_time = float(config['interval'].strip())
        if self.refresh:
            recurse = config['recurse'][0]
            pattern = sh_escape(config['pattern'])
            directory = sh_escape(config['directory'])
            exclude = sh_escape(config['exclude'])
            numthreads = int(config['numthreads'].strip())
    
            cmd = "xref -v %s -p %s -e %s -d %s -n %s"%('-r' if recurse else '',pattern,exclude,directory,numthreads)
            xref_out = subprocess.Popen(cmd,shell=True,bufsize=1024,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout
            log = open("xref_extension.log","a")
            for l in xref_out:
                print(l, file=log)
            
        return
        

    def refresh_now(self):
        """ config was changed, make sure we refresh on the next cycle """
        self.last_refresh = 0.0

class XrefConfigDialog(dialog.Dialog):
    """ configuration dialog save path, excluded paths """
    def __init__(self, xref_dialog, title = "Xref Config" ):
        """ constructor takes the chat_dialog we're nested over and a title """
        p_win = xref_dialog.win
        min_y,min_x = p_win.getbegyx()
        max_y,max_x = p_win.getmaxyx()
        max_x += min_x
        max_y += min_y
        width = 56
        height = 12
        x = (max_x + min_x)//2 - width//2
        y = (max_y + min_y)//2 - height//2
        dialog.Dialog.__init__(self,p_win,"XrefConfig", height, width, [
            dialog.Frame(title),
            dialog.Toggle("refresh",1,2,2,50-11,xref_dialog.config['refresh'][0],xref_dialog.config['refresh'][1]),
            dialog.Prompt("interval",2,2,3,"Interval: ", 50-10, xref_dialog.config['interval']),
            dialog.Toggle("recurse",3,2,4,50-11,xref_dialog.config['recurse'][0],xref_dialog.config['recurse'][1]),
            dialog.Prompt("pattern",4,2,5,"Pattern: ", 50-11, xref_dialog.config['pattern']),
            dialog.Prompt("directory",5,2,6,"Directory: ", 50-11, xref_dialog.config['directory']),
            dialog.Prompt("exclude",6,2,7,"Exclude: ", 50-9, xref_dialog.config['exclude']),
            dialog.Prompt("numthreads",7,2,9,"Threads: ", 50-11, xref_dialog.config['numthreads']),
            dialog.Button("ok",8,2,10,"OK",dialog.Component.CMP_KEY_OK),
            dialog.Button("cancel",9,7,10,"CANCEL",dialog.Component.CMP_KEY_CANCEL)],y,x)
                   
class XrefDialog(dialog.Dialog):
    """ dialog subclass that implements a xref dialog with a list of found files, list of lines for current file, and a preview window
        and field for query and buttons for config, open, cancel """
    def __init__(self,scr,query):
        """ takes the curses window to pop up over, title to display, will dynamically size to parent window """
        self.fname = ""
        self.line = 0
        self.files = []
        self.lines = {}
        self.config = {}
        self.load_config()
        max_y,max_x = scr.getmaxyx()
        pw = (max_x - 4)
        ph = ((max_y-7) // 3)
        cx = max_x // 2
        y = 1
        self.found_list = StreamSelectComponent("paths",5,cx-(pw//2),y,pw,ph,"Files",open(os.devnull,"r"))
        y += ph        
        self.lines_list = StreamSelectComponent("lines",6,cx-(pw//2),y,pw,ph,"Lines",open(os.devnull,"r"))
        y += ph        
        self.preview = FileBrowseComponent("browse",7,cx-(pw//2),y,pw,ph,"Preview",None)
        y += ph
        self.query = dialog.Prompt("query",1,2,y,"Query:",max_x-13,query)
        y += 1
        dialog.Dialog.__init__(self,scr,"XrefDialog", max_y, max_x, [ dialog.Frame("Xref"),
                                                            self.found_list,
                                                            self.lines_list,
                                                            self.preview,
                                                            self.query,
                                          dialog.Button("open",2,2,y,"OPEN",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("config",3,2+((max_x-4)//3),y,"CONFIG",dialog.Component.CMP_KEY_NOP),
                                          dialog.Button("cancel",4,2+(((max_x-4)//3)*2),y,"CANCEL",dialog.Component.CMP_KEY_CANCEL)])
        if query:
            self.do_query( query )
        self.refresh_thread = XrefRefreshThread( self )
        self.refresh_thread.start()
             
    def resize( self ):
        """ resize the window """
        self.__init__(self.getparent(),self.query.getvalue())
        self.render()
        

    def refresh_lists( self ):
        """ refresh the paths and lines lists """
        pls = io.StringIO()
        lls = io.StringIO()
        
        pidx = 0
        pfile = 0
        if self.files:
            for p in self.files:
                if p == self.fname:
                    pfile = pidx
                print(p, file=pls)
                pidx += 1

        def cmp_line( x, y ):
            return int(x[0])-int(y[0])
            
        fidx = 0
        fline = 0     
        if self.fname and self.fname in self.lines:
            for lineno,rest in sorted(self.lines[self.fname],cmp_line):
                if int(lineno) == self.line:
                    fline = fidx
                print("%5s | %s"%(lineno,rest), file=lls)
                fidx += 1
            
        pls.seek(0)
        lls.seek(0)
        self.found_list.setstream(pls)
        self.lines_list.setstream(lls)
        if self.fname:
            self.preview.setfilename(self.fname,self.line)
            
        self.render()

        if self.preview.editor:
            self.preview.editor.goto(self.line+self.preview.height//2,0)
            self.preview.editor.goto(self.line,0)
        if self.found_list.editor:
            self.found_list.editor.goto(pfile,0)
        if self.lines_list.editor:           
            self.lines_list.editor.goto(fline,0)
        
        self.render()
            
        
        
    def do_query( self, query ):
        """ perform the query and set up the fields """
        xref_out = subprocess.Popen("xref -q %s"%(sh_escape(query)),shell=True,bufsize=1024,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout
        self.files = []
        self.lines = {}
        for res in xref_out:
            res = res.strip()
            if res:
                try:
                    lineno,path,rest = res.split("|",2)
                    path = path.strip()
                    lineno = lineno.strip()
                    rest = rest.strip()
                    if path not in self.files:
                        self.files.append(path)
    
                    if path not in self.lines:
                        self.lines[path] = [(lineno,rest)]
                    else:
                        self.lines[path].append((lineno,rest))
                except:
                    print("Error parsing result:",res, file=open("xref_extension.log","a"))

        self.files = sorted(self.files)
        if self.files:
            self.fname = self.files[0]
            self.line = int(self.lines[self.fname][0][0])
        else:
            self.fname = ""
            self.line = 0
            
        self.refresh_lists()
    

    def load_config(self):
        """ load the config file """                               
        self.conf_dir = os.path.expanduser("~/.pedxref")
        if not os.path.exists(self.conf_dir):
            os.mkdir(self.conf_dir)
        self.conf_path = self.conf_dir+"/config"
        if os.path.exists(self.conf_path):
            # load config 
            self.config = json.load(open(self.conf_path,"r"))
        else:
            self.config = { 'refresh': [ 0, ["Don't refresh in background","Refresh in background"]],
                            'interval': '60',
                            'recurse': [ 0, ["Don't recurse subdirs","Recurse subdirs"]],
                            'pattern': '.*',
                            'directory': '.',
                            'exclude': '',
                            'numthreads': '10' }
            
    def save_config(self):
        """ save the config file """
        if self.config:
            conf_file = open(self.conf_path,"w")
            # save config 
            json.dump(self.config, conf_file)
            conf_file.close()

    def handle(self,ch):
        """ handles found file selection, populating the preview window, new searches, and opening a file """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = dialog.Dialog.handle(self,ch)
        
        if ch == keytab.KEYTAB_MOUSE:
            focus_index = self.current
            focus_field = self.focus_list[self.current][1]
            ch = ret_ch
            
        if ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            if focus_field == self.found_list:
                self.fname = focus_field.getvalue().strip()
                self.line = int(self.lines[self.fname][0][0])
                self.refresh_lists()
                self.goto(focus_field)
            elif focus_field == self.lines_list:
                self.line = int(focus_field.getvalue().split("|")[0].strip())
                self.refresh_lists()
                self.goto(focus_field)
            elif focus_field == self.query:
                self.do_query(focus_field.getvalue())
                self.goto(focus_field)
            elif focus_field.getname() == "config":
                conf_dialog = XrefConfigDialog(self,"Xref Config Dialog")
                values = conf_dialog.main()
                if values:
                    self.config = values
                    self.save_config()
                    self.refresh_thread.refresh_now()

        return ret_ch

def xref_dialog(editor_manager):
    """ wrapper function for searching your xref """

    query = ""
    editor = editor_manager.getCurrentEditor()
    if editor:
        cp = editor.get_marked()
        if cp:
            for p in cp[1]:
                query = query + p.strip()
            
    d = XrefDialog(editor.parent, query)
    values = d.main()
    

def ped_ext_info():
    """ return registration information for extension_manager """
    return ( "CMD_XREF", "MANAGER", "KEYTAB_F15", "KEYTAB_REFRESH", "xref_extension" )


def ped_ext_invoke( cmd_id, target, ch ):
    """ do our thing with the target object """
    ret  = xref_dialog( target )
    return True                           
    
def main( stdscr ):
    """ test driver for xref extension """
    try:
        d = XrefDialog(stdscr,"")
        d.main()
    except Exception as e:
        log = open("xref_extension.log","w")
        print(str(e), file=log)
        print(traceback.format_exc(), file=log)
    

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except Exception as e:
        log = open("xref_extension.log","w")
        print(str(e), file=log)
        print(traceback.format_exc(), file=log)
