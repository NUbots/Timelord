import sqlite3
import datetime
# Create / connect to database
con = sqlite3.connect("timelord.db", detect_types=sqlite3.PARSE_DECLTYPES)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS timeLog(userID TEXT NOT NULL, selectedDate date, minutes INTEGER NOT NULL)")
con.close()

today = datetime.date.today()

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect("timelord.db")
        self.cur = self.con.cursor()

    def __del__(self):
        # Close SQL connection (saving changes to file)
        self.con.close()

    def addTimeLogEntry(self, userID, selectedDate, minutes):
        self.cur.execute(f"INSERT INTO timeLog VALUES ('{userID}', {selectedDate}, {minutes})")
        print(type(selectedDate))
        self.con.commit()

    def getTimeLogTable(self):
        res = self.cur.execute("SELECT * FROM timeLog")
        return(res.fetchall())

    def getTimeSum(self, userID):
        res = self.cur.execute(f"SELECT SUM(minutes) FROM timeLog WHERE userID = '{userID}'")
        return(res.fetchone()[0])

    def getTimeSumAfterDate(self, userID, days):
        startDate = datetime.date.today() - datetime.timedelta(days=7)
        print(startDate)
        res = self.cur.execute(f"SELECT SUM(minutes) FROM timeLog WHERE userID = '{userID}' BETWEEN {startDate} AND {today}")
        return(res.fetchone()[0])

    def userExists(self, userID):
        res = self.cur.execute(f"SELECT * FROM timeLog WHERE userID = '{userID}';")
        if(len(res.fetchall()) == 0):
            return False
        else:
            return True