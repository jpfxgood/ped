# Copyright 2014 James P Goodwin ped tiny python editor
""" extension to implement AIM im client  """
import curses
import os
import sys
from editor_common import Editor
from dialog import Dialog, Component, ListBox, Button, Frame, Prompt, Toggle, rect, distribute
from editor_common import Editor
from file_component import FileEditorComponent
import keytab
import json
from twisted.words.protocols import oscar
from twisted.internet import protocol, reactor
from twisted.python import log
import threading
import Queue
import pprint
import traceback
from bs4 import BeautifulSoup
import editor_manager
import atexit
import time

DEFAULT_CHAT_FILE = os.path.expanduser("~/.pedchat/chat.log")

class ChatConnection(oscar.BOSConnection):
    parent_thread = None
    capabilities = [oscar.CAP_CHAT]
    
    def putEvent( self, event ):
        ChatConnection.parent_thread.events.put(event)
#        print >>open("./chat.log","a"),pprint.pformat(event)

    def initDone(self):
        self.requestSelfInfo().addCallback(self.gotSelfInfo)
        self.requestSSI().addCallback(self.gotBuddyList)
        self.putEvent(("initDone",self))

    def gotSelfInfo(self, user):
        self.putEvent(("gotSelfInfo",user))

    def gotBuddyList(self, l):
        self.putEvent(("gotBuddyList",l))
        self.activateSSI()
        self.setIdleTime(0)
        self.clientReady()

    def createdRoom(self, (exchange, fullName, instance)):
        self.putEvent(("createdRoom", exchange, fullName, instance ))
        self.joinChat(exchange, fullName, instance).addCallback(self.chatJoined)
        
    def updateBuddy(self, user):
        self.putEvent(("updateBuddy", user))
        
    def offlineBuddy(self, user):
        self.putEvent(("offlineBuddy", user))
        
    def receiveMessage(self, user, multiparts, flags):
        self.putEvent(("receiveMessage", user, multiparts, flags ))
        
    def messageAck(self, (username, message)):
        self.putEvent(("messageAck", username, message ))
        
    def gotAway(self, away, user):
        self.putEvent(("gotAway", away, user ))
            
    def receiveWarning(self, newLevel, user):
        self.putEvent(("receiveWarning", newLevel, user))
        
    def warnedUser(self, oldLevel, newLevel, username):
        self.putEvent(("warnedUser", oldLevel, newLevel, username))
        
    def receiveChatInvite(self, user, message, exchange, fullName, instance, shortName, inviteTime):
        self.putEvent(("receiveChatInvite", user, message, exchange, fullName, instance, shortName, inviteTime ))
        self.joinChat(exchange, fullName, instance).addCallback(self.chatJoined)

    def chatJoined(self, chat):
        self.putEvent(("chatJoined", chat))
#        print 'joined chat room', chat.name
#        print 'members:',map(lambda x:x.name,chat.members)

    def chatReceiveMessage(self, chat, user, message):
        self.putEvent(("chatReceiveMessage", chat, user, message ))
#        print 'message to',chat.name,'from',user.name,':',message
#        if user.name!=self.name: chat.sendMessage(user.name+': '+message)
#        if message.find('leave')!=-1 and chat.name!='%s Chat'%SN: chat.leaveChat()
        
    def chatMemberJoined(self, chat, member):
        self.putEvent(("chatMemberJoined", chat, member ))
#        print member.name,'joined',chat.name
        
    def chatMemberLeft(self, chat, member):
        self.putEvent(("chatMemberLeft", chat, member))
#        print member.name,'left',chat.name
#        print 'current members',map(lambda x:x.name,chat.members)
#        if chat.name!="%s Chat"%SN and len(chat.members)==1:
#            print 'leaving', chat.name
#            chat.leaveChat()

class ChatAuthenticator(oscar.OscarAuthenticator):
   BOSClass = ChatConnection

class ChatThread( threading.Thread ):
    def __init__(self, username, password,host,port):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.events = Queue.Queue()
        threading.Thread.__init__(self)
        self.daemon = True
        
    def run( self ):
        try:
            ChatAuthenticator.BOSClass.parent_thread = self
            log.startLogging(open(os.devnull,"w"))
            protocol.ClientCreator(reactor, ChatAuthenticator, self.username, self.password, icq=0).connectTCP(*(self.host, self.port))
            reactor.run(installSignalHandlers=0)
        except Exception,e:
#            print >>open("./chat.log","a"),str(e)
#            print >>open("./chat.log","a"),traceback.format_exc()
             raise
         

    def connect( self, username, password, host, port ):
        """ wrapper to switch connections via the reactor thread """
        reactor.callFromThread( self._connect,  username, password, host, port )
        
    def _connect( self, username, password, host, port ):
        """ disconnect and reconnect new """
        protocol.ClientCreator(reactor, ChatAuthenticator, username, password, icq=0).connectTCP(*(host, port))
            
        
    def stop( self ):
        reactor.callFromThread(reactor.stop)


