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

# Use the slack code block format to force monospace font (without this the table rows and lines will be missaligned)
def slack_table(title, message):
    return(f"*{title}*\n```{message}```")


################################### User validation ###################################

# Get user's full name and custom display name (if applicable) from database
def user_name(user_id):
    sqlc = database.SQLConnection()
    return(sqlc.user_name(user_id))

# Check if user is a Slack admin
def is_admin(user_id):
    user_info = slack_web_client.users_info(user=user_id)
    return(user_info["user"]["is_admin"])

# Check all usernames and custom display names in the database against info retrieved from slack web client
def validate_all_users():
    user_list = slack_web_client.users_list()
    sqlc = database.SQLConnection()
    for user in user_list["members"]:
        sqlc.validate_user(user["id"], user["profile"]["real_name"], user["profile"]["display_name"])

################################### Commands with forms ###################################

# Get time log form
@app.command("/timelog")
def time_log(ack, respond, command):
    ack()
    respond(blocks=blocks.timelog_form())

# Form response: confirmation of hours logged
@app.action("timelog_response")
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

# Get user-selection form (choose users to see their total hours logged)
@app.command("/gethours")
def get_user_hours_form(ack, respond, body, command):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.gethours_form())
    else:
        respond("You must be an admin to use this command!")

# Form response: total hours logged for each user chosen
@app.action("gethours_response")
def get_logged_hours(ack, body, respond, logger):
    ack()
    # Get list of users submitted for query by Slack admin
    users = body['state']['values']['user_input']['user_added']['selected_users']
    # Open an SQL connection
    sqlc = database.SQLConnection()
    output = ""
    # Add the time logged by each user to the output
    for i in users:
        name = user_name(i)
        user_time = sqlc.time_sum(i)
        if (user_time > 0):
            output += f"*{name}*: {int(user_time/60)} hours and {int(user_time%60)} minutes\n"
        else:
            output += f"*{name}* has no logged hours\n"
    # Send output to Slack chat and console
    logger.info("\n" + output)
    respond(output)

# Get user-selection form (choose users to see tables for their logged hours per date)
@app.command("/getusertables")
def get_user_hours_form(ack, respond, body, command):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.getusertables_form())
    else:
        respond("You must be an admin to use this command!")

# Form response: log tables for all users specified
@app.action("getusertables_response")
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
        name = user_name(user)
        table = sqlc.last_entries_table(user, num_entries)
        output += slack_table(f"{num_entries} most recent entries by {name}", table) + "\n"
    respond(output)

################################### Commands without forms ###################################

@app.command("/help")
def help(ack, respond, body, command):
    ack()
    output = """
    \n*User Commands:*
    */timelog* Opens a time logging form
    */deletelast* Delete your last entry
    */myentries n* Get a table with your last n entries (defaults to 5)"""
    if(is_admin(body['user_id'])):
        output += """
    \n*Admin Commands:*
    */gethours* Select users and get their total hours logged
    */allusersums* Get the total hours logged by all users
    */getusertables* Select users to see their last few entries
    */allusertable* Responds with the last 30 entries from all users
    */leaderboard n* Responds with the top n contributors and their total time logged (defaults to 10)"""
    respond(output)

# Respond with a table showing the last n entries made by the user issuing the command
@app.command("/myentries") # used '/myentries n'
def user_entries(ack, respond, body, command, logger):
    ack()
    try:
        user_id = body['user_id']
        name = user_name(user_id)
        num_entries = int(command['text']) if command['text'] != "" else 5 # Defaults to 5 entries
    except:
        logger.exception("Invalid user input, failed to create time log entry")
        respond("*Invalid input!* Please try again! You can generate a table with your last n entries with `/myentries n`. If you leave n blank a default value of 5 will be used.")

    sqlc = database.SQLConnection()
    table = sqlc.last_entries_table(user_id, num_entries)

    respond(slack_table(f"{num_entries} most recent entries by {name}", table))

# Delete the last entry made by the user issuing the command
@app.command("/deletelast")
def delete_last(ack, respond, body, command):
    ack()
    sqlc = database.SQLConnection()
    sqlc.remove_last_entry(body['user_id'])
    respond("Last entry removed!")

# Respond with the total time logged by all users
@app.command("/allusersums")
def get_logged_hours(ack, body, respond, logger):
    ack()
    if(is_admin(body['user_id'])):
        sqlc = database.SQLConnection()
        user_sum = sqlc.all_time_sums()
        output = ""
        # Add the time logged by each user to the output
        for user in user_sum:
            # Add a custom display name if the user has one set
            if user[1] != "": display_name = " ("+user[1]+")"
            output += f"*{user[0]}*{display_name}: {int(user[2]/60)} hours and {int(user[2]%60)} minutes\n"
        # Send output to Slack chat and console
        logger.info("\n" + output)
        respond(output)
    else:
        respond("You must be an admin to use this command!")

# Respond with last 30 hours entered by all users
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

# Get a leaderboard with the top 10 contributors and their hours logged
@app.command("/leaderboard")
def leaderboard(ack, body, respond):
    ack()
    try:
        user_id = body['user_id']
        num_users = int(command['text']) if command['text'] != "" else 10 # Defaults to 5 entries
    except:
        logger.exception("Invalid user input, failed to fetch leaderboard")
        respond("*Invalid input!* Please try again! You can get a leaderboard with n users with `/leaderboard n`. If you leave n blank a default value of 10 will be used.")

    if(is_admin(body['user_id'])):
        sqlc = database.SQLConnection()
        contributions = sqlc.leaderboard()
        output = "*Top 10 contributors*\n"
        for i in contributions:
            # Add custom display name if applicable
            name = i[0]
            if i[1] != "": name += " ("+i[1]+")"
            output += f"{name}: {int(i[2]/60)} hours and {int(i[2]%60)} minutes\n"
        respond(output)
    else:
        respond("You must be an admin to use this command!")

################################### Other events to be handled ###################################

# Update users real name and custom display name in database when a user changes this info through slack
@app.event("user_change")
def update_user_info(event, logger):
    sqlc = database.SQLConnection()
    sqlc.validate_user(event["user"]["id"], event["user"]["profile"]["real_name"], event["user"]["profile"]["display_name"])
    logger.info("Updated name for " + event["user"]["profile"]["real_name"])

# Update users real name and custom display name in database when a new user joins the slack workspace
@app.event("team_join")
def add_user(event, logger):
    sqlc = database.SQLConnection()
    sqlc.validate_user(event["user"]["id"], event["user"]["profile"]["real_name"], event["user"]["profile"]["display_name"])
    logger.info("New user: " + event["user"]["profile"]["real_name"])

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
    # Create tables
    database.create_log_table()
    database.create_user_table()
    # Check all users in workspace against users in database
    validate_all_users()
    # Open a WebSocket connection with Slack
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
