# Copyright 2015 James P Goodwin ped tiny python editor
""" undo module for the ped python editor, implements a simple undo mechanism """

import sys


class Change:
    """ Represents one span of lines that have been changed """
    def __init__(self, start_line = 0, end_line = sys.maxsize):
        """ Constructed with the first last lines of span of change and the revision number of the change """
        self.start_line = start_line
        self.end_line = end_line

    def __str__(self):
        return "Change( start_line = %d, end_line = %d )"%(self.start_line,self.end_line)

    def is_changed(self, line):
        """ tests to see if a specified line number is changed """
        if line >= self.start_line and line <= self.end_line:
            return True
        else:
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
        self.views = {}

    def __del__(self):
        self.change_list = None

    def __str__(self):
        if self.change_list:
            return "["+",".join([str(f) for f in self.change_list])+"]"
        else:
            return "[]"

    def add_view(self,view):
        """ adds a new view to this change manager """
        if view not in self.views:
            self.views[view] = self.change_list

    def remove_view(self,view):
        """ removes a view from this change manager """
        if view in self.views:
            del self.views[view]

    def has_changes(self,view):
        """ returns true if there are pending changes """
        if self.views[view]:
            return True
        else:
            return False

    def is_changed(self, view, line ):
        """ returns true if a line is marked as changed at or after the revNo passed """
        if not self.views[view]:
            return False

        for c in self.views[view]:
            if c.is_changed(line):
                return True
        return False

    def flush(self, view):
        """ reset the change list to empty used when the whole page is going to need refresh no matter what """
        self.views[view] = None
        all_none = True
        for v in self.views:
            if self.views[v]:
                all_none = False
                break
        if all_none:
            self.change_list = []

    def changed(self, start_line = 0, end_line = sys.maxsize ):
        """ mark a range of lines as changed or by default mark them all as changed """
        nc = Change(start_line,end_line)
        new_change_list = []
        for c in self.change_list:
            if nc.is_equal(c) or nc.is_contained(c):
                continue
            elif nc.is_adjacent(c):
                if c.start_line < nc.start_line:
                    nc = Change(c.start_line,end_line)
                else:
                    nc = Change(start_line,c.end_line)
            elif nc.is_overlapped( c ):
                if c.start_line < nc.start_line:
                    nc = Change(c.start_line,nc.end_line)
                else:
                    nc = Change(nc.start_line,c.end_line)
            elif c.is_contained(nc):
                nc = Change(c.start_line,c.end_line)
            else:
                new_change_list.append(Change(c.start_line,c.end_line))
        new_change_list.insert(0,nc)
        self.change_list = new_change_list
        for v in self.views:
            self.views[v] = self.change_list