class ChatConfigDialog(Dialog):
    """ configuration dialog to input server, userid, password """
    def __init__(self, chat_dialog, title = "Chat Config" ):
        """ constructor takes the chat_dialog we're nested over and a title """
        p_win = chat_dialog.win
        min_y,min_x = p_win.getbegyx()
        max_y,max_x = p_win.getmaxyx()
        max_x += min_x
        max_y += min_y
        width = 56
        height = 9
        x = (max_x + min_x)/2 - width/2
        y = (max_y + min_y)/2 - height/2
        Dialog.__init__(self,p_win,"ChatConfig", height, width, [
            Frame(title),
            Prompt("server",1,2,2,"Server: ", 50-8, chat_dialog.config.get("server","")),
            Prompt("port",2,2,3,"Port: ", 13-6, chat_dialog.config.get("port","")),
            Prompt("name",3,2,4,"Screen Name: ",50-13, chat_dialog.config.get("name","")),
            Prompt("password",4,2,5,"Password: ",50-10, chat_dialog.config.get("password","")),
            Button("ok",5,2,7,"OK",Component.CMP_KEY_OK),
            Button("cancel",6,7,7,"CANCEL",Component.CMP_KEY_CANCEL)],y,x)
        

class ChatDialog(Dialog):
    """ dialog subclass that implements a chat screen with a list of IM buddies, transcript, response field,
        and send button and a cancel button
        """
        
    chat_thread = None
    
    def __init__(self,scr,title = "Chat"):
        """ takes the curses window to pop up over, title to display, will dynamically size to parent window """
        self.current_buddy = None
        self.current_server = None
        self.chat_connection = None
        self.win = None
        self.buddys = None
        self.messages = None
        self.reply = None
        self.reply_border = None
        self.config_button = None
        self.cancel = None
        self.config = {}
        self.status = {}
        self.children = []
        self.myname = None
        self.event_time = time.clock()
        self.title = title
        # load the config right away
        self.load_config()
        self.setparent(scr)
        self.resize()
        max_y,max_x = self.getparent().getmaxyx()
        min_y,min_x = self.getparent().getbegyx()
        Dialog.__init__(self,scr,"ChatDialog", max_y, max_x, [ Frame(title),
                                                            self.buddys,
                                                            self.messages,
                                                            self.reply_border,
                                                            self.reply,
                                                            self.config_button,
                                                            self.cancel], min_y, min_x)
        self.start_chat_thread()
    

    def __copy__(self):
        """ return a copy of this dialog """
        return ChatDialog(self.getparent(), self.title)
        
    def __del__(self):
        """ clean up the chat thread when we go away """
        self.stop_chat_thread()

    def start_chat_thread( self ):
        """ start the chat thread if we have configuration """
        if self.config:
            if not ChatDialog.chat_thread:
                ChatDialog.chat_thread = ChatThread(self.config["name"],self.config["password"],self.config["server"],int(self.config["port"]))
                ChatDialog.chat_thread.start()
            else:
                self.connect(self.config["name"],self.config["password"],self.config["server"],int(self.config["port"]))
                
    def save_messages( self ):
        """ save the message list to the chat transcript """
        if self.messages.editor:
            self.messages.editor.workfile.setReadOnly(False)
            self.messages.editor.save()
            self.messages.editor.workfile.setReadOnly(True)
            
    def stop_chat_thread( self ):
        """ stop the chat thread if one exists """
        if ChatDialog.chat_thread:
            self.handle_chat_events()
                                                            
    def render( self ):
        """ process events whenever render is called """
        if time.clock() - self.event_time > 0.5:
            self.handle_chat_events()
            self.event_time = time.clock()
        Dialog.render(self)
        
    def resize( self ):
        """ compute the postions of all of the components """
        max_y,max_x = self.getparent().getmaxyx()
        min_y,min_x = self.getparent().getbegyx()
        if self.win:
            del self.win
            self.win = None
        self.win = self.getparent().subwin(max_y,max_x,min_y,min_x)
        self.win.clear()
        self.win.keypad(1)
        pw = (max_x - 4)
        ph = (max_y - 4)
        cx = max_x / 2
        y = 1  
        if not self.buddys:
            self.buddys = ListBox("buddys",1,2,y,ph-3,pw/4,"Buddys", 0)
        else:
            self.buddys.setpos(2,y)
            self.buddys.setsize(ph-3,pw/4)
            
        if not self.messages:
            self.messages = FileEditorComponent("messages",2,(pw/4)+2,y,pw - pw/4,ph-3,"Transcript", DEFAULT_CHAT_FILE, False, True)
        else:
            self.messages.setpos((pw/4)+2,y)
            self.messages.setsize(ph-3,pw-pw/4)
            
        y += (ph-2)
        if not self.reply:
            self.reply = Prompt("reply",3,3,y,"",pw-2)
            self.reply_border = Frame( "", 2, y-1, pw, 3 )
        else:
            self.reply.setpos(3,y)
            self.reply.setsize(1,pw-2)
            self.reply_border.setpos( 2, y-1 )
            self.reply_border.setsize( pw, 3 )
            
        y += 2
        
        if not self.config_button:
            self.config_button = Button("config",4,20,y,"CONFIG",Component.CMP_KEY_NOP)
        else:
            self.config_button.setpos(2,y)
            
        if not self.cancel:
            self.cancel = Button("cancel",5,30,y,"EXIT",Component.CMP_KEY_CANCEL)
        else:
            self.cancel.setpos(2,y)
            
        distribute( [self.config_button,self.cancel], 2, pw )
        
        for c in self.children:
            c.setparent(self.win)

    def load_config(self):
        """ load the config file """                               
        self.conf_dir = os.path.expanduser("~/.pedchat")
        if not os.path.exists(self.conf_dir):
            os.mkdir(self.conf_dir)
        self.conf_path = self.conf_dir+"/config"
        if os.path.exists(self.conf_path):
            # load config 
            self.config = json.load(open(self.conf_path,"r"))
        else:
            self.config = {}
            
    def save_config(self):
        """ save the config file """
        if self.config:
            conf_file = open(self.conf_path,"w")
            # save config 
            json.dump(self.config, conf_file)
            conf_file.close()
            
    def write_message( self, message ):
        """ write a message to the current chat log """
        ed = self.messages.editor
        ed.workfile.setReadOnly(False)
        nLines = ed.workfile.numLines()
        for l in message.split("\n"):
            ed.workfile.insertLine(nLines,l+'\n')
            nLines += 1
        ed.workfile.setReadOnly(True)
        ed.rewrap(True)
        ed.goto(nLines-1,0)
        
        if ed.scr:
            ed.scr.refresh()
         

    def show_item( self, i ):
        """ for debugging, drill down into the event """
        if hasattr(i,"__dict__"):
            self.write_message(pprint.pformat(i.__dict__))
        elif isinstance(i, list) or isinstance(i, tuple):
            self.write_message("[\n")
            for k in i:
                self.show_item(k)
            self.write_message("]\n")
        else:
            self.write_message(pprint.pformat(i))
            
    def log_item( self, i ):
        """ for debugging, drill down into the event """
        if hasattr(i,"__dict__"):
            print >>open("./chat.log","a"),pprint.pformat(i.__dict__)
        elif isinstance(i, list) or isinstance(i, tuple):
            print >>open("./chat.log","a"),"["
            for k in i:
                self.log_item(k)
            print >>open("./chat.log","a"),"]"
        else:
            print >>open("./chat.log","a"),pprint.pformat(i)

    def set_buddy_list( self, buddys ):
        """ rebuild the buddy list """
        choice,selection = self.buddys.getvalue()
        bl = []
        for sl in buddys:
            if isinstance(sl,list) or isinstance(sl,tuple):
                for b in sl:
                    if isinstance(b,oscar.SSIGroup):
                        for u in b.users: 
                            bl.append("%s : %s : %s"%(u.name, self.status.get(u.name,"unknown"), b.name))
        if selection:
            n,s,g = selection[choice].split(":")
            for choice in range(0,len(bl)):
                if bl[choice].startswith(n) and bl[choice].endswith(g):
                    break
            else:
                choice = 0
        self.buddys.setvalue((choice,bl))
        
    def update_buddy( self, user ):
        """ update the status of a buddy """
        self.status[user.name] = user.icqStatus
        choice,selection = self.buddys.getvalue()
        if selection:
            for i in range(0,len(selection)):
                n,s,g = selection[i].split(":")
                if n.startswith(user.name):
                    selection[i] = n+": "+ user.icqStatus +" :"+g
                    break         
            self.buddys.setvalue((choice,selection))

    def offline_buddy( self, user ):
        """ update the status of a buddy to offline """
        self.status[user.name] = "offline"
        choice,selection = self.buddys.getvalue()
        if selection:
            for i in range(0,len(selection)):
                n,s,g = selection[i].split(":")
                if n.startswith(user.name):
                    selection[i] = n+": offline :"+g
                    break
            self.buddys.setvalue((choice,selection))
            
    def receive_message(self, user, multiparts, flags ):
        """ recieve a message and format it so we can output it """
        self.set_current_buddy( user.name )
        for p in multiparts:
            for mp in p:
                self.write_message( "%s: %s"%(user.name,BeautifulSoup(mp).get_text()) )

    def handle_chat_events(self):
        """ process all pending chat events """
        if ChatDialog.chat_thread:
            empty = False
            while not empty:
                try:
                    item = ChatDialog.chat_thread.events.get_nowait()
                    eid = item[0]
                    if eid == "initDone":
                        self.chat_connection = item[1]
                    elif eid == "gotBuddyList":
                        self.set_buddy_list( item[1] )
                    elif eid == "updateBuddy":
                        self.update_buddy( item[1] )
                    elif eid == "offlineBuddy":
                        self.offline_buddy( item[1] )
                    elif eid == "receiveMessage":
                        self.receive_message( item[1], item[2], item[3] )
                    elif eid == "gotSelfInfo":
                        self.myname = item[1].name
                        
