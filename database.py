import sqlite3
import datetime

def createLogTable():
    # Create time log table
    con = sqlite3.connect("timelord.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS time_log(user_id TEXT NOT NULL, selected_date date, minutes INTEGER NOT NULL)")
    con.close()

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect("timelord.db")
        self.cur = self.con.cursor()

    def __del__(self):
        # Close SQL connection (saving changes to file)
        self.con.close()

    def insert_timelog_entry(self, user_id, selected_date, minutes):
        # Dates are stored in plain text - SQLite doesn't have a specific date type. This still works and is sortable as long as
        # dates are stored in the YYYY-MM-DD format (highest to lowest weight)

        # SQLite3 documentation says this format should be used rather than formatted strings to prevent sql injection attacks
        # This probably isn't necessary here but there's no good reason not to
        self.cur.execute("INSERT INTO time_log VALUES (?,?,?);", (user_id, selected_date, minutes))
        self.con.commit()

    # Get the time logged by all users
    def timelog_table(self):
        res = self.cur.execute("SELECT * FROM time_log;")
        return(res.fetchall())

    # Get total minutes logged by user with given user_id
    def time_sum(self, user_id):
        # If the user has entries in the database return their total time logged, otherwise return 0
        res = self.cur.execute(f"SELECT SUM(minutes) FROM time_log WHERE user_id = ?;", (user_id,))
        minutes = res.fetchone()[0]
        print(minutes)
        if (minutes != None):
            return(minutes)
        else:
            return(0)

    # Get total minutes logged by user with given user_id within the given number of days of the current date
    def time_sum_after_date(self, user_id, days):
        today = datetime.date.today()
        startDate = today - datetime.timedelta(days=7)
        # If the user has entries in the database return their time logged within the specified period, otherwise return 0
        res = self.cur.execute(f"SELECT SUM(minutes) FROM time_log WHERE user_id = ? AND selected_date BETWEEN ? AND ?;", (user_id, startDate, today))
        minutes = res.fetchone()[0]
        print(minutes)
        if (minutes != None):
            return(minutes)
        else:
            return(0)
