# Slack block kit - https://api.slack.com/block-kit

from datetime import datetime, timedelta

# # Get current date for time logging form
# def currentDate():
#     return datetime.now()

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

date_constraint_block = {
    "block_id": "date_constraint_block",
    "type": "input",
    "element": {
        "type": "static_select",
        "initial_option": {
            "text": {
                "type": "plain_text",
                "text": "This year",
            },
            "value": "This year"
        },
        "placeholder": {
            "type": "plain_text",
            "text": "Select an item",
        },
        "options": [
            {
                "text": {
                    "type": "plain_text",
                    "text": "This year",
                },
                "value": "This year"
            },
            {
                "text": {
                    "type": "plain_text",
                    "text": "Today",
                },
                "value": "today"
            },
            {
                "text": {
                    "type": "plain_text",
                    "text": "This week",
                },
                "value": "this week"
            },
            {
                "text": {
                    "type": "plain_text",
                    "text": "This month",
                },
                "value": "this month"
            }
        ],
        "action_id": "time_constraint_input"
    },
    "label": {
        "type": "plain_text",
        "text": "Selection range",
    }
}

def date_select_block():
    return {
        # Date picker
        "type": "input",
        "block_id": "date_select_block",
        "element": {
            "type": "datepicker",
            # YYYY-MM-DD format needs to be used here because SQL doesn't have a date data type so these are stored as strings
            # and in this format lexicographical order is identical to chronological order.
            "initial_date": datetime.now().strftime("%Y-%m-%d"),
            "placeholder": {
                "type": "plain_text",
                "text": "Select a date",
            },
            "action_id": "date_select_input"
        },
        "label": {
            "type": "plain_text",
            "text": "Date to log",
        }
    }

def submit_button_block(form_action):
    return {
        # Submit button
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Confirm and submit"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Submit",
            },
            "value": "placeholder",
            "action_id": form_action
        }
    }

# Time logging form
def timelog_form():
    return [
        date_select_block(),
        hours_input_block,
        submit_button_block("timelog_response")
    ]

# User selection form for hour sum
def gethours_form():
    return [
        user_select_block,
        submit_button_block("gethours_response")
    ]

def getusertables_form():
    return [
        user_select_block,
        num_entries_block,
        date_constraint_block(),
        submit_button_block("getusertables_response")
    ]

def dateoverview_form():
    return [
        date_select_block,
        submit_button_block("dateoverview_response")
    ]

def leaderboard_form():
    return [
        date_select_block(),
        submit_button_block("leaderboard_response")
    ]
