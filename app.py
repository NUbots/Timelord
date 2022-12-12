import os, re, logging, blocks, database
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from datetime import datetime, timedelta
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

    try:
        user_id = body['user']['id']

        selected_date = body['state']['values']['date_select_block']['date_select_input']['selected_date']
        time_input_text = body['state']['values']['hours_block']['hours_input']['value']
        summary = body['state']['values']['text_field_block']['text_input']['value']

        if not (select_date and time_input_text and summary):
            raise ValueError("Missing required field")
        
        time_inputs = re.findall(r'\d+', time_input_text) # List with two integers: hours and minutes

        if (len(summary) > 70):
            raise ValueError("Summary must be under 70 characters")
        if not (all(time_input.isdigit() for time_input in time_inputs) and len(time_inputs) == 2):
            raise ValueError("Time logged field must contain two numbers seperated by some characters (e.g. 3h 25m)")

    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    minutes = int(time_inputs[0])*60 + int(time_inputs[1])
    logger.info(f"New log entry of {time_inputs[0]} hours and {time_inputs[1]} minutes for {selected_date} by {user_id}")
    sqlc = database.SQLConnection()
    sqlc.insert_timelog_entry(user_id, selected_date, minutes, summary)
    respond(f"Time logged: {time_inputs[0]} hours and {time_inputs[1]} minutes for date {selected_date}.")



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
    try:
        users = body['state']['values']['user_select_block']['user_select_input']['selected_users']
        start_date = body['state']['values']['date_select_block_start']['date_select_input']['selected_date']
        end_date = body['state']['values']['date_select_block_end']['date_select_input']['selected_date']

        if not (users and start_date and end_date):
            raise ValueError("Missing required field")

    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    sqlc = database.SQLConnection()
    output = ""
    # Add the time logged by each user to the output
    for user in users:
        name = user_name(user)
        user_time = sqlc.time_sum(user, start_date, end_date)
        if (user_time > 0):
            output += f"*{name}*: {user_time//60} hours and {user_time%60} minutes\n"
        else:
            output += f"*{name}* has no logged hours\n"
    respond(output)



# Get user-selection form (choose users to see tables for their logged hours per date)
@app.command("/getentries")
def get_user_hours_form(ack, respond, body, command):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.getentries_form())
    else:
        respond("You must be an admin to use this command!")

# Form response: log tables for all users specified
@app.action("getentries_response")
def get_logged_hours(ack, body, respond, logger):
    ack()
    try:
        users = body['state']['values']['user_select_block']['user_select_input']['selected_users']
        num_entries_input_text = body['state']['values']['num_entries_block']['num_entries_input']['value']

        if not (users and num_entries_input_text):
            raise ValueError("Missing required field")

        num_entries_input = re.findall(r'\d+', num_entries_input_text)
        if len(num_entries_input) == 1 and num_entries_input[0].isdigit():
            num_entries = int(num_entries_input[0])
        else: 
            raise ValueError("Number of entries must be a single positive integer")
    
    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    sqlc = database.SQLConnection()
    output = ""
    for user in users:
        output += f"\n\n\n*{user_name(user)}*"
        entries = sqlc.given_user_entries_list(user, num_entries)
        if entries:
            for entry in entries:
                output += f"\n\n  •  {entry['selected_date']} / {(entry['minutes']//60):2} hours and {(entry['minutes']%60):2} minutes / Submitted {entry['entry_date']} / "
                output += f"_{entry['summary']}_" if entry['summary'] else "No summary given"
        else:
            output += "\n\n  •  No entries"
    respond(output)



@app.command("/dateoverview")
def get_date_overview_form(ack, respond, body):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.dateoverview_form())
    else:
        respond("You must be an admin to use this command!")

@app.action("dateoverview_response")
def get_date_overview(ack, body, respond, logger):
    ack()
    try:
        selected_date = body['state']['values']['date_select_block']['date_select_input']['selected_date']
        if not (selected_date):
            raise ValueError("Missing required field")

    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    sqlc = database.SQLConnection()
    entries = sqlc.entries_for_date_list(selected_date)
    output = f"*Overview for {selected_date}*"
    if entries:
        for entry in entries:
            name = entry['name']
            if entry['display_name'] != "": name += f" ({entry['display_name']})"
            output += f"\n\n  •  {name} / {(entry['minutes']//60):2} hours and {(entry['minutes']%60):2} minutes / "
            output += f"_{entry['summary']}_" if entry['summary'] else "No summary given"
    else:
        output += "\n\n  •  No entries"
    respond(output)



# Get a leaderboard with the top 10 contributors and their hours logged
@app.command("/leaderboard")
def leaderboard(ack, body, respond):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.leaderboard_form())
    else:
        respond("You must be an admin to use this command!")

