import database

def leaderboard():
    sqlc = database.SQLConnection()
    contributions = sqlc.leaderboard()
    output = "*Top 10 contributors this week*\n"
    for i in contributions:
        # Add custom display name if applicable
        name = i[0]
        if i[1] != "": name += " ("+i[1]+")"
        output += f"{name}: {int(i[2]/60)} hours and {int(i[2]%60)} minutes\n"
    return output

def tester(val):
    output = "value: "
    output += val
    return val

time_constrained_responses = {
    "tester": tester,
    "leaderboard": leaderboard
}
