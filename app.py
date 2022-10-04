import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import blocks

# Initialize app with bot token and socket mode handler
# Bot token is stored as a python virtual environment variable
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Register the number of hours worked today
@app.command("/timelog")
def repeat_text(ack, respond, command):
    # Acknowledge command request
    ack()
    respond(
        blocks=blocks.logForm
    )

@app.action("timelog_submit")
def submit_hours(ack, respond, body):
    ack()
    # print(body['state']['values']) # Use to show complete list of block elements and their values for testing purposes
    username = body['user']['username']
    selected_date = body['state']['values']['date_input']['select_date']['selected_date']
    time_logged = body['state']['values']['hours_input']['select_hours']['value']
    print("Username: " + username)
    print("Date: " + selected_date)
    print("Time logged: " + time_logged)
    respond("Submitted!")

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

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

# Open a WebSocket connection with Slack
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

