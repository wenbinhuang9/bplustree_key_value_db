import unittest

from bplustree_db.bplustree import bplus_tree
from bplustree_db.randomaccessfile import randomaccessfile


class MyTestCase(unittest.TestCase):
    def test_randomaccessfile(self):
        filehd = randomaccessfile("./random_test", "w+")
        offset = 0
        first_write = -1
        second_write = 312
        filehd.writeint(first_write, offset)
        offset += 4
        filehd.writelong(second_write, offset)

        offset = 0
        first_write_from_file = filehd.readint(offset)
        print(first_write_from_file)
        offset += 4
        sec_write_from_file = filehd.readlong(offset)
        print (first_write == first_write_from_file)
        self.assertEqual(first_write == first_write_from_file, True)
        self.assertEqual(second_write == sec_write_from_file, True)

    def test_open(self):
        pass

    def test_close(self):
        pass

    def test_insert(self):
        tree = bplus_tree()
        tree.open("./")

        for i in range(100):
            tree.insert(i, i)
            val = tree.get(i)
            print(val)
            self.assertEqual(val == i, True)

    def test_delete(self):
        tree = bplus_tree()
        tree.open("./")

        for i in range(100):
            tree.insert(i, i)
            val = tree.get(i)
            print(val)
            self.assertEqual(val == i, True)

            tree.delete(i)
            val = tree.get(i)
            print(val)
            self.assertEqual(val == None, True)

    ## todo the performance is really bad when data increasing
    def test_delete_2(self):
        tree = bplus_tree()
        tree.open("./")
        num = 1000
        for i in range(num):
            tree.insert(i, i)
            val = tree.get(i)
            ##print(val)
            self.assertEqual(val == i, True)

        for i in range(num):
            if i == 2:
                print("debug from here")
            tree.delete(i)
            val = tree.get(i)
            ##print(val)
            self.assertEqual(val == None, True)


    def test_query(self):
        tree = bplus_tree()
        tree.open("./")
        for i in range(100):
            val = tree.get(i)
            print (val)
            self.assertEqual(val == i, True)


if __name__ == '__main__':
    unittest.main()
