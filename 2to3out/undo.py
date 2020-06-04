# Copyright 2009 James P Goodwin ped tiny python editor
""" undo module for the ped python editor, implements a simple undo mechanism """

import copy

class UndoAction:
    """ represents one undoable action """
    def __init__(self, func, tpl ):       
        """ constructed with an undo func which is a function to call on undo
        and tpl which is a tuple of arguments to pass to the function
        a shallow copy of the tuple is made preserving the state """
        self.func = func
        self.tpl = copy.copy(tpl)

    def __del__(self):
        self.func = None
        self.tpl = None

    def undo(self):
        """ undo this action by invoking the function and passing the tuple 
        to it """
        self.func(*self.tpl)

class UndoTransaction:
    """ represents a collection of undo actions that should be undone together 
    as one transaction """
    def __init__(self, manager):
        """ constructed with a reference to the UndoManager that this
        transaction belongs to """
        self.manager = manager
        self.list = []

    def __del__(self):
        self.manager = None
        self.list = None

    def isEmpty(self):
        """ tests to see if this transaction has no actions in it """
        return not self.list

    def push(self, func, tpl ):
        """ pushes a new undo action onto this transaction """
        if not self.manager.inUndo():
            self.list.append(UndoAction(func,tpl))

    def undo(self):
        """ undoes all of the actions in this transaction """
        while self.list:
            self.list[-1].undo()
            del self.list[-1]
        self.list = []

class UndoManager:
    """ manager for a list of undo transactions for a given context """
    def __init__(self):
        """ construct an UndoManager, no arguments """
        self.transactions = []
        self.inundo = False

    def __del__(self):
        self.transactions = None

    def inUndo(self):
        """ returns true if currently executing an undo, used to prevent recursion during undo """
        return self.inundo
    
    def new_transaction(self):
        """ start a new transaction or return the current empty transaction """
        if not self.transactions or not self.transactions[-1].isEmpty():
            self.transactions.append(UndoTransaction(self))
        return self.transactions[-1]

    def get_transaction(self):
        """ return the current transaction if any """
        if self.transactions:
            return self.transactions[-1]
        else:
            return self.new_transaction()

    def undo_transaction(self):
        """ undo the current transaction """
        if self.transactions:
            self.inundo = True
            self.transactions[-1].undo()
            del self.transactions[-1]
            self.inundo = False
        return not self.transactions

    def flush_undo(self):
        """ free the transactions and forget all the undo information """
        self.transactions = []
