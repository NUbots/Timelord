import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from datetime import datetime

# Get current date for time logging form
def currentDate():
    return datetime.now()

# Time logging form blocks
logForm = [
    {
        # Horizontal line
        "type": "divider"
    },
    {
        # Date picker
        "type": "input",
        "element": {
            "type": "datepicker",
            # American format, YYYY:MM:DD
            "initial_date": currentDate().strftime("%Y-%m-%d"),
            "placeholder": {
                "type": "plain_text",
                "text": "Select a date",
            },
            "action_id": "datepicker-action"
        },
        "label": {
            "type": "plain_text",
            "text": "Date to log",
        }
    },
    {
        # Hours input
        "type": "input",
        "element": {
            "type": "plain_text_input",
            "action_id": "plain_text_input-action"
        },
        "label": {
            "type": "plain_text",
            "text": "Time logged (e.g. 2h, 25m)",
        }
    },
    {
        # Submit button
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Click to submit and log hours"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Submit",
            },
            "value": "placeholder",
            "action_id": "timelog_submit"
        }
    }
]

# Initialize app with bot token and socket mode handler
# Bot token is stored as a python virtual environment variable
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Register the number of hours worked today
@app.command("/timelog")
def repeat_text(ack, respond, command):
    # Acknowledge command request
    ack()
    respond(
        blocks=logForm
    )

# List commands (may need to rename to avoid conflict?)
@app.command("/help")
def repeat_text(ack, respond, command):
    # Acknowledge command request
    ack()
    # maybe this should be a modal popup?
    respond()

# Echo user text (for testing / checking if the bot is still working)
@app.command("/echo")
def repeat_text(ack, respond, command):
    # Acknowledge command request
    ack()
    respond(f"{command['text']}")

# Open a WebSocket connection with Slack
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

