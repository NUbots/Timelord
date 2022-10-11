import sqlite3
import datetime

def createLogTable(DBName):
    # Create time log table
    con = sqlite3.connect(DBName)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS time_log(entry_num INTEGER NOT NULL, user_id TEXT NOT NULL, entry_date date NOT NULL, selected_date date NOT NULL, minutes INTEGER NOT NULL, project TEXT)")
    con.close()

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect("timelord.db")
        self.cur = self.con.cursor()

    def __del__(self):
        # Close SQL connection (saving changes to file)
        self.con.commit()
        self.con.close()

    def insert_timelog_entry(self, user_id, selected_date, minutes):
        # Dates are stored in plain text - SQLite doesn't have a specific date type. This still works and is sortable as long as
        # dates are stored in the YYYY-MM-DD format (highest to lowest weight)

        # SQLite3 documentation says this format with placeholder question marks and a tuple of values should be used rather than formatted strings to prevent sql injection attacks
        # This probably isn't necessary here but there's no good reason not to

        today = datetime.date.today()

        res = self.cur.execute("SELECT MAX(entry_num) FROM time_log WHERE user_id = ?;", (user_id,))
        entry_num = res.fetchone()[0]
        if (entry_num == None): 
            entry_num = 1
        else:
            entry_num += 1

        self.cur.execute("INSERT INTO time_log VALUES (?,?,?,?,?, NULL);", (entry_num, user_id, selected_date, minutes, today))

    def remove_last_entry(self, user_id):
        res = self.cur.execute("SELECT user_id, entry_num FROM time_log WHERE user_id = ? ORDER BY entry_num DESC LIMIT 1;", (user_id,))
        print(res.fetchall())
        # Limit isn't allowed in SQLite delete commands by default. It can be enabled when compiling sqlite from source but isn't in the standard Python package used here so a select subquery is used instead.
        self.cur.execute("DELETE FROM time_log WHERE (user_id, entry_num) IN (SELECT user_id, entry_num FROM time_log WHERE user_id = ? ORDER BY entry_num DESC LIMIT 1);", (user_id,))

    # Get the time logged by all users
    def timelog_table(self):
        res = self.cur.execute("SELECT * FROM time_log;")
        return(res.fetchall())

    # Get total minutes logged by user with given user_id
    def time_sum(self, user_id):
        # If the user has entries in the database return their total time logged, otherwise return 0
        if (self.has_entries(user_id)):
            res = self.cur.execute(f"SELECT SUM(minutes) FROM time_log WHERE user_id = ?;", (user_id,))
            return(res.fetchone()[0])
        else:
            return(0)

    # Get total minutes logged by user with given user_id within the given number of days of the current date
    def time_sum_after_date(self, user_id, days):
        today = datetime.date.today()
        startDate = today - datetime.timedelta(days=7)
        # If the user has entries in the database return their time logged within the specified period, otherwise return 0
        if (self.has_entries(user_id)):
            res = self.cur.execute(f"SELECT SUM(minutes) FROM time_log WHERE user_id = ? AND selected_date BETWEEN ? AND ?;", (user_id, startDate, today))
            return(res.fetchone()[0])
        else:
            return(0)

    # Check whether the user with given user_id has any entries in the time log table
    def has_entries(self, user_id):
        res = self.cur.execute(f"SELECT * FROM time_log WHERE user_id = ?;", (user_id,))
        if(len(res.fetchall()) == 0):
            return False
        else:
            return True