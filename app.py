import os, re, logging, time, threading, schedule
import blocks, database
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

def send_instant_message(user_id, message):
    conversation = slack_web_client.conversations_open(users=user_id)
    slack_web_client.chat_postMessage(channel=conversation["channel"]["id"], text=message)

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
# This is only to catch missed changes (if the bot was offline). Usually changes should be caught in real time by the event listener.
def validate_all_users():
    web_query = slack_web_client.users_list()
    if web_query["ok"]:
        # USLACKBOT is the slack api. It doesn't have is_bot but it does have this unique user id.
        active_users = [user for user in web_query["members"] if (not user["deleted"] and not user["is_bot"] and not user["is_app_user"] and not user["id"] == "USLACKBOT")]
        sqlc = database.SQLConnection()
        for user in active_users:
            sqlc.validate_user(user["id"], user["profile"]["real_name"], user["profile"]["display_name"])
        # If users have left the workspace their logs should remain but they should be removed from the active user list
        sqlc.remove_deactivated_users([user["id"] for user in active_users])
    else:
        logging.error(f"Error retrieving user list from Slack: {web_query['error']}")

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
        time_input = body['state']['values']['hours_block']['hours_input']['value'] # String
        summary = body['state']['values']['text_field_block']['text_input']['value']

        if not (select_date and time_input and summary):
            raise ValueError("Missing required field")
        
        time_list = re.findall(r'\d+', time_input) # List with two ints

        if (len(summary) > 70):
            raise ValueError("Summary must be under 70 characters")
        if not (all(i.isdigit() for i in time_list) and len(time_list) == 2):
            raise ValueError("Time logged field must contain two numbers seperated by some characters (e.g. 3h 25m)")

    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    minutes = int(time_list[0])*60 + int(time_list[1])    # user input (hours and minutes) stored as minutes only
    logger.info(f"New log entry of {time_list[0]} hours and {time_list[1]} minutes for {selected_date} by {user_id}")
    sqlc = database.SQLConnection()
    sqlc.insert_timelog_entry(user_id, selected_date, minutes, summary)
    respond(f"Time logged: {time_list[0]} hours and {time_list[1]} minutes for date {selected_date}.")


@app.command("/gethours")
def get_user_hours_form(ack, respond, body):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.gethours_form())
    else:
        respond("You must be an admin to use this command!")

@app.action("gethours_response")
def get_logged_hours(ack, body, respond, logger):
    ack()
    try:
        users = body['state']['values']['user_select_block']['user_select_input']['selected_users']
        start_date = body['state']['values']['date_select_block_start']['date_select_input']['selected_date']
        end_date = body['state']['values']['date_select_block_end']['date_select_input']['selected_date']

        if not (users and start_date and end_date):
            raise ValueError("Missing required field")

        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    except ValueError as e:
        respond(f"*Invalid input, please try again!* {str(e)}.")
        logger.warning(e)
        return

    sqlc = database.SQLConnection()
    output = ""
    # Add the time logged by each user to the output
    for i in users:
        name = user_name(i)
        user_time = sqlc.time_sum(i, start_date, end_date)
        if (user_time > 0):
            output += f"*{name}*: {int(user_time/60)} hours and {int(user_time%60)} minutes\n"
        else:
            output += f"*{name}* has no logged hours\n"
    respond(output)


@app.command("/getentries")
def get_user_hours_form(ack, respond, body, command):
    ack()
    if(is_admin(body['user_id'])):
        respond(blocks=blocks.getentries_form())
    else:
        respond("You must be an admin to use this command!")

