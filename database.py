import sqlite3
from datetime import date, timedelta
from tabulate import tabulate

db_file = "timelord.db"

def create_log_table():
    # Create time log table
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS time_log (
                        entry_num INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        entry_date date NOT NULL,
                        selected_date date NOT NULL,
                        minutes INTEGER NOT NULL,
                        summary TEXT,

                        PRIMARY KEY (entry_num, user_id)) """)
    con.close()

def create_user_table():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS user_names (
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        display_name TEXT,

                        PRIMARY KEY (user_id)) """)

# Dates are stored in plain text (SQLite doesn't have a specific date type). This still works and is sortable as long as
# dates are stored in the YYYY-MM-DD format (highest to lowest weight)

# SQLite3 documentation says placeholder question marks and a tuple of values should be used rather than formatted strings to prevent sql injection attacks
# Ot's probably not important in this project but there's no reason not to do it this way

# All public methods in this class assume date is being given as a date object, not a string. This means multiple conversions are needed sometimes but it
# keeps things consistent and makes the whole program easier to maintain.

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect(db_file)
        self.cur = self.con.cursor()

    def __del__(self):
        # Close SQL connection (saving changes to file)
        self.con.commit()
        self.con.close()

    # Validate user info from slack client against internal user entry
    def validate_user(self, user_id, name, display_name):
        self.cur.execute("""INSERT INTO user_names (user_id, name, display_name)
                            VALUES (?, ?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET name=?, display_name=? """, (user_id, name, display_name, name, display_name))

    # Get user's full name and custom display name from database
    def user_name(self, user_id):
        res = self.cur.execute("""SELECT name, display_name
                                  FROM user_names
                                  WHERE user_id = ?""", (user_id,))
        # user is a tuple containing the users real name and a custom display name if applicable (otherwise an empty string)
        user = res.fetchone()
        name = user[0]
        # Add custom display name if applicable
        if user[1] != "": name += " ("+user[1]+")"
        return(name)

    def insert_timelog_entry(self, user_id, selected_date, minutes, summary):
        today = date.today().strftime('%Y-%m-%d')

        # Get and increment the entry number
        res = self.cur.execute("""SELECT MAX(entry_num)
                                  FROM time_log
                                  WHERE user_id = ? """, (user_id,))
        entry_num = res.fetchone()[0]
        entry_num = 1 if not entry_num else entry_num + 1
        
        self.cur.execute("INSERT INTO time_log VALUES (?,?,?,?,?,?)", (entry_num, user_id, today, selected_date, minutes, summary))

    def remove_last_entry(self, user_id):
        self.cur.execute("""DELETE FROM time_log
                            WHERE (user_id, entry_num) IN (
                                SELECT user_id, entry_num FROM time_log
                                WHERE user_id = ? 
                                ORDER BY entry_num DESC LIMIT 1) """, (user_id,))

    # Get last entries by all users
    def all_user_entries_list(self, num_entries):
        res = self.cur.execute("""SELECT u.name, u.display_name, tl.selected_date, tl.minutes, tl.entry_date, tl.summary
                                  FROM time_log tl
                                  INNER JOIN user_names u
                                  ON tl.user_id=u.user_id
                                  LIMIT ? """, (num_entries,))
        return(res.fetchall())

    # Get the last n entries by user
    def given_user_entries_list(self, user_id, num_entries = 10):
        res = self.cur.execute("""SELECT selected_date, minutes, entry_date, summary
                                FROM time_log 
                                WHERE user_id = ?
                                ORDER BY entry_num DESC
                                LIMIT ? """, (user_id, num_entries))
        return(res.fetchall())

    # Get total minutes logged by user with given user_id
    def time_sum(self, user_id, start_date = None, end_date = None):
        # If the user has entries in the database return their total time logged, otherwise return 0
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        res = self.cur.execute("""SELECT SUM(minutes)
                                  FROM time_log
                                  WHERE user_id = ?
                                  AND selected_date >= ? 
                                  AND selected_date <= ? """, (user_id, start_date, end_date))
        minutes = res.fetchone()[0]
        return minutes if minutes else 0

    # Get the top 10 contributors
    def leaderboard(self, start_date = None, end_date = None):
        res = self.cur.execute("""SELECT u.name, u.display_name, sum(tl.minutes) AS totalMinutes
                                  FROM user_names u
                                  INNER JOIN time_log tl
                                  ON u.user_id=tl.user_id
                                  WHERE selected_date >= ? 
                                  AND selected_date <= ?
                                  GROUP BY u.name, u.display_name
                                  ORDER BY totalMinutes DESC """, (start_date, end_date))
        return(res.fetchall())

    def entries_for_date_list(self, selected_date):
        # Get all entries by all users
        res = self.cur.execute("""SELECT u.name, u.display_name, tl.minutes, tl.summary
                                FROM time_log tl
                                INNER JOIN user_names u
                                ON tl.user_id=u.user_id
                                WHERE tl.selected_date=? """, (selected_date,))
        return(res.fetchall())

    def inactive_users(self):
        last_week = date.today() - timedelta(days=7)
        # Since this is an inner join, users who have never logged hours won'be be included
        res = self.cur.execute("""SELECT u.user_id
                                  FROM user_names u
                                  INNER JOIN time_log tl
                                  ON u.user_id=tl.user_id
                                  WHERE ? > (SELECT MAX(selected_date)
                                             FROM time_log)""", (last_week,))