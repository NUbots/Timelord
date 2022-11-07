import sqlite3
import datetime
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
                        project TEXT,

                        PRIMARY KEY (entry_num, user_id));""")
    con.close()

def create_user_table():
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS user_names (
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        display_name TEXT,

                        PRIMARY KEY (user_id));""")


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
                            ON CONFLICT(user_id) DO UPDATE SET name=?, display_name=?;""", (user_id, name, display_name, name, display_name))

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

    def insert_timelog_entry(self, user_id, selected_date, minutes):
        # Dates are stored in plain text - SQLite doesn't have a specific date type. This still works and is sortable as long as
        # dates are stored in the YYYY-MM-DD format (highest to lowest weight)

        # SQLite3 documentation says this format with placeholder question marks and a tuple of values should be used rather than formatted strings to prevent sql injection attacks
        # This probably isn't necessary here but there's no good reason not to

        today = datetime.date.today().strftime('%Y-%m-%d')

        # Get and increment the entry number
        res = self.cur.execute("""SELECT MAX(entry_num)
                                  FROM time_log
                                  WHERE user_id = ?;""", (user_id,))
        entry_num = res.fetchone()[0]
        if (entry_num == None):
            entry_num = 1
        else:
            entry_num += 1
        
        self.cur.execute("INSERT INTO time_log VALUES (?,?,?,?,?, NULL);", (entry_num, user_id, today, selected_date, minutes ))

    def remove_last_entry(self, user_id):
        self.cur.execute("""DELETE FROM time_log
                            WHERE (user_id, entry_num) IN (
                                SELECT user_id, entry_num FROM time_log
                                WHERE user_id = ? 
                                ORDER BY entry_num DESC LIMIT 1);""", (user_id,))

    # Get all entries by all users
    def timelog_table(self):
        res = self.cur.execute("""SELECT u.name, tl.entry_num, tl.entry_date, tl.selected_date, tl.minutes
                                  FROM time_log tl
                                  INNER JOIN user_names u
                                  ON tl.user_id=u.user_id
                                  LIMIT 30;""")
        header = ["Name", "Entry Number", "Date Submitted", "Date of Log", "Minutes"]
        return(tabulate(res.fetchall(), header, tablefmt="simple_grid"))

    # Get the last n entries by user as a table
    def last_entries_table(self, user_id, num_entries, start_date = ""):
        print(start_date)
        res = self.cur.execute("""SELECT entry_num, entry_date, selected_date, minutes
                                FROM time_log 
                                WHERE user_id = ?
                                AND selected_date > ?
                                ORDER BY entry_num DESC
                                LIMIT ?;""", (user_id, start_date, num_entries))
        header = ["Entry Number", "Date Submitted", "Date of Log", "Minutes"]
        return(tabulate(res.fetchall(), header, tablefmt="simple_grid"))

    # Get total minutes logged by user with given user_id
    def time_sum(self, user_id):
        # If the user has entries in the database return their total time logged, otherwise return 0
        res = self.cur.execute("""SELECT SUM(minutes)
                                   FROM time_log
                                   WHERE user_id = ?;""", (user_id,))
        minutes = res.fetchone()[0]
        if (minutes != None):
            return(minutes)
        else:
            return(0)

    # Get total minutes logged by all users
    def all_time_sums(self):
        # If the user has entries in the database return their total time logged
        res = self.cur.execute("""SELECT u.name, u.display_name, SUM(tl.minutes) AS time_sum
                                  FROM time_log tl
                                  INNER JOIN user_names u
                                  ON u.user_id=tl.user_id
                                  GROUP BY u.name, u.display_name
                                  ORDER BY time_sum;""")
        return(res.fetchall())

    # Get the top 10 contributors
    def leaderboard(self, num_users = None, date_constraint = None):
        query = """SELECT u.name, u.display_name, sum(tl.minutes) AS totalMinutes
                 FROM user_names u
                 INNER JOIN time_log tl
                 ON u.user_id=tl.user_id """
        params = []
        if date_constraint:
            query += "WHERE selected_date >= ? AND selected_date <= ? "
            params.append(date_constraint.start_date)
            params.append(date_constraint.end_date)
        # query += """ """ # Close the WHERE clause
        query += """GROUP BY u.name, u.display_name
                    ORDER BY totalMinutes DESC """
        if num_users:
            query += "LIMIT ?"
            params.append(num_users)
        print(query)
        print(params)
        res = self.cur.execute(query, params)
        return(res.fetchall())

    def entries_for_date_table(self, selected_date):
        # Get all entries by all users7
        res = self.cur.execute("""SELECT u.name, tl.minutes
                                FROM time_log tl
                                INNER JOIN user_names u
                                ON tl.user_id=u.user_id
                                WHERE tl.selected_date=?;""", (selected_date,))
        header = ["Name", "Minutes"]
        print(selected_date)
        return(tabulate(res.fetchall(), header, tablefmt="simple_grid"))
