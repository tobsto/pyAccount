import numpy as np
import datetime
import re
import os
from decimal import Decimal

class category:
    def __init__(self, name):
        # category name
        self.name = name
        # list of string which should be contained in bk item
        self.clauses = []
        # list of list of strings which all should be contained in bk item
        self.andclauses = []

    def append_clause(self, clause):
        # append and cut comments
        self.clauses.append(clause)

    def append_andclause(self, andclause):
        # append and cut comments
        self.andclauses.append(andclause)

    def show(self):
        print "Category name: ", self.name
        if self.clauses:
            for c in self.clauses:
                print c
        if self.andclauses:
            print "AND-clauses:"
            for acl in self.andclauses:
                print acl

class bookkeeping_filter:
    def __init__(self):
        self.categories = []

    def load(self, folder):
        # get all *.lst files in folder
        lstfiles = [ f for f in os.listdir(folder) if (os.path.isfile(os.path.join(folder,f)) and os.path.join(folder,f).endswith('lst')) ]
        for lstfile in lstfiles:
            # new category named by file name
            cat = category(lstfile[:-4])

            # read in lines
            f = open(os.path.join(folder,lstfile), 'r')
            lines = f.readlines()
            f.close()

            # parse filter words 
            for l in lines:
                if l:
                    # split by all AND words
                    acl=l.split(' (UND) ')
                    # if there are any AND words, save an and-clause
                    if len(acl) != 1:
                        cat.append_andclause([ a.rstrip('\n') for a in acl])
                    # otherwise use normal clause
                    else :
                        cat.append_clause(l.rstrip('\n'))
            self.categories.append(cat)

    def show(self):
        for c in self.categories:
            c.show()
