import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import blocks
import database

# Initialize app with bot token and socket mode handler
# Bot token is stored as a python virtual environment variable
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Register the number of hours worked today
@app.command("/timelog")
def repeat_text(ack, respond, command):
    ack()
    respond(
        blocks=blocks.logForm
    )

@app.action("timelog_submit")
def submit_hours(ack, respond, body):
    ack()
    print(body['state']['values']) # Use to show complete list of block elements and their values for development purposes
    username = body['user']['username']
    selectedDate = body['state']['values']['date_input']['select_date']['selected_date']
    timeInput = re.findall(r'\d+', body['state']['values']['hours_input']['select_hours']['value'])

    print("Username: " + username)
    print("Date: " + selectedDate)
    print("Time logged: " + timeInput[0] + " hours and " + timeInput[1] + " minutes.")

    minutes = int(timeInput[0])*60 + int(timeInput[1])

    SQLC = database.SQLConnection()
    SQLC.addTimeLogEntry(username, selectedDate, minutes)
    respond("Submitted!")

# List commands (may need to rename to avoid conflict?)
@app.command("/help")
def repeat_text(ack, respond, command):
    ack()
    # maybe this should be a modal popup?
    respond()

# Respond with the total time logged by a user
@app.command("/totallogged")
def repeat_text(ack, respond, command):
    ack()
    SQLC = database.SQLConnection()
    username = command['text']
    userDetails = SQLC.getTimeSum(username)
    print(userDetails)
    respond(
        "Username: " + userDetails[0] + "\n"
        # "User ID: " + userDetails[0] + "\n"
        "Total minutes logged: " + str(userDetails[1]) + "\n"
    )

@app.command("/geteverything")
def repeat_text(ack, respond, command):
    ack()
    SQLC = database.SQLConnection()
    SQLC.getTimeLogTable()

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

# Open a WebSocket connection with Slack
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

