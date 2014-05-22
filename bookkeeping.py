import datetime
import decimal
import codecs
import sqlite3
import pickle
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.dates import date2num

import categories

# pretty print
def pp(s, length):
    if len(s)>length:
        return s[:length-3] + '...'
    else:
        return s.ljust(length)

# parse lines to get item
def parse_raw_item(itemline):
    words = []
    for w in itemline.split(';'):
        words.append(w.strip('"\r\n'))
    # get date
    date_str = words[0].split('.')
    year = int(date_str[2])
    month = int(date_str[1])
    day = int(date_str[0])
    date = datetime.date(year, month, day)

    # get item
    descr = words[3].encode('utf-8')
    value = decimal.Decimal(words[4].replace('.', '').replace(',', '.'))
    return (date, value, descr)

class book:
    def __init__(self):
        self.data = pd.DataFrame()

    def __eq__(self, other):
        return (self.data == other.data)

    def __ne__(self, other):
        return not self.__eq__(other)

    def dataimport(self, filename):
        infile = codecs.open(filename, 'r', encoding='latin1')
        lines = infile.readlines()
        infile.close()

        # Get line number of first and last item
        start = map(lambda x: x.startswith('"Neuer Kontostand"'), lines).index(True) + 3
        end = map(lambda x: x.startswith('"Alter Kontostand"'), lines).index(True) - 1

        # get data
        dates = []
        values = []
        descrs = []
        lines = [l for l in lines[start:end] if l]
        for l in lines:
            date, value, descr = parse_raw_item(l)
            dates.append(date)
            values.append(value)
            descrs.append(descr)

        # convert to data frame
        newdata = pd.DataFrame({'Date' : dates, 'Value' : values, 'Descr' : descrs}, columns=['Date', 'Value', 'Descr'])
        # index by date
        newdata.set_index('Date', inplace=True)
        # append empty categories and comment columns
        newdata['Category'] = np.nan
        newdata['Comment'] = np.nan       

        # add to existing data 
        if not self.data.empty:
            self.data = pd.concat([self.data, newdata])
            # remove duplicates in date, value and descr
            self.data.drop_duplicates(cols = ('Value', 'Descr'), inplace=True)
        else:
            self.data = newdata

    def clear(self):
        self.data = None

    def write(self, filename):
        f = open(filename, 'w')
        pickle.dump(self, f)
        f.close()

    def writetxt(self, filename):
        self.data.to_csv(filename, sep='\t')

    def readtxt(self, filename):
        self.data = pd.read_csv(filename, delimiter='\t', parse_dates=True, index_col='Date')

    def show(self, maxlen=None):
        if maxlen:
            print self.data.head(maxlen)
        else:
            print self.data

    def showCategory(self, category_name):
        print self.data[self.data['Category' == category_name]]

    def showByCategory(self):
        for cat in self.data.loc[~self.data['Category'].isnull()]['Category'].unique():
            print cat
            self.showCategory(cat)

    def sumCategory(self, category_name):
        return self.data.loc[self.data['Category'] == category_name]['Value'].sum()

    def sum(self):
        return self.data['Value'].sum()

    def check(self):
        csum = decimal.Decimal(0.0)
        for cn in self.data.loc[~self.data['Category'].isnull()]['Category'].unique():
            csum = csum + self.sumCategory(cn)
        tsum = self.sum()
        if csum == tsum:
            return True
        else:
            return False

    def filter(self, cats):
        count = 0
        for index, d in self.data.loc[self.data['Category'].isnull()].iterrows():
            found_cats=[]
            # loop over all categories
            for cat in cats:
                found = False
                # check all clauses
                for clause in cat.clauses:
                    if clause in d['Descr']:
                        found = True
                # check all and-clauses
                if not found:
                    for aclause in cat.andclauses:
                        conditions=[]
                        for clause in aclause:
                            if clause in d['Descr']:
                                conditions.append(True)
                            else:
                                conditions.append(False)
                        if all(conditions):
                            found = True
                            break
                if found:
                    found_cats.append(cat)
                    break

            # check if more than on categorie was found
            if len(found_cats) > 1:
                print "Error: The following description: "
                print d['Descr']
                print "fits multiple categories:"
                for cat in found_cats:
                    print cat.name
                print "You need to adapt the filter lists!"
                exit(0)
            elif len(found_cats) == 0:
                print ""
                print "Warning: The following item does not fit any of the know categories:"
                print "Date:        ", "%04i-%02i-%02i" % d.name.isocalendar()
                print "Value:       ", d['Value']
                print "Description: ", d['Descr']
                cnstr=''
                for cn in self.data.loc[~self.data['Category'].isnull()]['Category'].unique():
                    cnstr += cn + " | "
                print cnstr
                catname = raw_input("Choose a category or assign a new one: ")
                comment = raw_input("Add a comment (optional): ")
                self.data.iloc[count, self.data.columns.get_loc("Category")]=catname
                self.data.iloc[count, self.data.columns.get_loc("Comment")]=comment

            elif len(found_cats) == 1:
                print "Date:        ", d.name, found_cats[0].name, "Description: ", d['Descr']
                self.data.iloc[count, self.data.columns.get_loc("Category")]=found_cats[0].name
            count = count +1
