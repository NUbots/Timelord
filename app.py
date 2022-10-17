import os, re, logging, blocks, database
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path(".env")
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Initialize Slack app and web client with bot token
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
slack_web_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Set up logging for info messages
logging.basicConfig(level=logging.INFO)

# Get user's full name from slack web client
def full_name(user_id):
    user_info = slack_web_client.users_info(user=user_id)
    return(user_info["user"]["real_name"])

# Check if user is a Slack admin
def is_admin(user_id):
    user_info = slack_web_client.users_info(user=user_id)
    return(user_info["user"]["is_admin"])

# Use the slack code block format to force monospace font (without this the table rows and lines will be missaligned)
def slack_table(title, message):
    return(f"*{title}*\n```{message}```")

# Get time log form
@app.command("/timelog")
def time_log(ack, respond, command):
    ack()
    respond(blocks=blocks.log_form)

# Get admin user request form
@app.command("/gethours")
def get_user_hours_form(ack, respond, body, command):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.user_hours_selection)
    else:
        respond("You must be an admin to use this command!")

@app.command("/deletelast")
def delete_last(ack, respond, body, command):
    ack()
    sqlc = database.SQLConnection()
    sqlc.remove_last_entry(body['user_id'])
    respond("Last entry removed!")

@app.action("get_user_hours")
def get_logged_hours(ack, body, respond, logger):
    ack()
    # Get list of users submitted for query by Slack admin
    users = body['state']['values']['user_input']['user_added']['selected_users']
    # Open an SQL connection
    sqlc = database.SQLConnection()
    output = ""
    # Add the time logged by each user in the last week to the output
    for i in users:
        name = full_name(i)
        user_time = sqlc.time_sum(i)
        if (user_time > 0):
            output += f"{name}: {int(user_time/60)} hours and {int(user_time%60)} minutes\n"
        else:
            output += f"{name} has no logged hours\n"
    # Send output to Slack chat and console
    logger.info("\n" + output)
    respond(output)

# Get time log tables for selected users form
@app.command("/getusertables")
def get_user_hours_form(ack, respond, body, command):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.user_table_selection)
    else:
        respond("You must be an admin to use this command!")

@app.action("get_user_table")
def get_logged_hours(ack, body, respond, logger):
    ack()
    users = body['state']['values']['user_input']['user_added']['selected_users']
    try:
        num_entries = re.findall(r'\d+', body['state']['values']['num_entries']['select_num_entries']['value'])[0]
    except:
        respond('Invalid input! Please try again.')
    
    sqlc = database.SQLConnection()
    output = ""
    for user in users:
        name = full_name(user)
        table = sqlc.last_entries_table(user, num_entries)
        output += slack_table(f"{num_entries} most recent entries by {name}", table) + "\n"

    respond(output)

@app.action("timelog_submit")
def submit_timelog_form(ack, respond, body, logger):
    ack()
    user_id = body['user']['id']
    # Get user-selected date, hours, and minutes from form
    selected_date = datetime.strptime(body['state']['values']['date_input']['select_date']['selected_date'], "%Y-%m-%d").date()
    time_input = re.findall(r'\d+', body['state']['values']['hours_input']['select_hours']['value']) # creates list containing two strings (hours and minutes)

    try:
        minutes = int(time_input[0])*60 + int(time_input[1])    # user input (hours and minutes) stored as minutes only

        logger.info(f"New log entry of {time_input[0]} hours and {time_input[1]} minutes for {selected_date} by {user_id}")
        
        # Open an SQL connection and add entry to database containing user input
        sqlc = database.SQLConnection()
        sqlc.insert_timelog_entry(user_id, selected_date, minutes)

        respond(f"Time logged: {time_input[0]} hours and {time_input[1]} minutes for date {selected_date}.")

    except Exception as e:
        # Show the user an error if they input anything other than two integers seperated by some character / characters
        logger.exception("Invalid user input, failed to create time log entry")
        respond("*Invalid input!* Please try again!")


# List commands (may need to rename to avoid conflict)
@app.command("/help")
def help(ack, respond, body, command):
    ack()
    output = """
    \n*User Commands:*
    */timelog* Opens a time logging form
    */deletelast* Delete your last entry
    */myentries n* Get a table with your last n entries"""
    if(is_admin(body['user_id'])):
        output += """
    \n*Admin Commands:*
    */gethours* Select users and get their total hours logged
    */getusertables* Select users to see their last few entries
    */allusertable* Responds with the last 30 entries from all users"""
    respond(output)

@app.command("/myentries")
def user_entries(ack, respond, body, command, logger):
    ack()
    try:
        user_id = body['user_id']
        name = full_name(user_id)
        num_entries = int(command['text'])
    except:
        logger.exception("Invalid user input, failed to create time log entry")
        respond("*Invalid input!* Please try again! You can generate a table with your last n entries with /myentries n")

    sqlc = database.SQLConnection()
    table = sqlc.last_entries_table(user_id, num_entries)

    respond(slack_table(f"{num_entries} most recent entries by {name}", table))

# Print entire database to console
@app.command("/allusertable")
def log_database(ack, body, respond, command, logger):
    ack()
    if(is_admin(body['user_id'])):
        sqlc = database.SQLConnection()
        table = sqlc.timelog_table()

        logger.info("\n" + table)
        respond(slack_table("Last 30 entries from all users", table))
    else:
        respond("You must be an admin to use this command!")


# Handle irrelevant messages so they don't show up in logs
@app.event("message")
def message_event(body, logger):
    logger.debug(body)

@app.action("user_added")
def user_added_in_slack_input(ack, body, logger):
    ack()
    logger.debug(body)

@app.action("select_date")
def select_date(ack, body, logger):
    ack()
    logger.debug(body)

if __name__ == "__main__":
    # Create time log table
    database.createLogTable()
    # Open a WebSocket connection with Slack
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()