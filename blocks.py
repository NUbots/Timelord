# Slack block kit - https://api.slack.com/block-kit
# Each slack block used is stored here as a single dictionary object. These are then combined into a list of blocks for each message.

#  Clicking the submit button for a form will send a block_action payload with the user-input content from the form stored in a dictionary.
# All inputs are stored as strings, integers, and booleans. Dates are stored as strings in the YYYY-MM-DD format.
from datetime import date, timedelta

num_entries_block = {
    # Number of entries
    "type": "input",
    "block_id": "num_entries_block",
    "element": { 
        "type": "plain_text_input",
        "action_id": "num_entries_input",
        "initial_value": "20"
    },
    "label": {
        "type": "plain_text",
        "text": "Maximum number of entries to return for each user",
    }
}

divider = {
    "type": "divider"
}

num_users_block = {
    # Number of entries
    "type": "input",
    "block_id": "num_users_block",
    "element": { 
        "type": "plain_text_input",
        "action_id": "num_users_input",
        "initial_value": "10"
    },
    "label": {
        "type": "plain_text",
        "text": "Number of users to return",
    }
}


hours_input_block = {
    # Hours input
    "type": "input",
    "block_id": "hours_block",
    "element": {
        "type": "plain_text_input",
        "action_id": "hours_input"
    },
    "label": {
        "type": "plain_text",
        "text": "Time logged (e.g. 2h, 25m)",
    }
}

user_select_block = {
    "type": "input",
    "block_id": "user_select_block",
    "element": {
        "type": "multi_users_select",
        "placeholder": {
            "type": "plain_text",
            "text": "Select users",
        },
        "action_id": "user_select_input"
    },
    "label": {
        "type": "plain_text",
        "text": "Select users",
    }
}

def text_field_block(label, max_length):
    return {
        "type": "input",
        "block_id": "text_field_block",
        "element": {
            "type": "plain_text_input",
            "action_id": "text_input",
            "max_length": max_length
        },
        "label": {
            "type": "plain_text",
            "text": label
        }
    }

# Getter functions are used when the block has dynamic content
def date_select_block(label, initial_date, id_modifier = None):
    block_id = "date_select_block_" + id_modifier if id_modifier else "date_select_block"
    return {
        "type": "input",
        "block_id": block_id,
        "element": {
            "type": "datepicker",
            "initial_date": initial_date.strftime("%Y-%m-%d"),
            "placeholder": {
                "type": "plain_text",
                "text": "Select a date",
            },
            "action_id": "date_select_input"
        },
        "label": {
            "type": "plain_text",
            "text": label,
        }
    }

def submit_button_block(form_action):
    return {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Confirm",
                },
                "value": "confirm",
                "action_id": form_action
            }
        ]
    }

# Time logging form
def timelog_form():
    return [
        date_select_block("Date to log", date.today()),
        hours_input_block,
        text_field_block("Summary of work done", 70),
        submit_button_block("timelog_response")
    ]

# User selection form for hour sum
def gethours_form():
    return [
        user_select_block,
        date_select_block("Start date", date.today() - timedelta(days=365), "start"),
        date_select_block("End date", date.today(), "end"),
        submit_button_block("gethours_response")
    ]

def getentries_form():
    return [
        user_select_block,
        num_entries_block,
        submit_button_block("getentries_response")
    ]

def getusertables_form():
    return [
        user_select_block,
        num_entries_block,
        submit_button_block("getusertables_response")
    ]

def dateoverview_form():
    return [
        date_select_block("Date to view", date.today()),
        submit_button_block("dateoverview_response")
    ]

def leaderboard_form():
    return [
        date_select_block("Start date", date.today() - timedelta(days=365), "start"),
        date_select_block("End date", date.today(), "end"),
        submit_button_block("leaderboard_response")
    ]