@app.action("getentries_response")
def get_logged_hours(ack, body, respond, logger):
    ack()
    try:
        users = body['state']['values']['user_select_block']['user_select_input']['selected_users']
        num_entries_input = body['state']['values']['num_entries_block']['num_entries_input']['value']

        if not (users and num_entries_input):
            raise ValueError("Missing required field")

        try: num_entries = int(re.findall(r'\d+', num_entries_input)[0])
        except: raise ValueError("Number of entries must be an integer")
    
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
            for i in entries:
                output += f"\n\n  •  {i[0]} / {int(i[1]/60):2} hours and {i[1]%60:2} minutes / Submitted {i[2]} / "
                output += f"_{i[3]}_" if i[3] else "No summary given"
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
        for i in entries:
            name = i[0]
            if i[1] != "": name += " ("+i[1]+")"
            output += f"\n\n  •  {name} / {int(i[2]/60):2} hours and {i[2]%60:2} minutes / "
            output += f"_{i[3]}_" if i[3] else "No summary given"
    else:
        output += "\n\n  •  No entries"
    respond(output)


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
    contributions = sqlc.leaderboard(start_date, end_date)
    
    # Doing this means we are converting from date object to string, to date object, and then back to string
    # I still think this is the best approach because it is clearer and easier to read than a string manipulation
    au_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%y")
    au_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%y")

    if contributions:
        output = f"*All contributors between {au_start_date} and {au_end_date} ranked by hours logged*\n"
        for i in contributions:
            # Add custom display name if applicable
            name = i[0]
            if i[1] != "": name += " ("+i[1]+")"
            output += f"{name}: {int(i[2]/60)} hours and {int(i[2]%60)} minutes\n"
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
    yearly_minutes = sqlc.time_sum(user_id, today - timedelta(days=365), today)
    weekly_minutes = sqlc.time_sum(user_id, today - timedelta(days=today.weekday()), today)

    output = f"\n*Hours logged in the last 365 days*: {int(yearly_minutes/60)} hours and {yearly_minutes%60} minutes"
    output += f"\n*Hours logged this week:* {int(weekly_minutes/60)} hours and {weekly_minutes%60} minutes"
    
    if entries:
        for i in entries:
            output += f"\n\n  •  {i[0]} / {int(i[1]/60):2} hours and {i[1]%60:2} minutes / Submitted {i[2]} / "
            output += f"_{i[3]}_" if i[3] else "No summary given"
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
            for i in entries:
                name = i[0]
                if i[1] != "": name += " ("+i[1]+")"
                output += f"\n\n  •  {name} / {i[2]} / {int(i[3]/60):2} hours and {i[3]%60:2} minutes / Submitted {i[4]} / "
                output += f"_{i[5]}_" if i[5] else "No summary given"
        else:
            output += "\n\n  •  No entries"

        respond(output)
    else:
        respond("You must be an admin to use this command!")

@app.command("/togglereminders")
def toggle_reminders(ack, respond, body):
    ack()
    sqlc = database.SQLConnection()
    if(sqlc.toggle_reminders(body['user_id'])):
        respond("Reminders enabled!")
    else:
        respond("Reminders disabled!")

################################### Other events to be handled ###################################

# Update users real name and custom display name in database when a user changes this info through slack
@app.event("user_change")
def update_user_info(event, logger):
    sqlc = database.SQLConnection()
    user = event["user"]
    if user["deleted"]:
        sqlc.remove_user(user["id"])
        logger.info(f"Removed user {user['profile']['real_name']} from active users list")
    else:
        sqlc.validate_user(user["id"], user["profile"]["real_name"], user["profile"]["display_name"])
        logger.info(f"Updated name for {user['profile']['real_name']}")

# Update users real name and custom display name in database when a new user joins the slack workspace
@app.event("team_join")
def add_user(event, logger):
    sqlc = database.SQLConnection()
    user = event["user"]
    sqlc.validate_user(user["id"], user["profile"]["real_name"], user["profile"]["display_name"])
    logger.info("New user: " + user["profile"]["real_name"])

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

################################### Startup and related functions ###################################

def notify_inactive_users():
    sqlc = database.SQLConnection()
    users = sqlc.inactive_users()
    if users:
        for user in users:
            logging.info(f"Notifying user {user['name']} of inactivity (last entry {user['last_entry_date']})")
            send_instant_message(user['id'], "You have not logged any hours in the last 7 days. *Please remember to log your hours!* If you don't want to receive these reminders, you can do /disablereminders")
    # Maybe this is an unnecessary extra loop but it's simpler than the alternatives and I think it's probably fine for this project.
    sqlc.update_reminded_users([user['id'] for user in users])

def schedule_reminders():
    schedule.every().day.at("12:00").do(notify_inactive_users)
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_app(app, token):
    SocketModeHandler(app, token).start()

if __name__ == "__main__":
    database.create_log_table()
    database.create_user_table()
    validate_all_users()

    reminders_thread = threading.Thread(target=schedule_reminders, args=())
    app_thread = threading.Thread(target=start_app, args=(app, os.environ["SLACK_APP_TOKEN"]))

    reminders_thread.start() 
    app_thread.start()

    reminders_thread.join()
    app_thread.join()