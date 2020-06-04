# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a simple nntp news reader for ped """
import curses
import curses.ascii
import sys
import os
import tempfile
import re
import traceback
import nntplib
import nntplib_ssl
import pickle
import time
try:
    import email.utils as email_utils
except Exception as e:
    import email.Utils as email_utils
import email
from dialog import Dialog, Component, ListBox, Button, Frame, Prompt, Toggle, rect, distribute
from editor_common import Editor
from array import array
from message_dialog import message
from file_find import FileBrowseComponent
import io
import traceback
import keytab
from file_component import FileEditorComponent

# data structures for config
class ServerConfig:
    def __init__(self, server = "", usessl = 0, username="", password="", email_addr="", subscribed=[]):
        self.server = server
        self.usessl = usessl
        self.username = username
        self.password = password
        self.email_addr = email_addr
        self.subscribed = subscribed
        
class UserConfig:
    def __init__(self):
        self.server_configs = [ServerConfig()]
        self.fetch_max = 500
                            
# group cache data structure
class Group:
    def __init__(self):
        self.messages = []
        self.unread = {}
        self.start_message = 0
        self.end_message = 0
             
# items in message cache tuple
MSG_NUMBER=0
MSG_SUBJECT=1
MSG_POSTER=2
MSG_DATE=3
MSG_ID=4
MSG_REFERENCES=5
MSG_SIZE=6
MSG_LINES=7  

def normdate( date ):
    """ normalize timestamps to a single format in local time """
    timestamp = email_utils.parsedate_tz(date)
    timeval = email_utils.mktime_tz(timestamp)
    return time.strftime("%m/%d/%y %I:%M:%S%p",time.localtime(timeval))
    
def normname( addr ):
    """ normalize the e-mail address to realname, return realname if there is one, return e-mail addr otherwise """
    ( realname, mailaddr ) = email_utils.parseaddr( addr )
    if realname:
        return realname
    else:
        return mailaddr

class SearchDialog(Dialog):
    """ dialog subclass that implements search message dialog for finding a regulare expression in news messages """
    SEARCH_SUBJECT = 0
    SEARCH_SENDER = 1
    SEARCH_MESSAGE = 2
    
    def __init__(self,scr, parent_dialog, title = "Search Message" ):
        """ takes the curses window to open over, title to display, and the parent dialog for reference, will size to fit parent window """
        
        max_y,max_x = scr.getmaxyx()                         
        pw = (max_x - 4)
        ph = (max_y - 4)
        cx = max_x // 2
        dh = 5
        y = 1           
        self.searchin_choices = ["Search Subject/Number","Search Sender", "Search Entire Message"]
        
        self.searchfor = Prompt("searchfor",1,2,y,"Search for: ",pw-12,"")
        y += 1
        self.searchin = Toggle("searchin",2,2,y,pw,SearchDialog.SEARCH_SUBJECT,self.searchin_choices)
        y += 1
        self.search_button = Button("search",9,2,y,"SEARCH",Component.CMP_KEY_OK)
        self.cancel = Button("cancel",10,11,y,"CANCEL",Component.CMP_KEY_CANCEL)
        distribute([self.search_button,self.cancel],2,pw)
        Dialog.__init__(self,scr,"SearchMessage", dh, max_x, [ Frame(title),
                                                            self.searchfor,
                                                            self.searchin, 
                                                            self.search_button,
                                                            self.cancel])

class NewMessageDialog(Dialog):
    """ dialog subclass that implements compose a new message dialog for creating and posting news messages """
    def __init__(self,scr, parent_dialog, title = "New Message" ):
        """ takes the curses window to open over, title to display, and the parent dialog for reference, will size to fit parent window """
        
        max_y,max_x = scr.getmaxyx()                         
        pw = (max_x - 4)
        ph = (max_y - 4)
        cx = max_x // 2
        y = 1
        
        self.parent_dialog = parent_dialog                  
        if self.parent_dialog.current_group:
            current_group = self.parent_dialog.current_group[1]
        else:
            current_group = ""
                                                                 
        self.new_message = self.parent_dialog.conf_dir + "/newmessage"
        nm = open(self.new_message,"w")
        nm.close()
        self.groups = Prompt("groups",1,2,y,"Groups: ",pw-8,current_group)
        y += 1
        self.subject = Prompt("subject",2,2,y,"Subject: ",pw-9,"")
        y += 1
        self.body = FileEditorComponent("body",3,2,y,pw,ph-4,"New Message",self.new_message,False)
        y += (ph-4)
        self.send = Button("send",4,2,y,"SEND",Component.CMP_KEY_OK)
        self.cancel = Button("cancel",5,11,y,"CANCEL",Component.CMP_KEY_CANCEL)
        distribute([self.send,self.cancel],2,pw)
        Dialog.__init__(self,scr,"NewMessageDialog", max_y, max_x, [ Frame(title),
                                                            self.groups,
                                                            self.subject,
                                                            self.body,
                                                            self.send,
                                                            self.cancel])
        self.set_history(False)

