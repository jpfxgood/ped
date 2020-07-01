# Copyright 2009-2010 James P Goodwin ped tiny python editor
""" module to implement common functions for modes for the ped editor does colorizing of code """
import threading
import copy
import curses
import os

class Reader:
    """ adapter class to let EditFile be read sequetially from start to end using readline """
    def __init__(self,workfile):
        """ takes EditFile to read """
        self.workfile = workfile
        self.idx = 0

    def __del__(self):
        """ clean up my references """
        self.workfile = None

    def readline(self):
        """ implement readline to be called by tokenizer """
        ret = ""
        if self.idx < self.workfile.numLines():
            ret = self.workfile.getLine(self.idx)+'\n'
            self.idx += 1
        return ret

class Tokens:
    """ object to act as holder for token list, and to coordinate with token generation thread """
    def __init__(self):
        """ no args to constructor """
        self.tokens = {}
        self.modref = -1
        self.thread = None
        self.lock = threading.Lock()

    def __del__(self):
        """ get rid of any lingering references """
        self.tokens = None
        self.thread = None
        self.lock = None

    def getTokens(self):
        """ get the token list if there is one """
        self.lock.acquire()
        try:
            return self.tokens
        finally:
            self.lock.release()

    def setTokens(self,tokens):
        """ set the token list """
        self.lock.acquire()
        try:
            self.tokens = tokens
        finally:
            self.lock.release()

    def getModref(self):
        """ get the modification reference number that these tokens were generated from """
        self.lock.acquire()
        try:
            return self.modref
        finally:
            self.lock.release()

    def setModref(self,modref):
        """ set the modref for this set of tokens """
        self.lock.acquire()
        try:
            self.modref = modref
        finally:
            self.lock.release()

    def getThread(self):
        """ get the reference to the generation thread """
        self.lock.acquire()
        try:
            return self.thread
        finally:
            self.lock.release()

    def setThread(self,thread):
        """ set the reference to the generation thread """
        self.lock.acquire()
        try:
            self.thread = thread
        finally:
            self.lock.release()

    def refresh(self,workfile,lexer):
        """ refresh the token list based on a new EditFile, does nothing if a thread is already running """
        self.lock.acquire()
        try:
            if self.thread:
                return
            self.tokens = {}
            self.modref = -1
            self.thread = threading.Thread(target = gen_tokens, args= (self,copy.copy(workfile),lexer))
            self.thread.start()
        finally:
            self.lock.release()

def gen_tokens( tokenobj, workfile, lexer ):
    """ thread worker function, reads and tokenizes the EditFile passed to it stores the list in the Token
    object provided, updates the modref, closes the EditFile """
    tokens = {}
    row = 0
    r = Reader(workfile)
    while True:
        line = r.readline()
        if not line:
            break
        line_tokens = []
        for (index,tokentype,value) in lexer.get_tokens_unprocessed(line):
            line_tokens.append((tokentype, value, (row,index), (row,index+len(value)), line))

        tokens[row] = line_tokens
        row = row + 1
    tokenobj.setTokens(tokens)
    tokenobj.setModref(workfile.getModref())
    tokenobj.setThread(None)
    workfile.close()
    del workfile
    workfile = None

def is_token_in( token, list_token_classes ):
    """ return true if token is in the list or is a subclass of anything in the list """
    for c_token in list_token_classes:
        if token in c_token:
            return True
    return False

def window_pos(ed,line,pos):
    sc_line,sc_pos = ed.scrPos(line,pos)
    return((sc_line-ed.line)+1,sc_pos-ed.left)

def render( editor, tokens, keywords, strings, comments ):
    """ using token map (keywords, strings, comments) hilight the tokens in the editor """
    curses.init_pair(1,curses.COLOR_GREEN,curses.COLOR_BLACK)
    curses.init_pair(2,curses.COLOR_RED,curses.COLOR_BLACK)
    curses.init_pair(3,curses.COLOR_CYAN,curses.COLOR_BLACK)
    curses.init_pair(4,curses.COLOR_WHITE,curses.COLOR_BLACK)

    green = curses.color_pair(1)
    red = curses.color_pair(2)
    cyan = curses.color_pair(3)
    white = curses.color_pair(4)

    if tokens:
        tokens = tokens.getTokens()
    else:
        tokens = {}

    start_line = editor.line
    lidx = start_line
    max_sc_line = 1
    while lidx < start_line+(editor.max_y-1):
        try:
            f_line,f_pos = editor.filePos(lidx,editor.left)
            if editor.workfile.isLineChanged(editor,f_line):
                if f_line in tokens:
                    sc_line,sc_pos = window_pos(editor,f_line,f_pos)
                    editor.addstr(sc_line,0,' '*editor.max_x)
                    line_tokens = tokens[f_line]
                    for (t_type, t_text, (t_srow,t_scol), (t_erow,t_ecol), t_line) in line_tokens:
                        if is_token_in(t_type,keywords):
                            attr = cyan
                        elif is_token_in(t_type,strings):
                            attr = green
                        elif is_token_in(t_type,comments):
                            attr = red
                        else:
                            attr = white
                        for ch in t_text:
                            sc_line,sc_pos = window_pos(editor,t_srow,t_scol)
                            if sc_line >= 0 and sc_line < editor.max_y and sc_pos >= 0 and sc_pos < editor.max_x:
                                editor.addstr(sc_line,sc_pos,ch,attr)
                            t_scol += 1
                    if sc_line > max_sc_line:
                        max_sc_line = sc_line
                else:
                    if lidx >= editor.numLines(True):
                        max_sc_line += 1
                        editor.addstr(max_sc_line,0,' '*editor.max_x)
                    else:
                        sc_line,sc_pos = window_pos(editor,f_line,f_pos)
                        l = self.getContent(lidx,self.left+self.max_x,True,True)
                        self.addstr(sc_line,0,l[self.left:self.left+self.max_x])
                        if sc_line > max_sc_line:
                            max_sc_line = sc_line
            else:
                if lidx >= editor.numLines(True):
                    max_sc_line += 1
                else:
                    sc_line,sc_pos = window_pos(editor,f_line,f_pos)
                    if sc_line > max_sc_line:
                        max_sc_line = sc_line

        except Exception as e:
            pass
        lidx = lidx + 1

    return True
