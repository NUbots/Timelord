import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import blocks
import database

# Initialize Slack app and web client with bot token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def getName(userID):
    try:
        userInfo = client.users_info(
            user=userID
        )
        return(userInfo["user"]["real_name"])
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
def getHours(ack, respond, command):
    ack()
    respond(
        blocks=blocks.userSelection
    )

@app.action("user_submit")
def handle_some_action(ack, body, respond):
    ack()
    users = body['state']['values']['user_input']['user_added']['selected_users']
    SQLC = database.SQLConnection()
    output = ""
    for i in users:
        name = getName(i)
        if (SQLC.userExists(i)):
            userTime = SQLC.getTimeSum(i)
            output += f"{name}: {int(userTime/60)} hours and {userTime%60} minutes\n"
        else:
            output += f"{name} has no logged hours\n"
    respond(
        output
    )


@app.action("timelog_submit")
def submitTimelogForm(ack, respond, body):
    ack()
    # print(body['state']['values']) # Use to show complete list of block elements and their values for development purposes
    userID = body['user']['id']
    selectedDate = body['state']['values']['date_input']['select_date']['selected_date']
    timeInput = re.findall(r'\d+', body['state']['values']['hours_input']['select_hours']['value']) # creates list containing two strings (hours and minutes)

    print("\nNew Log Entry ⏰ ")
    print("User ID: " + userID)
    print("Date: " + selectedDate)
    print("Time logged: " + timeInput[0] + " hours and " + timeInput[1] + " minutes.")

    minutes = int(timeInput[0])*60 + int(timeInput[1])

    SQLC = database.SQLConnection()
    SQLC.addTimeLogEntry(userID, selectedDate, minutes)

    respond("Submitted!")

# List commands (may need to rename to avoid conflict?)
@app.command("/help")
def help(ack, respond, command):
    ack()
    respond()

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


@app.action("select_date")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)



# Open a WebSocket connection with Slack
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

