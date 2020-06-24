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

    y = 1
    lidx = editor.line
    while lidx < editor.line+(editor.max_y-1):
        try:
            if editor.isLineChanged(lidx):
                if lidx in tokens:
                    line_tokens = tokens[lidx]
                    for (t_type, t_text, (t_srow,t_scol), (t_erow,t_ecol), t_line) in line_tokens:
                        o_srow = t_srow
                        o_erow = t_erow
                        o_scol = t_scol
                        o_ecol = t_ecol
                        (o_srow,o_scol) = editor.scrPos(o_srow,o_scol)
                        (o_erow,o_ecol) = editor.scrPos(o_erow,o_ecol)
                        o_srow -= editor.line
                        o_erow -= editor.line
                        o_scol -= editor.left
                        o_ecol -= editor.left
                        t_start = 0
                        t_end = len(t_text)

                        if o_srow < 0 and o_erow < 0:
                            continue

                        if (o_scol < 0 and o_ecol < 0) or (o_scol > editor.max_x-1 and o_ecol > editor.max_x-1):
                            continue

                        if o_srow > (editor.max_y-2):
                            break

                        if t_type in keywords:
                            attr = cyan
                        elif t_type in strings:
                            attr = green
                        elif t_type in comments:
                            attr = red
                        else:
                            attr = white

                        for ch in range(0,len(t_text)):
                            if o_srow >= 0 and o_srow < editor.max_y-1 and o_scol >= 0 and o_scol <= editor.max_x-1:
                                try:
                                    editor.addstr(o_srow+1,o_scol,t_text[ch], attr)
                                except:
                                    pass
                            o_scol += 1
                            if editor.wrap:
                                if o_scol > editor.max_x-1:
                                    o_srow += 1
                                    o_scol = 0
                            if o_srow > (editor.max_y-2):
                                break

                        if o_srow > (editor.max_y-2):
                            break

                    if line_tokens and o_srow <= (editor.max_y-2):
                        while o_scol <= editor.max_x-1:
                            try:
                                editor.addstr(o_srow+1,o_scol,' ', white)
                            except:
                                pass
                            o_scol += 1
                    y =  o_srow+1
                else:
                    l = editor.getContent(lidx,editor.left+editor.max_x,True,True)
                    editor.addstr(y,0,l[editor.left:editor.left+editor.max_x])
        except Exception as e:
            pass
        y = y + 1
        lidx = lidx + 1

    return True

#def render( editor, tokens, keywords, strings, comments ):
#    """ using token lists (keywords, strings, comments) hilight the tokens in the editor """
#    curses.init_pair(1,curses.COLOR_GREEN,curses.COLOR_BLACK)
#    curses.init_pair(2,curses.COLOR_RED,curses.COLOR_BLACK)
#    curses.init_pair(3,curses.COLOR_CYAN,curses.COLOR_BLACK)
#    curses.init_pair(4,curses.COLOR_WHITE,curses.COLOR_BLACK)
#
#    green = curses.color_pair(1)
#    red = curses.color_pair(2)
#    cyan = curses.color_pair(3)
#    white = curses.color_pair(4)
#
#    token_list = tokens.getTokens()
#    for (t_type, t_text, (t_srow,t_scol), (t_erow,t_ecol), t_line) in token_list:
#        f_line = t_srow - 1
#        o_srow = t_srow - 1
#        o_erow = t_erow - 1
#        o_scol = t_scol
#        o_ecol = t_ecol
#        (o_srow,o_scol) = editor.scrPos(o_srow,o_scol)
#        (o_erow,o_ecol) = editor.scrPos(o_erow,o_ecol)
#        o_srow -= editor.line
#        o_erow -= editor.line
#        o_scol -= editor.left
#        o_ecol -= editor.left
#        t_start = 0
#        t_end = len(t_text)
#
#        if o_srow < 0 and o_erow < 0:
#            continue
#
#        if (o_scol < 0 and o_ecol < 0) or (o_scol >= editor.max_x-1 and o_ecol >= editor.max_x-1):
#            continue
#
#        if o_srow > (editor.max_y-2):
#            break
#
#        if t_type in keywords:
#            attr = cyan
#        elif t_type in strings:
#            attr = green
#        elif t_type in comments:
#            attr = red
#        else:
#            attr = white
#
#        for ch in range(0,len(t_text)):
#            if o_srow >= 0 and o_srow < editor.max_y-1 and o_scol >= 0 and o_scol < editor.max_x-1:
#                try:
#                    if editor.isLineChanged(f_line):
#                        editor.addstr(o_srow+1,o_scol,t_text[ch], attr)
#                except:
#                    pass
#            o_scol += 1
#            if editor.wrap:
#                if o_scol >= editor.max_x-1:
#                    o_srow += 1
#                    f_line += 1
#                    o_scol = 0
#            if o_srow > (editor.max_y-2):
#                break
#
#        if o_srow > (editor.max_y-2):
#            break
#    return True
