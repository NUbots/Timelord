import sqlite3
# Create / connect to database
con = sqlite3.connect("timelord.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS timeLog(userID string, date, minutes)")
cur.execute("CREATE TABLE IF NOT EXISTS users(userID, username)")
con.close()

class SQLConnection:
    def __init__(self):
        # Open SQL connection
        self.con = sqlite3.connect("timelord.db")
        self.cur = self.con.cursor()

    def __del__(self):
        # Close SQL connection (saving changes to file)
        self.con.close()

    def addTimeLogEntry(self, userID, date, minutes):
        self.cur.execute(f"INSERT INTO timeLog VALUES ('{userID}', '{date}', {minutes})")
        self.con.commit()

    def getTimeLogTable(self):
        res = self.cur.execute("SELECT * FROM timeLog")
        print(res.fetchall())

    def getUsers(self):
        res = self.cur.execute("SELECT * FROM users")
        print(res.fetchall())

    def getTimeSum(self, userID):
        res = self.cur.execute(f"SELECT SUM(minutes) FROM timeLog WHERE userID = '{userID}'")
        return(res.fetchone()[0])

    def userExists(self, userID):
        res = self.cur.execute(f"SELECT * FROM users WHERE userID = '{userID}';")
        if(len(res.fetchall()) == 0):
            return False
        else:
            return True

    def registerUsername(self, userID, username):
        self.cur.execute(f"INSERT INTO users VALUES ('{userID}', '{username}')")
        self.con.commit()
    
    def updateUsername(self, userID, username):
        self.cur.execute(f"UPDATE users SET username = '{username}' WHERE userID = '{userID}'")
        self.con.commit()

    def getUsername(self, userID):
        res = self.cur.execute(f"SELECT username FROM users WHERE userID = '{userID}'")
        return(res.fetchone()[0])