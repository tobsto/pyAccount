#!/usr/bin/env python

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import datetime
import decimal
import os
import argparse

import bookkeeping
import categories

def main():
    parser = argparse.ArgumentParser(description='Analyse pesonal money flow', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output', default='%s/output' % os.getcwd(), help='Output folder')
    parser.add_argument('--dbfile', default='%s/data/umsaetze.db' % os.getcwd(), help='Path to database file')
    parser.add_argument('--filterdir', default='%s/filter' % os.getcwd(), help='Path to filter list folder')

    subparsers = parser.add_subparsers(help="Give a keyword", dest='mode')

    # import new data
    import_parser = subparsers.add_parser("import", help='Import new data in cvs format to database')
    import_parser.add_argument('importfile', help='Original file to import')

    filter_parser = subparsers.add_parser("filter", help="Apply filter from filterdir to database to sort bookkeeping items")

    show_parser = subparsers.add_parser("show", help="Raw print of database")
    show_parser.add_argument('printmode', choices=('raw', 'categories'))

    check_parser = subparsers.add_parser("check", help="Check database")

    plot_parser = subparsers.add_parser("plot", help="Plot data")
    plot_parser.add_argument('plotmode', choices=('histogram', 'timeseries', 'piechart'))
    plot_parser.add_argument('-s', '--start', help="Start date in format YYYY-MM-DD")
    plot_parser.add_argument('-e', '--end', help="End date in format YYYY-MM-DD")
    group = plot_parser.add_mutually_exclusive_group()
    group.add_argument('-w', '--whitelist', nargs='*', help="Whitelist for categories to include")
    group.add_argument('-b', '--blacklist', nargs='*', help="Blacklist for categories to include")
    plot_parser.add_argument('-f', '--hardcopy', action='store_true', help="Save plot file")
    plot_parser.add_argument('-m', '--average_months', action='store_true', help="Average over a period from 15th to 15th")
    plot_parser.add_argument('--average_dom', help="Alternative day of month for average")
    
    args = parser.parse_args()

    # bookkeeping items
    book=bookkeeping.book()
    # read in database
    if os.path.exists(args.dbfile):
        book.readtxt(args.dbfile)
    # or create folder if it does not exist
    else:
        if not os.path.exists(os.path.dirname(args.dbfile)):
            os.mkdir(os.path.dirname(args.dbfile))

    # import data
    if args.mode == "import":
        try:
            book.dataimport(args.importfile)

        except Exception as e:
            print "Error during data import. Break"
            print e.message
            exit(1)
        book.writetxt(args.dbfile)

    # apply filter
    if args.mode == "filter":
        try:
            # read in filter lists
            filt=categories.bookkeeping_filter()
            filt.load(args.filterdir)

            # apply filter to bookkeeping items
            book.filter(filt.categories)
        except Exception as e:
            print "Error during filtering. Break"
            print e.message
            exit(1)
        book.writetxt(args.dbfile)

    # print
    if args.mode == "show":
        if args.printmode == 'raw':
            book.show()
        elif args.printmode == 'categories':
            book.showByCategory()

    # check database 
    if args.mode == "check":
        status = book.check()
        if status:
            print "Check successful"
        else:
            print "Check unsuccessful"

    # plot data
    if args.mode == "plot":
        # prepare output folder
        if args.hardcopy and not os.path.exists(args.output):
            os.mkdir(args.output)

        # set start and end dates
        end = book.data.ix[0].name
        start = book.data.ix[-1].name
        if args.start:
            start = pd.to_datetime(datetime.datetime.strptime(args.start,"%Y-%m-%d"))
        if args.end:
            end = pd.to_datetime(datetime.datetime.strptime(args.end,"%Y-%m-%d"))
        duration=start.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d")

        # set catogories to plot according to blacklist and whitelist
        cats = book.data.loc[~book.data['Category'].isnull()]['Category'].unique()
        if args.whitelist:
            cats = args.whitelist
        elif args.blacklist:
            for blackcat in args.blacklist:
                cats = filter(lambda x: x!=blackcat, categories)

        # filter data
        # filter out dates
        book.data = book.data[(book.data.index>start) & (book.data.index<end)]
        # average over months

        # categorize
        sum  = 0.0
        for cn in cats:
            subdata = book.data.loc[book.data['Category']==cn]
            print cn.ljust(25), " : ", subdata['Value'].sum()
            sum = sum + subdata['Value'].sum()
        print "Total: ", sum

        # plot histogram
        if args.plotmode == "histogram":

            for cn in cats:
                subdata = book.data.loc[book.data['Category']==cn]
                print subdata
                print cn.ljust(25), " : ", subdata['Value'].sum()
            exit(0)
            filename = args.output + "/histogram_" + duration + ".eps"
            data = []
            labels = []
            for ic in items_categorized:
                sum = decimal.Decimal(0.0)
                for i in ic[1]:
                    sum = sum + i.value 
                if (sum<0):
                    data.append(-sum)
                    labels.append(ic[0])
            ypos = np.arange(len(data))
            plt.barh(ypos, np.array(data), align='center', alpha=0.4)
            plt.yticks(ypos, labels)
            plt.xlabel('Ausgaben')
            plt.title('Zeitraum: %s' % duration)
            plt.legend()
            plt.show()
        exit(0)

        # plot piechart
        if args.plotmode == "piechart":
            filename = args.output + "/piechart" + duration + ".eps"
            data = []
            labels = []
            for ic in items_categorized:
                sum = decimal.Decimal(0.0)
                for i in ic[1]:
                    sum = sum + i.value 
                if (sum<0):
                    data.append(-sum)
                    labels.append(ic[0])
            cmap= plt.cm.prism
            colors = cmap(np.linspace(0., 1., len(data)))
            plt.pie(data, colors=colors, labels=labels, labeldistance=1.05)
            plt.title('Ausgaben im Zeitraum: %s' % duration)
            plt.show()

        # plot time series
        if args.plotmode == "timeseries":
            filename = args.output + "/timeseries" + duration + ".eps"
            for ic in items_categorized:
                x = np.array([i.date for i in ic[1]])
                y = np.array([i.value for i in ic[1]])
                plt.plot(x,y, label=ic[0])
            plt.legend()
            plt.show()

if __name__=="__main__":
    main()
