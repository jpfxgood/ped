# Copyright 2015 James P Goodwin ped tiny python editor
""" undo module for the ped python editor, implements a simple undo mechanism """

import sys

#change_log = open("change.log","a")
#change_debg = True

#def logChange( change, message ):
#    if change_debg:
#        print >>change_log, change, message
    
class Change:
    """ Represents one span of lines that have been changed """
    def __init__(self, start_line = 0, end_line = sys.maxsize, revNo = sys.maxsize):
        """ Constructed with the first last lines of span of change and the revision number of the change """
        self.start_line = start_line
        self.end_line = end_line
        self.revNo = revNo
        
    def __str__(self):
        return "Change( start_line = %d, end_line = %d, revNo = %d )"%(self.start_line,self.end_line,self.revNo)

    def is_changed(self, line, revNo = 0):
        """ tests to see if a specified line number is changed at the revNo or greater in this span """
#        logChange( self, "is_changed( %d, %d )"%(line, revNo))
        if line >= self.start_line and line <= self.end_line and revNo < self.revNo:
#            logChange( self, "is_changed( %d, %d ) return True"%(line, revNo))
            return True
        else:
#            logChange( self, "is_changed( %d, %d ) return False"%(line, revNo))
            return False
            
    def is_equal(self, change ):
        """ tests to see if this change is equal in span to another change """
        if self.start_line == change.start_line and self.end_line == change.end_line:
            return True
        else:
            return False
        
    def is_overlapped(self, change ):
        """ tests to see if this change overlaps another span """
        if (change.start_line < self.start_line and change.end_line >= self.start_line and change.end_line <= self.end_line) or (change.start_line >= self.start_line and change.start_line <= self.end_line and change.end_line > self.end_line):
            return True
        else:
            return False
        
    def is_adjacent(self, change ):
        """ tests to see if this change is next to another span """
        if (change.end_line == self.start_line-1 or self.end_line == change.start_line-1):
            return True
        else:
            return False
        
    def is_samerev(self, change ):
        """ tests to see if this change is at the same revision """
        if self.revNo == change.revNo:
            return True
        else:
            return False
        
    def is_contained(self, change ):
        """ tests to see if this change completely contains the change """
        if change.start_line >= self.start_line and change.start_line <= self.end_line and change.end_line <= self.end_line and change.end_line >= self.start_line:
            return True
        else:
            return False

class ChangeManager:
    """ manager for a list of changed lines for a given context so we can use it to do minimal redraw """
    def __init__(self):
        """ construct an ChangeManager, no arguments """
        self.change_list = []

    def __del__(self):
        self.change_list = None
        
    def __str__(self):
        if self.change_list:
            return "["+",".join([str(f) for f in self.change_list])+"]"
        else:
            return "[]"

    def is_changed(self, line, revNo = 0):
        """ returns true if a line is marked as changed at or after the revNo passed """
        if not self.change_list:
            return True
            
        for c in self.change_list:
            if c.is_changed(line,revNo):
                return True
        return False
        
    def flush(self):
        """ reset the change list to empty used when the whole page is going to need refresh no matter what """
        self.change_list = []

    def changed(self, start_line = 0, end_line = sys.maxsize, revNo = sys.maxsize ):
        """ mark a range of lines as changed or by default mark them all as changed """
        nc = Change(start_line,end_line,revNo)
        new_change_list = []
        for c in self.change_list:
            if nc.is_equal(c) | nc.is_contained(c):
                continue
            elif nc.is_adjacent(c) and nc.is_samerev(c):
                if c.start_line < nc.start_line:
                    nc = Change(c.start_line,end_line,revNo)
                else:
                    nc = Change(start_line,c.end_line,revNo)
            elif nc.is_overlapped( c ):
                if c.start_line < nc.start_line:
                    new_change_list.append(Change(c.start_line,nc.start_line-1,c.revNo))
                else:
                    new_change_list.append(Change(nc.end_line+1,c.end_line,c.revNo))
            elif c.is_contained(nc):
                new_change_list.append(Change(c.start_line,nc.start_line-1,c.revNo))
                new_change_list.append(Change(nc.end_line+1,c.end_line,c.revNo))
            else:
                new_change_list.append(c)
        new_change_list.insert(0,nc)
        self.change_list = new_change_list
 #       logChange( self, "ChangeManager changed( %d, %d, %d )"%(start_line,end_line,revNo))
