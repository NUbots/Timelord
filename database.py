import sqlite3
# Create / connect to database
con = sqlite3.connect("timelord.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS timeLog(userID, date, minutes)")
con.close()

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect("timelord.db")
        self.cur = self.con.cursor()
        print('Connection opened')

    def __del__(self):
        # Close SQL connection
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

    def getTimeSum(self, userID):
        res = self.cur.execute(f"SELECT userID, SUM(minutes) FROM timeLog WHERE userID = '{userID}' GROUP BY userID")
        return(res.fetchone())