import sqlite3
import datetime
# Create / connect to database
con = sqlite3.connect("timelord.db")
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
        # Dates are stored in plain text - SQLite doesn't have a specific date type. This still works and is sortable as long as
        # dates are stored in the YYYY-MM-DD format (highest to lowest weight)

        # SQLite3 documentation says this format should be used rather than formatted strings to prevent sql injection attacks
        # This probably isn't necessary here but there's no good reason not to
        self.cur.execute("INSERT INTO timeLog VALUES (?,?,?);", (userID, selectedDate, minutes))
        self.con.commit()

    # Get the time logged by all users
    def getTimeLogTable(self):
        res = self.cur.execute("SELECT * FROM timeLog;")
        return(res.fetchall())

    # Get total minutes logged by user with given userID
    def getTimeSum(self, userID):
        res = self.cur.execute(f"SELECT SUM(minutes) FROM timeLog WHERE userID = ?;", (userID,))
        return(res.fetchone()[0])

    # Get total minutes logged by user with given userID within the given number of days of the current date
    def getTimeSumAfterDate(self, userID, days):
        today = datetime.date.today()
        startDate = today - datetime.timedelta(days=7)
        res = self.cur.execute(f"SELECT SUM(minutes) FROM timeLog WHERE userID = ? AND selectedDate BETWEEN ? AND ?;", (userID, startDate, today))
        return(res.fetchone()[0])

    # Check whether the user with given userID has any entries in the time log table
    def userExists(self, userID):
        res = self.cur.execute(f"SELECT * FROM timeLog WHERE userID = ?;", (userID,))
        if(len(res.fetchall()) == 0):
            return False
        else:
            return True