@app.action("leaderboard_response")
def leaderboard_response(ack, body, respond, logger, command):
    ack()
    try:
        start_date = body['state']['values']['date_select_block_start']['date_select_input']['selected_date']
        end_date = body['state']['values']['date_select_block_end']['date_select_input']['selected_date']

        if not (start_date and end_date):
            raise ValueError("Both a start and end date must be specified")

    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    sqlc = database.SQLConnection()
    contributors = sqlc.leaderboard(start_date, end_date)
    
    # Convert to the australian standard date format for slack output
    au_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%y")
    au_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%y")

    if contributors:
        output = f"*All contributors between {au_start_date} and {au_end_date} ranked by hours logged*\n"
        for contributor in contributors:
            name = contributor['name']
            # Add custom display name if applicable
            if contributor['display_name'] != "": name += f" ({contributor['display_name']})"
            output += f"{name}: {contributor['totalMinutes']//60} hours and {contributor['totalMinutes']%60} minutes\n"
        respond(output)
    else:
        respond(f"No hours logged between {au_start_date} and {au_end_date}!")


################################### Commands without forms ###################################

@app.command("/help")
def help(ack, respond, body):
    ack()
    output = """
    \n*User Commands:*
    */timelog* Open a time logging form
    */deletelast* Delete your last entry
    */myentries n* Get your last n entries (defaults to 5)"""
    if(is_admin(body['user_id'])):
        output += """
    \n*Admin Commands:*
    */gethours* Select users and see their total hours logged
    */getentries* Select users and see their most recent entries
    */lastentries n* See the last n entries from all users in one list (defaults to 30)
    */leaderboard* Select a date range and rank all users by hours logged in that range
    */dateoverview* See all entries for a given date"""
    respond(output)

# Respond with a table showing the last n entries made by the user issuing the command
@app.command("/myentries") # used '/myentries n'
def user_entries(ack, respond, body, command, logger):
    ack()
    try:
        user_id = body['user_id']
        if command['text'].isdigit():
            num_entries = int(command['text'])
        elif not command['text']:
            num_entries = 10
        else:
            raise ValueError("If a number of entries is provided it must be a positive integer")

    except ValueError as e:
        respond(f"*Invalid input!* Please try again! {str(e)}.")
        logger.warning(e)
        return

    sqlc = database.SQLConnection()
    entries = sqlc.given_user_entries_list(user_id, num_entries)
    today = datetime.today()
    yearly_minutes = sqlc.time_sum(user_id, (today - timedelta(days=365)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
    weekly_minutes = sqlc.time_sum(user_id, (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

    output = f"\n*Hours logged in the last 365 days*: {yearly_minutes//60} hours and {yearly_minutes%60} minutes"
    output += f"\n*Hours logged this week:* {weekly_minutes//60} hours and {weekly_minutes%60} minutes"
    
    if entries:
        for entry in entries:
            # restricting hours and minutes to 2 characters makes the list look nicer
            output += f"\n\n  •  {entry['selected_date']} / {(entry['minutes']//60):2} hours and {(entry['minutes']%60):2} minutes / Submitted {entry['entry_date']} / "
            output += f"_{entry['summary']}_" if entry['summary'] else "No summary given"
    else:
        output += "\n\n  •  No entries"
    respond(output)

@app.command("/deletelast")
def delete_last(ack, respond, body, command):
    ack()
    sqlc = database.SQLConnection()
    sqlc.remove_last_entry(body['user_id'])
    respond("Last entry removed!")

@app.command("/lastentries")
def log_database(ack, body, respond, command, logger):
    ack()
    if(is_admin(body['user_id'])):
        try:
            if command['text'].isdigit():
                num_entries = int(command['text'])
            elif not command['text']:
                num_entries = 30
            else:
                raise ValueError("If a number of users is provided it must be a positive integer")

        except ValueError as e:
            respond(f"*Invalid input!* {str(e)}")
            logger.warning(e)
            return

        sqlc = database.SQLConnection()
        entries = sqlc.all_user_entries_list(num_entries)

        output = f"*Last {num_entries} entries from all users*"
        if entries:
            for entry in entries:
                name = entry['name']
                if entry['display_name'] != "": name += f" ({entry['display_name']})"
                output += f"\n\n  •  {name} / {entry['selected_date']} / {(entry['minutes']//60):2} hours and {(entry['minutes']%60):2} minutes / Submitted {entry['entry_date']} / "
                output += f"_{entry['summary']}_" if entry['summary'] else "No summary given"
        else:
            output += "\n\n  •  No entries"

        respond(output)
    else:
        respond("You must be an admin to use this command!")

################################### Other events to be handled ###################################

# Update user info in the database to match slack user info
@app.event("user_change")
def update_user_info(event, logger):
    sqlc = database.SQLConnection()
    sqlc.validate_user(event["user"]["id"], event["user"]["profile"]["real_name"], event["user"]["profile"]["display_name"])
    logger.info("Updated name for " + event["user"]["profile"]["real_name"])

# Add users to the database when they join the workspace
@app.event("team_join")
def add_user(event, logger):
    sqlc = database.SQLConnection()
    sqlc.validate_user(event["user"]["id"], event["user"]["profile"]["real_name"], event["user"]["profile"]["display_name"])
    logger.info("New user: " + event["user"]["profile"]["real_name"])

# Handle irrelevant messages so they don't show up in logs
@app.event("message")
def message_event(body, logger):
    logger.debug(body)

@app.action("user_select_input")
def user_added_in_slack_input(ack, body, logger):
    ack()
    logger.debug(body)

@app.action("date_select_input")
def select_date(ack, body, logger):
    ack()
    logger.debug(body)

@app.action("date_constraint_input")
def handle_some_action(ack, body, logger):
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