class ReplyMessageDialog(Dialog):
    """ dialog subclass that implements compose a new message dialog for creating and posting news messages """
    def __init__(self,scr, parent_dialog, subject, groups, title = "Reply Message" ):
        """ takes the curses window to open over, title to display, and the parent dialog for reference, will size to fit parent window """
        
        max_y,max_x = scr.getmaxyx()                         
        pw = (max_x - 4)
        ph = (max_y - 4)
        cx = max_x // 2
        y = 1
        
        self.parent_dialog = parent_dialog                  
        old_message = self.parent_dialog.conf_dir + "/message"
        self.new_message = self.parent_dialog.conf_dir + "/newmessage"
        nm = open(self.new_message,"w")
        nm.close()
        self.groups = Prompt("groups",1,2,y,"Groups: ",pw-8,groups)
        y += 1
        self.subject = Prompt("subject",2,2,y,"Subject: ",pw-9,subject)
        y += 1
        self.oldmessage = FileEditorComponent("oldmessage",3,2,y,pw,(ph-4)//2,"Message",old_message,False)
        y += ((ph-4)//2)
        self.body = FileEditorComponent("body",4,2,y,pw,(ph-4)//2,"New Reply",self.new_message,False)
        y += ((ph-4)//2)
        self.send = Button("send",5,2,y,"SEND",Component.CMP_KEY_OK)
        self.cancel = Button("cancel",6,11,y,"CANCEL",Component.CMP_KEY_CANCEL)
        distribute([self.send,self.cancel],2,pw)
        Dialog.__init__(self,scr,"ReplyMessageDialog", max_y, max_x, [ Frame(title),
                                                            self.groups,
                                                            self.subject,
                                                            self.oldmessage,
                                                            self.body,
                                                            self.send,
                                                            self.cancel])
        self.set_history(False)

class NewsConfigDialog(Dialog):
    """ dialog subclass that implements a configuration dialog for managing servers, accounts, global config, and group subscriptions """
    def __init__(self,scr,title = "News Config Dialog", config = None):
        """ takes the curses window to open over, and title to display will dynamically size to parent window """
        
        max_y,max_x = scr.getmaxyx()                         
        pw = (max_x - 4)
        ph = (max_y - 4)
        cx = max_x // 2
        y = 1                                                   
        if config:
            self.config = config
        else:
            self.config = UserConfig()
            
        self.current_server = self.config.server_configs[0]     
        self.ssl_choices = ["Don't use SSL","Use SSL"]
        
        self.servers = ListBox("servers",1,2,y,8,pw,"Servers",0,self.getservers())
        y += 8
        self.server = Prompt("server",2,2,y,"Server: ",pw-8,self.getserver())
        y += 1
        self.usessl = Toggle("usessl",3,2,y,pw,self.getusessl(),self.ssl_choices)
        y += 1
        self.username = Prompt("username",4,2,y,"Username: ",pw-10,self.getusername())
        y += 1
        self.password = Prompt("password",5,2,y,"Password: ",pw-10,self.getpassword())
        y += 1
        self.email_addr = Prompt("email_addr",6,2,y,"Email Address: ", pw-15, self.getemailaddr())
        y += 1
        self.available_groups = ListBox("available",7,2,y,(ph-y-2),(pw//2)-1,"Groups",0,self.getavailablegroups())
        self.subscribed_groups = ListBox("subscribed",8,2+(pw//2),y,(ph-y-2),(pw//2)-1,"Subscribed",0,self.getsubscribed())
        y += (ph-y-2)
        self.save = Button("save",9,2,y,"SAVE",Component.CMP_KEY_OK)
        self.delete = Button("delete",10,2,y,"DELETE",Component.CMP_KEY_NOP)
        self.cancel = Button("cancel",11,11,y,"CANCEL",Component.CMP_KEY_CANCEL)
        distribute([self.save,self.delete,self.cancel],2,pw)
        Dialog.__init__(self,scr,"NewsConfigDialog", max_y, max_x, [ Frame(title),
                                                            self.servers,
                                                            self.server,
                                                            self.usessl,
                                                            self.username,
                                                            self.password,
                                                            self.email_addr,
                                                            self.available_groups,
                                                            self.subscribed_groups,
                                                            self.save,
                                                            self.delete,
                                                            self.cancel])
        self.set_history(False)
                                                            
    def sync_fields(self):
        """ sync up all the fields when something changes """
        servers = self.getservers()
        server = self.getserver()
        self.servers.setvalue((servers.index(server),servers))
        self.server.setvalue(server)
        self.usessl.setvalue((self.getusessl(),self.ssl_choices))
        self.username.setvalue(self.getusername())
        self.password.setvalue(self.getpassword())
        self.email_addr.setvalue(self.getemailaddr())
        availablegroups = self.getavailablegroups()
        subscribed = self.getsubscribed()
        (selection,choices) = self.available_groups.getvalue()
        if selection >= len(availablegroups):
            selection = len(availablegroups)-1
            if selection < 0:
                selection = 0
        self.available_groups.setvalue((selection,availablegroups))
        (selection,choices) = self.subscribed_groups.getvalue()
        if selection >= len(subscribed):
            selection = len(subscribed)-1
            if selection < 0:
                selection = 0
        self.subscribed_groups.setvalue((selection,subscribed))
                                                            
    def handle(self,ch):
        """ handles found file selection, populating the preview window, new searches, and opening a file """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = Dialog.handle(self,ch)
        if ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR,keytab.KEYTAB_TAB]:
            if focus_field == self.servers:
                (selection, choices ) = self.servers.getvalue()
                self.server.setvalue(choices[selection])
                self.current_server = self.config.server_configs[selection]
                self.sync_fields()
            elif focus_field == self.server:
                server = self.server.getvalue().lower()
                if server not in self.getservers():
                    if self.current_server.server:
                        self.config.server_configs.append(ServerConfig(server))
                        self.current_server = self.config.server_configs[-1]
                    else:
                        self.current_server.server = server
                    self.sync_fields()
                else:
                    self.current_server = self.config.server_configs[self.getservers().index(server)]
                    self.sync_fields()
            elif focus_field == self.usessl:
                (selection,choices) = self.usessl.getvalue()
                self.current_server.usessl = selection
                self.sync_fields()
            elif focus_field == self.username:        
                self.current_server.username = self.username.getvalue()
                self.sync_fields()
            elif focus_field == self.password:
                self.current_server.password = self.password.getvalue()
                self.sync_fields()
            elif focus_field == self.email_addr:
                self.current_server.email_addr = self.email_addr.getvalue()
            elif focus_field == self.available_groups:
                if ch != keytab.KEYTAB_TAB:
                    (selection,choices) = self.available_groups.getvalue()
                    self.current_server.subscribed.append(choices[selection])
                    self.sync_fields()
            elif focus_field == self.subscribed_groups:
                if ch != keytab.KEYTAB_TAB:
                    (selection,choices) = self.subscribed_groups.getvalue()
                    index = self.current_server.subscribed.index(choices[selection])
                    del self.current_server.subscribed[index]
                    self.sync_fields()
            elif focus_field == self.delete:
                if ch != keytab.KEYTAB_TAB:
                    (selection, choices) = self.servers.getvalue()
                    del self.config.server_configs[selection]
                    if len(self.config.server_configs):
                        if selection > 0:
                            self.current_server = self.config.server_configs[-1]
                        else:
                            self.current_server = self.config.server_configs[0]
                    else:
                        self.config.server_configs.append(ServerConfig())
                        self.current_server = self.config.server_configs[0]
                    self.sync_fields()
               
        return ret_ch                                          
        
    def getusessl(self):
        """ get the usessl flag, 0=don't use ssl, 1=use ssl """
        return self.current_server.usessl

    def getservers(self):
        """ get the list of servers for the current config """
        return [s.server for s in self.config.server_configs]
        
    def getserver(self):
        """ get the name of the currently selected server """
        return self.current_server.server
        
    def getusername(self):
        """ get the user name for the currently selected server """
        return self.current_server.username
        
    def getpassword(self):
        """ get the password for the currently selected server """
        return self.current_server.password
        
    def getemailaddr(self):
        """ get the e-mail address for the currently selected server """
        return self.current_server.email_addr
        
    def getavailablegroups(self):
        """ get the available groups less the subscribed ones for the current server """
        server = self.getserver()
        if server:                                       
            try:
                if self.getusessl():
                    nn = nntplib_ssl.NNTP_SSL( host=server, user=self.getusername(), password=self.getpassword() )
                else:
                    nn = nntplib.NNTP( host=server, user=self.getusername(), password=self.getpassword() )
    
                groups = nn.list()[1]
                result = list(set([g[0] for g in groups if g[3] == 'y' ]).difference(set(self.getsubscribed())))
                result.sort()
                return result
            except Exception as e:
                pass
        return []
        
    def getsubscribed(self):
        """ get the subscribed groups for the current server """
        return self.current_server.subscribed

def filter_headers( instr, fout ):
    inheaders = True
    for line in instr.split("\n"):
        if inheaders:
            if not line:         
                fout.write("\n")
                inheaders = False
            else:
                result = line.split(":",1)
                name = result[0]
                if name.strip() in ["From","Newsgroups","Subject","Date","Xref"]:
                    fout.write(line+"\n")
        else:
            fout.write(line+"\n")              
            
def write_msg( msg, fout ):
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            filter_headers(str(part),fout)
        elif part.get_filename() != None:
            fout.write("-[Attachment]-(%s)"%part.get_filename())
            
def fetch_msg( nn, id ):
    (hresp, hnumber, hrrid, headers) = nn.head(id)
    (mresp, mnumber, mrrid, body) = nn.body(id)
    msg_string ="\n".join(headers)+"\n\n"+"\n".join(body)
    return email.message_from_string(msg_string)
    
        
class NewsBrowseDialog(Dialog):
    """ dialog subclass that implements a news browse dialog with a list of news groups, list of messages,
        and a preview pane, provides a reply button, a goto message button, a search button, and a config button
        """
    def __init__(self,scr,title = "News Browse Dialog"):
        """ takes the curses window to pop up over, title to display, will dynamically size to parent window """

        message(scr, "News Browse","Synchronizing News",False)
#        scr.nooutrefresh()
        
        # load the config right away
        self.load_config()
        self.current_group = None
        self.current_server = None
        self.group_cache = {}
        self.group_table = []
        self.current_message = None
        self.searchfor = None
        self.searchin = 0
        
        self.win = None
        self.groups = None
        self.messages = None
        self.preview = None
        self.new = None
        self.reply = None
        self.refresh = None
        self.search = None
        self.markread = None
        self.config_button = None
        self.cancel = None
        self.children = []
        self.setparent(scr)
        self.resize()
        max_y,max_x = self.getparent().getmaxyx()
        Dialog.__init__(self,scr,"NewsBrowseDialog", max_y, max_x, [ Frame(title),
                                                            self.groups,
                                                            self.messages,
                                                            self.preview,
                                                            self.new,
                                                            self.reply,
                                                            self.refresh,
                                                            self.search,
                                                            self.markread,
                                                            self.config_button,
                                                            self.cancel])
                                                            
    def __del__(self):
        """ make sure we get rid of any open coonections and save any updates to the cache """
        try:
            # save any outstanding group cache entries
            self.savecache()
        except:
            pass
            
    def resize( self ):
        """ compute the postions of all of the components """
        max_y,max_x = self.getparent().getmaxyx()
        if self.win:
            del self.win
            self.win = None
        self.win = self.getparent().subwin(max_y,max_x,0,0)
        self.win.clear()
        self.win.keypad(1)
        pw = (max_x - 4)
        ph = (max_y - 4)
        cx = max_x // 2
        y = 1
        if not self.groups:
            self.groups = ListBox("groups",1,2,y,ph,pw//4,"Groups", 0, self.getgroups())
        else:
            self.groups.setpos(2,y)
            self.groups.setsize(ph,pw//4)
            
        if not self.messages:
            self.messages = ListBox("messages",2,(pw//4)+2,y,ph//2,pw - pw//4,"Messages", 0, self.getmessages())
        else:
            self.messages.setpos((pw//4)+2,y)
            self.messages.setsize(ph//2,pw-pw//4)
            
        y += (ph//2)
        if not self.preview:
            self.preview = FileBrowseComponent("preview",3,(pw//4)+2,y,pw-pw//4,ph-(ph//2),"Current Message",None,False)
        else:
            self.preview.setpos((pw//4)+2,y)
            self.preview.setsize(ph-(ph//2),pw-pw//4)
            
        y += (ph-(ph//2))
        if not self.new:
            self.new = Button("new",4,2,y,"NEW(F9)",Component.CMP_KEY_NOP)
        else:
            self.new.setpos(2,y)
        
        if not self.reply:
            self.reply = Button("reply",5,2,y,"REPLY(F10)",Component.CMP_KEY_NOP)
        else:
            self.reply.setpos(2,y)
            
        if not self.refresh:
            self.refresh = Button("refresh",6,2,y,"REFRESH(F11)",Component.CMP_KEY_NOP)
        else:
            self.refresh.setpos(2,y)
            
        if not self.search:
            self.search = Button("search",7,2,y,"SEARCH(F5)",Component.CMP_KEY_NOP)
        else:
            self.search.setpos(2,y)
            
        if not self.markread:
            self.markread = Button("markread",8,2,y,"MARKREAD(F8)",Component.CMP_KEY_NOP)
        else:
            self.markread.setpos(2,y)
            
        if not self.config_button:
            self.config_button = Button("config",9,20,y,"CONFIG",Component.CMP_KEY_NOP)
        else:
            self.config_button.setpos(2,y)
            
        if not self.cancel:
            self.cancel = Button("cancel",10,30,y,"CANCEL",Component.CMP_KEY_CANCEL)
        else:
            self.cancel.setpos(2,y)
            
        distribute( [self.new,self.reply,self.refresh,self.search,self.markread,self.config_button,self.cancel], 2, pw )
        
        for c in self.children:
            c.setparent(self.win)
            
    def savecache( self ):
        """ save cache to disk """
        # save any outstanding group cache entries
        for server in self.user_config.server_configs:
            for group in server.subscribed:
                if (server.server,group) in self.group_cache:
                    self.savegroup(server, group)
        
    def getConnection( self, server ):
        """ get an nntp connection to a server from the cache or create a new one """
        if server.usessl:
            nn = nntplib_ssl.NNTP_SSL( host = server.server, user = server.username, password = server.password )
        else:
            nn = nntplib.NNTP( host = server.server, user = server.username, password = server.password )
        return nn
         
    def loadgroup( self, server, group ):
        """ load a group cache object from the file system or create it if it isn't there """
        group_path = "%s/%s.%s"%(self.conf_dir, server.server,group)
        if os.path.exists(group_path):
            group_file = open(group_path,"r")
            up = pickle.Unpickler(group_file)
            group_object = up.load()
            group_file.close()
            return group_object
        else:
            return Group()
        
    def savegroup( self, server, group ):
        """ save the group cache object corresponding to the group name passed """
        group_path = "%s/%s.%s"%(self.conf_dir, server.server,group)
        group_file = open(group_path,"w")
        pk = pickle.Pickler(group_file)
        pk.dump(self.group_cache[(server.server,group)])
        group_file.close()
        
        
    def refreshgroup( self, server, group ):
        """ refresh the group cache object corresponding to the group name passed using the server config provided """
        group_obj = self.group_cache[(server.server,group)]

        try:
            nn = self.getConnection(server)
                             
            news_group = nn.group(group)
            end = int(news_group[3])
            if end != group_obj.end_message:
                if group_obj.end_message:
                    start = group_obj.end_message+1
                else:
                    start = max(0,end-self.user_config.fetch_max)
                    group_obj.start_message = start
                group_obj.end_message = end
                over = nn.xover(str(start),str(end))[1]
                ids = [o[4] for o in over]
                group_obj.messages.extend(over)
                def cmp_msg( x, y ):
                    if int(x[0]) > int(y[0]):
                        return -1
                    elif int(x[0]) == int(y[0]):
                        return 0
                    else:
                        return 1
                group_obj.messages.sort( cmp=cmp_msg )
                for id in ids:
                    group_obj.unread[id] = True
        except Exception as e:
            raise Exception("Error refreshing %s, %s, %s"%(server.server,group,str(e)),e)
            
    def reloadgroups(self):
        """ force a refresh of all of the groups """
        return self.getgroups(True)
    
    def getgroups(self,force_refresh=False):
        """ return list of groups we've subscribed to with number of unread in parens """
        for server in self.user_config.server_configs:
            for group in server.subscribed:
                if (server.server,group) not in self.group_cache:
                    group_object = self.loadgroup(server,group)
                    self.group_cache[(server.server, group)] = group_object
                    self.group_table.append((server.server,group,group_object))
                    self.refreshgroup(server, group)
                elif force_refresh:
                    self.refreshgroup(server, group)
                    
        self.group_table.sort()
                
        return ["%s (%d)"%(k[1],len(k[2].unread)) for k in self.group_table]
        
    def getmessages(self):
        """ if there is a group selected, return the list of message metadata for that group """
        if self.current_group:
            group_obj = self.group_cache[self.current_group]                
            unread_map = { True:"*", False:" " }
            return ["%s %8.8s %19.19s %-16.16s %s"%(unread_map[m[MSG_ID] in group_obj.unread],m[MSG_NUMBER],normdate(m[MSG_DATE]),normname(m[MSG_POSTER]),m[MSG_SUBJECT]) for m in group_obj.messages]
        else:
            return []
        
    def load_config(self):
        """ load the config file """                               
        self.user_config = None   
        self.conf_dir = os.path.expanduser("~/.pednews")
        if not os.path.exists(self.conf_dir):
            os.mkdir(self.conf_dir)
        self.conf_path = self.conf_dir+"/config"
        if os.path.exists(self.conf_path):
            conf_file = open(self.conf_path,"r")
            up = pickle.Unpickler(conf_file)
            self.user_config = up.load()
            conf_file.close()       
        else:
            self.user_config = UserConfig()
            
    def save_config(self):
        """ save the config file """
        if self.user_config:
            conf_file = open(self.conf_path,"w")
            pk = pickle.Pickler(conf_file)
            pk.dump(self.user_config)
            conf_file.close()    
            
    def server_from_groups( self, groups ):
        """ given a list of groups, find the server record """
        for server in self.user_config.server_configs:
            if groups.split(",")[0] in server.subscribed:
                return server
        return None
            
    def newmessage(self):
        """ compose a new message and send post it """
        newmessage = NewMessageDialog(self.win,self)
        values = newmessage.main()
        if values:
            newmessage.body.editor.save()
            mesg = io.StringIO()
            groups = newmessage.groups.getvalue()
            server = self.server_from_groups( groups )
            print("Newsgroups:",groups, file=mesg)
            print("Subject:",newmessage.subject.getvalue(), file=mesg)
            print("From:",server.email_addr, file=mesg)
            print("", file=mesg)
            print(open(newmessage.new_message,"r").read(), file=mesg)
            mesg.seek(0)
            self.getConnection(server).post(mesg)
            mesg.close()
                       
    def getheaders(self,server,message_id):
        """ return a dict with headername: value """
        headers = {}
        hlist = self.getConnection(server).head(message_id)[3]
        for h in hlist:
            values = h.split(":",1)
            if len(values) == 2:
                headers[values[0].strip()] = values[1].strip()
            else:
                headers[values[0].strip()] = ""
        return headers
        
    def replymessage(self):
        """ reply to the current message """
        if self.current_message:                                 
            server = self.current_server
            headers = self.getheaders(server,self.current_message[MSG_ID])
            if self.current_message[MSG_SUBJECT].lower().startswith("re:"):
                subject = self.current_message[MSG_SUBJECT]
            else:
                subject = "re:"+self.current_message[MSG_SUBJECT]
            replymessage = ReplyMessageDialog(self.win,self,subject,headers["Newsgroups"])
            values = replymessage.main()
            if values:
                replymessage.body.editor.save()
                mesg = io.StringIO()
                groups = replymessage.groups.getvalue()
                print("Newsgroups:",groups, file=mesg)
                print("Subject:",replymessage.subject.getvalue(), file=mesg)
                print("From:",server.email_addr, file=mesg)
                references = ""
                if "References" in headers:
                    references += headers["References"]
                if "Message-ID" in headers:
                    references += " " + headers["Message-ID"]
                print("References:",references, file=mesg)
                
                print("", file=mesg)
                print(open(replymessage.new_message,"r").read(), file=mesg)
                mesg.seek(0)
                self.getConnection(server).post(mesg)
                mesg.close()
        
    def performsearch(self, offset = 0):
        """ do a search """
        if self.current_group and self.searchfor:
            (selection,choices) = self.messages.getvalue()
            group_obj = self.group_cache[self.current_group]
 
            msg_idx = selection + offset
            while msg_idx < len(group_obj.messages):
                m = group_obj.messages[msg_idx]
                if self.searchin == SearchDialog.SEARCH_SUBJECT:
                    if re.search(self.searchfor,"%s %s"%(m[MSG_NUMBER],m[MSG_SUBJECT])):
                        break
                elif self.searchin == SearchDialog.SEARCH_SENDER:
                    if re.search(self.searchfor,m[MSG_POSTER]):
                        break
                elif self.searchin == SearchDialog.SEARCH_MESSAGE:
                    try:
                        if re.search(self.searchfor," ".join(self.getConnection(self.current_server).article(m[MSG_ID])[3])):
                            break
                    except Exception as e:
                        pass
                msg_idx += 1
            else:                 
                message( self.win, title="Not Found", message="%s not found"%(self.searchfor))
                return
            self.messages.setvalue((msg_idx,choices))
        
    def searchagain(self):
        """ repeat prior search if any, from the next message """
        self.performsearch(1)
        
    def searchmessage(self):
        """ search for a regular expression in messages """
        searchmessage = SearchDialog( self.win, self )
        values = searchmessage.main()
        if values:
            self.searchfor = values["searchfor"]
            self.searchin = values["searchin"][0]
            
            self.performsearch()
    
    def clearunread(self):
        """ clear unread marks for the current group """
        if self.current_group:
            self.group_cache[self.current_group].unread = {}
            
        (group_selection,choices) = self.groups.getvalue()
        (messages_selection,choices) = self.messages.getvalue()
        
        self.groups.setvalue((group_selection,self.getgroups()))
        self.messages.setvalue((messages_selection,self.getmessages()))
        
    def checkunread(self):
        """ loop over all the groups and refresh them with any new unread messages """
        message(self.win, "News Browse","Synchronizing News",False)
        (selection,choices) = self.groups.getvalue()
        id = None
        if self.current_message:
            id = self.current_message[MSG_ID]

        if self.group_table:
            group_key = (self.group_table[selection][0],self.group_table[selection][1])
        else:
            group_key = None
            
        self.reloadgroups() 
                   
        if group_key:
            for idx in range(0,len(self.group_table)):
                if group_key[0] == self.group_table[idx][0] and group_key[1] == self.group_table[idx][1]:
                    break
            else:
                idx = 0
        else:
            idx = 0
                
        self.groups.setvalue((idx,self.getgroups()))
        self.current_group = group_key
        
        if self.current_group:
            for server in self.user_config.server_configs:
                if server.server == self.current_group[0]:
                    self.current_server = server
                    break
            if id:
                message_idx = 0
                for msg in self.group_cache[self.current_group].messages:
                    if msg[MSG_ID] == id:
                        self.current_message = msg
                        self.messages.setvalue((message_idx,self.getmessages()))
                        return
                    message_idx += 1
            self.current_message = self.group_cache[self.current_group].messages[0]
        else:
            self.current_message = None
            self.current_server = None
        self.messages.setvalue((0,self.getmessages()))
            
    def handle(self,ch):
        """ handles found file selection, populating the preview window, new searches, and opening a file """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = Dialog.handle(self,ch)
        if ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            if focus_field == self.groups:
                (selection,choices) = self.groups.getvalue()
                self.current_group = (self.group_table[selection][0],self.group_table[selection][1])
                for server in self.user_config.server_configs:
                    if server.server == self.current_group[0]:
                        self.current_server = server
                        break
                else:
                    raise Exception("Invalid server in list!")
                self.messages.setvalue((0,self.getmessages()))
            elif focus_field == self.messages:
                self.current = focus_index
                if self.current_group:
                    (selection,choices) = self.messages.getvalue()
                    group_obj = self.group_cache[self.current_group]
                    server = self.current_server
                    try:
                        nn = self.getConnection( server )
                        message_path = self.conf_dir+"/message"
                        message_file = open(message_path,"w")
                        self.current_message = group_obj.messages[selection]
                        id = self.current_message[MSG_ID]
                        try:
                            msg = fetch_msg( nn, id )
                            write_msg(msg,message_file)
                        except Exception as e:
                            message_file.write("ERROR: %s\n"%(str(e)))
                        references = []
                        references.extend(self.current_message[MSG_REFERENCES])
                        references.reverse()
                        for rid in references:
                            message_file.write("=================================[Thread Message]=================================\n")
                            try:
                                msg = fetch_msg( nn, id )
                                write_msg(msg,message_file)
                            except Exception as e:
                                message_file.write("ERROR: %s\n"%(str(e)))
                            message_file.write("=================================[ End Message  ]=================================\n")
                        message_file.close()
                        self.preview.setfilename(message_path,0)
                        if id in group_obj.unread:
                            del group_obj.unread[id]
                            (group_selection,choices) = self.groups.getvalue()
                            self.groups.setvalue((group_selection,self.getgroups()))
                        self.messages.setvalue((selection,self.getmessages()))
                    except Exception as e:
                        raise Exception("Error fetching %s, %s, %s"%(server.server,self.current_group[1],str(e)),e)
            elif focus_field == self.config_button:
                conf_dialog = NewsConfigDialog(self.win,"News Config Dialog",self.user_config)
                values = conf_dialog.main()
                if values:
                    self.save_config()     
                    self.group_cache = {}
                    self.group_table = []
                    self.checkunread()
                else:
                    self.load_config()
            elif focus_field == self.preview:
                line = self.preview.getvalue()
                if line.startswith("-[Attachment]-"):
                    start = line.find("(")+1
                    end = line.rfind(")")
                    filename = line[start:end]
                    nn = self.getConnection(self.current_server)
                    msg = fetch_msg(nn,self.current_message[MSG_ID])
                    for part in msg.walk():
                        if part.get_filename() == filename:        
                            download_dir = os.path.expanduser("~/ped_download")
                            if not os.path.exists(download_dir):
                                os.mkdir(download_dir)
                            try_filename = os.path.join(download_dir,filename)
                            filenumber = 0
                            while (os.path.exists(try_filename)):
                               try_filename = os.path.join(download_dir,filename)+"."+str(filenumber)
                               filenumber = filenumber + 1
                            outfile = open(try_filename,"w")
                            outfile.write(part.get_payload(decode=True))
                            outfile.close()
                            message(self.win,"Attachment saved",try_filename,True)
                            break
                    else:
                        message(self.win,"Error","Failed to save attachment",True)
            elif focus_field == self.new:
                self.newmessage()
            elif focus_field == self.reply:
                self.replymessage()
            elif focus_field == self.search:
                self.searchmessage()
            elif focus_field == self.refresh:
                self.checkunread()
            elif focus_field == self.markread:
                self.clearunread()
        elif ch == keytab.KEYTAB_F10:
            self.replymessage()
        elif ch == keytab.KEYTAB_F11:
            self.checkunread()
        elif ch == keytab.KEYTAB_F05:
            self.searchmessage()
        elif ch == keytab.KEYTAB_F09:
            self.newmessage()
        elif ch == keytab.KEYTAB_F03:
            self.searchagain()
        elif ch == keytab.KEYTAB_F08:
            self.clearunread()
               
        return ret_ch
                                          
news_browser = None
def newsbrowse(scr, title = "News Browse Dialog"):
    """ wrapper function for browsing news """
    global news_browser

    if not news_browser:
        news_browser = NewsBrowseDialog(scr,title)
    values = news_browser.main()
    return values

def main(stdscr):
    """ test main driver for news browse dialog """
    try:
        values = newsbrowse(stdscr)
    except Exception as e:
        log = open("newsbrowse.log","w")
        print(str(e), file=log)
        print(traceback.format_exc(), file=log)

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except Exception as e:
        log = open("newsbrowse.log","w")
        print(str(e), file=log)
        print(traceback.format_exc(), file=log)
