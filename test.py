import datetime
import pickle
import unittest
import shutil
import os

import bookkeeping
import categories

class TestBook(unittest.TestCase):

    def setUp(self):
        # read in data
        self.book=bookkeeping.book()
        self.book.dataimport('testdata/umsaetze_test.csv')

        # red in filter lists
        folder = 'filter'
        filt=categories.bookkeeping_filter()
        filt.load(folder)

        # apply filter to bookkeeping items
        self.book.filter(filt.categories)

        # check integrity
        self.assertTrue(self.book.check())

        if not os.path.exists('testdata/output'):
            os.mkdir('testdata/output')

    def tearDown(self):
        shutil.rmtree('testdata/output')

    def testImport(self):
        # import multiple overlapping datasets
        book2=bookkeeping.book()
        book2.dataimport('testdata/umsaetze_test1.csv')

    def testMultipleImports(self):
        # import multiple overlapping datasets
        book2=bookkeeping.book()
        book2.dataimport('testdata/umsaetze_test1.csv')
        book2.dataimport('testdata/umsaetze_test2.csv')
        book2.dataimport('testdata/umsaetze_test3.csv')

        # red in filter lists
        folder = 'filter'
        filt=categories.bookkeeping_filter()
        filt.load(folder)

        # apply filter to bookkeeping items
        book2.filter(filt.categories)

        self.assertEqual(book2, self.book)

    def testTextIO(self):
        self.book.writetxt('testdata/output/umsaetze.dat')
        book2=bookkeeping.book()
        book2.readtxt('testdata/output/umsaetze.dat')
        book2.writetxt('testdata/output/umsaetze2.dat')
        self.assertEqual(book2, self.book)

    def testIO(self):
        self.book.write('testdata/output/umsaetze.db')
        book2 = pickle.load(open('testdata/output/umsaetze.db', 'r'))
        self.assertEqual(book2, self.book)

if __name__ == '__main__':
    unittest.main()

