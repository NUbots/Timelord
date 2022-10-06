import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import blocks
import database

# Initialize app with bot token and socket mode handler
# Bot token is stored as a python virtual environment variable
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Get time log form
@app.command("/timelog")
def timelog(ack, respond, command):
    ack()
    respond(
        blocks=blocks.logForm
    )

# Get admin user request form
@app.command("/gethours")
def getHours(ack, respond, command):
    ack()
    respond(
        blocks=blocks.userSelection
    )

# @app.action("user_select")
# def submitTimelogForm(ack, respond, body):
#     ack()
#     # print(body['state']['values']) # Use to show complete list of block elements and their values for development purposes
#     print(body['state']['values'])

@app.action("user_submit")
def handle_some_action(ack, body, respond):
    ack()
    users = body['state']['values']['user_input']['user_added']['selected_users']
    print(users)
    output = ""
    SQLC = database.SQLConnection()
    for i in users:
        if (SQLC.userExists(i)):
            userTime = SQLC.getTimeSum(i)
            output += f"{i}: {int(userTime/60)} hours and {userTime%60} minutes\n"
        else:
            output += f"{i} has no logged hours"
    respond(
        output
    )


@app.action("timelog_submit")
def submitTimelogForm(ack, respond, body):
    ack()
    # print(body['state']['values']) # Use to show complete list of block elements and their values for development purposes
    username = body['user']['username']
    userID = body['user']['id']
    selectedDate = body['state']['values']['date_input']['select_date']['selected_date']
    timeInput = re.findall(r'\d+', body['state']['values']['hours_input']['select_hours']['value']) # creates list containing two strings (hours and minutes)

    print("\nNew Log Entry ⏰ ")
    print("Username: " + username)
    print("User ID: " + userID)
    print("Date: " + selectedDate)
    print("Time logged: " + timeInput[0] + " hours and " + timeInput[1] + " minutes.")

    minutes = int(timeInput[0])*60 + int(timeInput[1])

    SQLC = database.SQLConnection()
    # Add time log entry and check user name and ID in database
    SQLC.addTimeLogEntry(userID, selectedDate, minutes)
    checkUsernameEntry(SQLC, userID, username)

    respond("Submitted!")

# List commands (may need to rename to avoid conflict?)
@app.command("/help")
def help(ack, respond, command):
    ack()
    respond()

# Respond with the total time logged by a user
# @app.command("/totallogged")
# def repeat_text(ack, respond, command):
#     ack()
#     SQLC = database.SQLConnection()
#     username = command['text']
#     userDetails = SQLC.getTimeSum(username)
#     print(userDetails)
#     respond(
#         "Username: " + userDetails[0] + "\n"
#         # "User ID: " + userDetails[0] + "\n"
#         "Total minutes logged: " + str(userDetails[1]) + "\n"
#     )

@app.command("/geteverything")
def repeat_text(ack, respond, command):
    ack()
    SQLC = database.SQLConnection()
    SQLC.getTimeLogTable()
    SQLC.getUsers()

# Handle irrelevant messages so they don't show up in logs
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

@app.action("user_added")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)


# Open a WebSocket connection with Slack
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

