from kotazutils.storage import SimpleBase, ColumnAttribute

import unittest

class TestSimpleBase(unittest.TestCase):
    def setUp(self) -> None:
        self.base = SimpleBase('test.db')
        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()

    def test_1(self):

        t1 = self.base.create_table('test', [ColumnAttribute('name', 'TEXT', primary_key=True), ColumnAttribute('age', 'INTEGER')])
        t1.insert({"name": "Alex", "age": 25})
        t1.insert({"name": "Alex2", "age": 24})
        t1.insert({"name": "Alex4", "age": 26})
        assert t1.get() == [('Alex', 25), ('Alex2', 24), ('Alex4', 26)]
        assert t1.get(order='age') == [('Alex4', 26), ('Alex', 25), ('Alex2', 24)]

    def test_2(self):
        t2 = self.base.create_table('test2', ColumnAttribute.from_dict({
                    "pos": ["INTEGER", "PRIMARY KEY", "AUTOINCREMENT", "UNIQUE"],
                    "id": ["INTEGER", "UNIQUE"],
                    "name": "Alex",
                    "age": 25,
                    "city": "Moscow",
                    "rate": 5.5,
                    "uuid": ["TEXT", "UNIQUE"],
                }))


        t2.insert({
                    "id": 2,
                    "name": "Alex",
                    "age": 25,
                    "city": "Moscow",
                    "rate": 5.5,
                    "uuid": "AABBCC",
                })
        t2.insert({
                    "id": 4,
                    "name": "Alex",
                    "age": 25,
                    "city": "Moscow",
                    "rate": 5.5,
                    "uuid": "AABBCCDD",
                })
                
        assert t2.get() == [(1, 2, 'Alex', 25, 'Moscow', 5.5, 'AABBCC'), (2, 4, 'Alex', 25, 'Moscow', 5.5, 'AABBCCDD')]

if __name__ == '__main__':
    unittest.main()