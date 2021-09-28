import sqlite3
import datetime

class Databasesetup:
    def __init__(self, dbname="todo.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        tblstmt = "CREATE TABLE IF NOT EXISTS items (description text, owner text, date timestamp, deleted integer)"
        itemidx = "CREATE INDEX IF NOT EXISTS itemIndex ON items (description ASC)"
        ownidx = "CREATE INDEX IF NOT EXISTS ownIndex ON items (owner ASC)"
        self.conn.execute(tblstmt)
        self.conn.execute(itemidx)
        self.conn.execute(ownidx)
        self.conn.commit()

    def add_item(self, item_text, owner):
        stmt = "INSERT INTO items (description, owner, date, deleted) VALUES (?, ?, ?, ?)"
        args = (item_text, owner, datetime.datetime.now(), 0)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_item(self, item_text, owner):
        stmt = "UPDATE items SET deleted = 1 WHERE description = (?) AND owner = (?)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_all(self, item_text, owner):
        stmt = "UPDATE items SET deleted = 1 WHERE owner = (?)"
        args = (owner, )
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def get_users(self):
        cur = self.conn.cursor()
        stmt = "SELECT distinct owner FROM items"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_num_messages(self, item_text, owner):
        cur = self.conn.cursor()
        stmt = "SELECT count(DISTINCT description) AS alias FROM items"
        args = (owner, )
        cur.execute(stmt, ())
        num = cur.fetchone()
        return num

        
    def get_items(self, owner):
        stmt = "SELECT description FROM items WHERE owner = (?) and deleted = 0"
        args = (owner, )
        return [x[0] for x in self.conn.execute(stmt, args)]
