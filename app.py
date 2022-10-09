import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, date
import blocks
import database

# Initialize Slack app and web client with bot token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
slackWebClient = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Get user's full name
def getName(userID):
    try:
        userInfo = slackWebClient.users_info(user=userID)
        return(userInfo["user"]["real_name"])
    except SlackApiError as e:
        print(f"Error fetching user info: {e}")

# Check if user is a Slack admin
def isAdmin(userID):
    try:
        userInfo = slackWebClient.users_info(user=userID)
        return(userInfo["user"]["is_admin"])
    except SlackApiError as e:
        print(f"Error fetching user info: {e}")


# Get time log form
@app.command("/timelog")
def timelog(ack, respond, command):
    ack()
    respond(
        blocks=blocks.logForm
    )

# Get admin user request form
@app.command("/gethours")
def getHours(ack, respond, body, command):
    ack()
    if(isAdmin(body['user_id'])):
        respond(blocks=blocks.userSelection)
    else:
        respond("You must be an admin to use this command!")

@app.action("user_submit")
def handle_some_action(ack, body, respond):
    ack()
    users = body['state']['values']['user_input']['user_added']['selected_users']
    SQLC = database.SQLConnection()
    output = ""
    for i in users:
        name = getName(i)
        if (SQLC.userExists(i)):
            userTime = SQLC.getTimeSumAfterDate(i, 7)
            output += f"{name}: {int(userTime/60)} hours and {int(userTime%60)} minutes\n"
        else:
            output += f"{name} has no logged hours\n"
    print("\n" + output)
    respond(output)

@app.action("timelog_submit")
def submitTimelogForm(ack, respond, body):
    ack()
    # print(body['state']['values']) # Use to show complete list of block elements and their values for development purposes
    userID = body['user']['id']
    # Get user-selected date, hours, and minutes from form
    selectedDate = datetime.strptime(body['state']['values']['date_input']['select_date']['selected_date'], "%Y-%m-%d").date()
    timeInput = re.findall(r'\d+', body['state']['values']['hours_input']['select_hours']['value']) # creates list containing two strings (hours and minutes)

    try:
        # A better input should be used here if possible
        minutes = int(timeInput[0])*60 + int(timeInput[1])

        print("\nNew Log Entry ⏰ ")
        print("User ID: " + userID)
        print("Date: " + str(selectedDate))
        print(f"Time logged: {timeInput[0]} hours and {timeInput[1]} minutes for date {selectedDate}.")
        
        SQLC = database.SQLConnection()
        SQLC.addTimeLogEntry(userID, selectedDate, minutes)

        respond(f"Time logged: {timeInput[0]} hours and {timeInput[1]} minutes for date {selectedDate}.")
    except Exception as e:
        print(e)
        respond("*Invalid input!* Please try again!")


# List commands (may need to rename to avoid conflict)
@app.command("/help")
def help(ack, respond, command):
    ack()
    respond()

# Print entire database to console
@app.command("/geteverything")
def repeat_text(ack, respond, command):
    ack()
    SQLC = database.SQLConnection()
    print(SQLC.getTimeLogTable())

# Handle irrelevant messages so they don't show up in logs
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

@app.action("user_added")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)


@app.action("select_date")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)

# Open a WebSocket connection with Slack
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

