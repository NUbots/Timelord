# Create and connect to database
import sqlite3
con = sqlite3.connect("timelord.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS timeLog(userID, date, minutes)")
con.close()

# Python program to illustrate destructor
class SQLConnection:
    # Initializing
    def __init__(self):
        self.con = sqlite3.connect("timelord.db")
        self.cur = self.con.cursor()
        print('Connection opened')

    # Deleting (Calling destructor)
    def __del__(self):
        print('Connection closed')
        self.con.close()

    def addTimeLogEntry(self, userID, date, minutes):
        self.cur.execute(f"""
        INSERT INTO timeLog VALUES
            ('{userID}', '{date}', {minutes})
        """)
        self.con.commit()

    def getTimeLogTable(self):
        res = self.cur.execute("SELECT userID, date, minutes FROM timeLog")
        print(res.fetchall())