# Slack block kit - https://api.slack.com/block-kit

from datetime import datetime, timedelta

# Get current date for time logging form
def currentDate():
    return datetime.now()

# Time logging form blocks
def timelog_form():
    output = [
        {
            # Horizontal line
            "type": "divider"
        },
        {
            # Date picker
            "type": "input",
            "block_id": "date_select_block",
            "element": {
                "type": "datepicker",
                # YYYY-MM-DD format needs to be used here because SQL doesn't have a date data type so these are stored as strings
                # and in this format lexicographical order is identical to chronological order.
                "initial_date": currentDate().strftime("%Y-%m-%d"),
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
        },
        {
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
                "action_id": "timelog_response"
            }
        }
    ]
    return output

# User selection form for hour sum
def gethours_form():
    output = [
        {
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
                "text": "Select users to view their total time logged",
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Confirm Selection",
                    },
                    "action_id": "gethours_response"
                }
            ]
        }
    ]
    return output

# User selection form for table
def getusertables_form():
    output = [
        {
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
                "text": "Select users to their last n entries as a table",
            }
        },
        {
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
        },
        # Add a date constraint selector
        date_constraint(),
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Confirm Selection",
                    },
                    "action_id": "getusertables_response"
                },
            ]
        }
    ]
    return output

# This is a seperate function because it's a large block used in most of the commands and in some cases is the only 
def date_constraint():
    # Let the user choose a date constraint - the time_constraint_response event listener will run the function at
    # response_endpoint with the given date constraint
    today = datetime.today()
    output = {
        "block_id": "date_constraint_block",
        "type": "input",
        "element": {
            "type": "static_select",
            # Default to all time
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
                    # "value": today
                    "value": "today"
                },
                {
                    "text": {
                        "type": "plain_text",
                        "text": "This week",
                    },
                    # Move back n days where n is the weekday number (so we reach the start of the week)
                    # Monday is 0 and Sunday is 6 here
                    # "value": today - timedelta(days = today.weekday())
                    "value": "this week"
                },
                {
                    "text": {
                        "type": "plain_text",
                        "text": "This month",
                    },
                    "value": "this month"
                    # Replace the day part of the date with 1 (2022-11-23 becomes 2022-11-01)
                    # "value": today.replace(day=1)
                }
            ],
            "action_id": "time_constraint_input"
        },
        "label": {
            "type": "plain_text",
            "text": "Selection range",
        }
    }

    print("got it")
    return output

# def time_constraint_form(response_endpoint):
#     # Let the user choose a date constraint - the time_constraint_response event listener will run the function at
#     # response_endpoint with the given date constraint
#     today = date.today()
#     output = [
#         {
#             "type": "input",
#             "element": {
#                 "type": "static_select",
#                 "placeholder": {
#                     "type": "plain_text",
#                     "text": "Select an item",
#                     "emoji": true
#                 },
#                 "options": [
#                     {
#                         "text": {
#                             "type": "plain_text",
#                             "text": "Today",
#                             "emoji": true
#                         },
#                         "value": today
#                     },
#                     {
#                         "text": {
#                             "type": "plain_text",
#                             "text": "This week",
#                             "emoji": true
#                         },
#                         # Move back n days where n is the weekday number (so we reach the start of the week)
#                         # Monday is 0 and Sunday is 6 here
#                         "value": today - datetime.timedelta(days = today.weekday())
#                     },
#                     {
#                         "text": {
#                             "type": "plain_text",
#                             "text": "This month",
#                             "emoji": true
#                         },
#                         # Replace the day part of the date with 1 (2022-11-23 becomes 2022-11-01)
#                         "value": today.replace(day=1)
#                     },
#                     {
#                         "text": {
#                             "type": "plain_text",
#                             "text": "All time",
#                             "emoji": true
#                         },
#                         "value": "All time"
#                     }
#                 ],
#                 "value": response_endpoint,
#                 "action_id": "time_constraint_response"
#             },
#             "label": {
#                 "type": "plain_text",
#                 "text": "Selection range",
#                 "emoji": true
#             }
#         }
#     ]