#                    self.log_item(item)
                    
                    ChatDialog.chat_thread.events.task_done()
                except Queue.Empty:
                    empty = True
            self.save_messages()
                    
    def start_chat( self, buddy_ref ):
        """ start new chat by switching to a different transcript and current buddy """
        buddy,status,group = buddy_ref.split(":")
        buddy=buddy.strip()
        status=status.strip()
        group=group.strip()
        self.set_current_buddy( buddy )
        
        
    def set_current_buddy( self, buddy):
        """ set a new buddy as the current buddy """
        if buddy != self.current_buddy:
            self.save_messages()
            self.messages.setfilename(os.path.expanduser(os.path.join("~/.pedchat","%s.log"%(buddy))),-1)
            self.messages.render()
            self.current_buddy = buddy
            choice,selection = self.buddys.getvalue()
            if selection:
                for i in range(0,len(selection)):
                    if selection[i].startswith(buddy):
                        break
                else:
                    i = 0
                self.buddys.setvalue((i,selection))
            
    def send_message( self, user, message ):
        """ send a message to the user """
        self.chat_connection.sendMessage(user,message)
        self.write_message("%s: %s"%(self.myname,message))                                             
        
    def connect( self, username, password, host, port ):
        """ connect using different connection settings """
        if ChatDialog.chat_thread:
            if self.chat_connection:
                self.chat_connection.disconnect()
            self.messages.setfilename(DEFAULT_CHAT_FILE,0)
            self.buddys.setvalue((0,[]))
            ChatDialog.chat_thread.connect( username, password, host, port )
            
    def handle(self,ch):
        """ handles found file selection, populating the preview window, new searches, and opening a file """
        self.handle_chat_events()
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        if ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            if focus_field == self.buddys:
                (selection,choices) = self.buddys.getvalue()
                # make the selected buddy current in chat
                self.start_chat(choices[selection])
                self.current = self.reply.getorder()-1
                ch = Component.CMP_KEY_NOP
            elif focus_field == self.config_button:
                conf_dialog = ChatConfigDialog(self,"Chat Config Dialog")
                values = conf_dialog.main()
                if values:
                    self.config = values
                    self.save_config()
                    self.current = self.buddys.getorder()-1
                    ch = Component.CMP_KEY_NOP
                    self.connect( values['name'], values['password'], values['server'], int(values['port']) )
            elif focus_field == self.reply and ch == keytab.KEYTAB_CR:
                # type in the reply
                self.send_message( self.current_buddy, self.reply.getvalue() )
                self.reply.setvalue("")
                self.reply.home()
                ch = Component.CMP_KEY_NOP
        elif ch in [keytab.KEYTAB_F04,keytab.KEYTAB_ALTK,keytab.KEYTAB_ALTE]:
            return ch

        ret_ch = Dialog.handle(self,ch)
        
        if ret_ch in [Component.CMP_KEY_CANCEL]:
            self.stop_chat_thread()
            ret_ch = keytab.KEYTAB_ALTK
               
        return ret_ch

def ped_ext_info():
    """ return registration information for extension_manager """
    return ( "CMD_IM", "MANAGER", "KEYTAB_F14", "KEYTAB_REFRESH", "im_extension" )


def ped_ext_invoke( cmd_id, target, ch ):
    """ do our thing with the target object """
    frame = target.replaceFrame(editor_manager.DialogFrame)
    frame.setdialog(ChatDialog(frame.win))
    return True
    
def main(stdscr):
    min_y,min_x = stdscr.getbegyx()
    max_y,max_x = stdscr.getmaxyx()
    win = stdscr.subwin( max_y - 4, (max_x / 2) - 2 , 2, max_x / 2 )
    d = ChatDialog( win )
#    cd = ChatConfigDialog( d )
    values = d.main()
    d.stop_chat_thread()
#    print >>open("./im_extesnsion.out","w"), values
               

if __name__ == '__main__':
    try:
        curses.wrapper(main)
#        thread = ChatThread("jpfxgood","Dana2012","login.oscar.aol.com",5190)
#        thread.start()
    except Exception,e:
        print >>open("./chat.log","a"),str(e)
        print >>open("./chat.log","a"),traceback.format_exc()
