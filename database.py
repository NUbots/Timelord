import sqlite3
import datetime
from tabulate import tabulate

db_file = "timelord.db"

def create_log_table():
    # Create time log table
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS time_log(
                        entry_num INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        entry_date date NOT NULL,
                        selected_date date NOT NULL,
                        minutes INTEGER NOT NULL,
                        project TEXT,

                        PRIMARY KEY (entry_num, user_id));""")
    con.close()

def create_user_name_table():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS user_names(
                        name TEXT NOT NULL,
                        user_id TEXT NOT NULL,

                        PRIMARY KEY (entry_num, user_id));""")

def validate_user(user_id, name):
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("INSERT INTO user_names (user_id, name) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET name=?;", (user_id, name, name))

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect(db_file)
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
        
        today = datetime.date.today().strftime('%Y-%m-%d')

        res = self.cur.execute("SELECT MAX(entry_num) FROM time_log WHERE user_id = ?;", (user_id,))
        entry_num = res.fetchone()[0]
        if (entry_num == None): 
            entry_num = 1
        else:
            entry_num += 1

        self.cur.execute("INSERT INTO time_log VALUES (?,?,?,?,?, NULL);", (entry_num, user_id, today, selected_date, minutes ))

    def remove_last_entry(self, user_id):
        self.cur.execute("DELETE FROM time_log WHERE (user_id, entry_num) IN (SELECT user_id, entry_num FROM time_log WHERE user_id = ? ORDER BY entry_num DESC LIMIT 1);", (user_id,))

    # Get all entries by all users
    def timelog_table(self):
        res = self.cur.execute("SELECT * FROM time_log LIMIT 30;")
        header = ["Entry Number", "User ID", "Date Submitted", "Date of Log", "Minutes", "Project"]
        return(tabulate(res.fetchall(), header, tablefmt="simple_grid"))

    # Get the last n entries by user as a table
    def last_entries_table(self, user_id, num_entries):
        res = self.cur.execute("SELECT entry_num, entry_date, selected_date, minutes FROM time_log WHERE user_id = ? ORDER BY entry_num DESC LIMIT ?;", (user_id, num_entries))
        header = ["Entry Number", "Date Submitted", "Date of Log", "Minutes"]
        return(tabulate(res.fetchall(), header, tablefmt="simple_grid"))

    # Get total minutes logged by user with given user_id
    def time_sum(self, user_id):
        # If the user has entries in the database return their total time logged, otherwise return 0
        res = self.cur.execute(f"SELECT SUM(minutes) FROM time_log WHERE user_id = ?;", (user_id,))
        minutes = res.fetchone()[0]
        if (minutes != None):
            return(minutes)
        else:
            return(0)

    # Get total minutes logged by user with given user_id within the given number of days of the current date
    def time_sum_after_date(self, user_id, days):
        today = datetime.date.today().strftime('%Y-%m-%d')
        startDate = today - datetime.timedelta(days)
        # If the user has entries in the database return their time logged within the specified period, otherwise return 0
        minutes = res.fetchone()[0]
        if (minutes != None):
            return(minutes)
        else:
            return(0)
