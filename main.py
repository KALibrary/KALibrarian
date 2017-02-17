import os
import time
import requests
import json
from slackclient import SlackClient
import sqlite3


BOT_NAME = 'librarian'

# Instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# Get the bot's ID
BOT_ID = os.environ.get("BOT_ID")

VALID_COMMANDS = {'search'}
VALID_COMMAND_HELP_TEXT = [{
    "fallback": "To search for books, in #ka-library, type in `@{} search <insert keywords here>`".format(BOT_NAME),
    "color": "#36a64f",
    "pretext": "Valid Command(s):",
    "title": "Search for Books in the KA Library",
    "text": "`@{} search <insert keywords here>` - returns books where title or author matches your keywords".format(BOT_NAME),
}]

# Limit the number of results shown in Slack
MAX_NUM_SLACK_ATTACHMENTS = 10

AT_BOT = "<@" + BOT_ID + ">"

# LIBRARYTHING API SEARCH URL
LIBRARYTHING_SEARCH_API_URL = "https://www.librarything.com/api_getdata.php?userid=KA-library&key=2744260721&max=1000&responseType=json&showCollections=1"

def get_bot_id():
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # Get all the users in the team
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print "Bot ID for {} is {}".format(user['name'], user.get('id'))
                return user.get('id')
    else:
        print "Did not find bot user with the name {}".format(BOT_NAME)


def get_any_slack_id(slack_handle):
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # Get all the users in the team
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == slack_handle:
                print "Slack ID for {} is {}".format(user['name'], user.get('id'))
                return user.get('id')
    else:
        print "Did not find user with the name {}".format(slack_handle)


def handle_command(command, channel, user):
    """Receives commands directed at the bot and determines
    if the commands are valid. If so, acts on the command.
    If not, returns help text.
    """
    keywords = None
    attachments = []
    slack_command = None
    try:
        slack_command = command.split(" ")[0]
        keywords = " ".join(command.split(" ")[1:])
        # If slack_command is invalid, remind user of valid command(s)
        if slack_command not in VALID_COMMANDS or keywords is None:
            print "Invalid command {} and keywords is None".format(slack_command)
            attachments = VALID_COMMAND_HELP_TEXT
        else:
            # DM the user to let them know the bot has started the search
            slack_client.api_call("chat.postMessage", channel=user,
                                  text="Searching for {}".format(keywords),
                                  as_user=True)

            # Search books by keyword
            search_results = search_library_db(keywords)
            # If there are no search results, let the user know right away.
            if not search_results:
                slack_client.api_call("chat.postMessage", channel=user,
                                      text="No matching books found... Try again.",
                                      as_user=True)
            else:
                # If there are search results, format each result as a
                # Slack message attachment and append it to the
                # list of attachments
                attachments = []
                for idx, result in enumerate(search_results):
                    book_id, title, author, _, lang, cover_url, avail, collection = result
                    curr_attachment = {
                        "fallback": title,
                        "color": "#36a64f",
                        "pretext": "Search Results:",
                        "title": "{} by {}".format(title, author),
                        "text": "Location: {}".format(collection),
                        "thumb_url": cover_url,
                    }
                    # If this is not the first result,
                    # no need for the "Search Results:" pretext
                    if idx > 0:
                        del curr_attachment["pretext"]
                    attachments.append(curr_attachment)
    except Exception as e:
        print "Error Msg: {} with command {} and keywords {}".format(str(e), slack_command, keywords)
        attachments = VALID_COMMAND_HELP_TEXT

    # Limit the number of returned results to 10 for now
    # (to manage the UX in Slack)
    final_attachments = attachments[:MAX_NUM_SLACK_ATTACHMENTS]
    slack_client.api_call("chat.postMessage", channel=user,
                          attachments=final_attachments, as_user=True)


def parse_slack_output(slack_rtm_output):
    """Parse Slack RTM API events firehouse to return None
    unless a message is directed at the bot based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                channel = output['channel']
                command_str = output['text'].split(AT_BOT)[1].strip().lower()
                user_slack_id = output['user']
                return command_str, channel, user_slack_id

    return None, None, None


def get_ka_library_books():
    """Get KA Library books from LibraryThing API.
    """
    r = requests.get(LIBRARYTHING_SEARCH_API_URL)
    all_books_dict = r.json()['books']
    return all_books_dict


def search_library_db(search_keywords):
    """Search local database for all books where each keyword is at least
    a substring of the title or author.
    """
    conn = sqlite3.connect('library_database/library.db')
    c = conn.cursor()

    # Set up the tuple of keywords to be repeated twice
    # (so that the SQL query can match against title or author)
    keywords_as_list = search_keywords.split(" ")
    double_keywords_as_list = [keyword for keyword in keywords_as_list for _ in (0, 1)]
    t = tuple(['%' + keyword + '%' for keyword in double_keywords_as_list])

    # Write the SQL query to return books where each keyword
    # is at least a substring of either title or author
    sql_query = "SELECT * FROM BOOKS WHERE "
    for idx, keyword in enumerate(keywords_as_list):
        if idx < (len(keywords_as_list) - 1):
            sql_query += "(title like ? OR author_fl like ?) AND "
        else:
            sql_query += "(title like ? OR author_fl like ?)"

    c.execute(sql_query, t)

    return c.fetchall()


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1  # 1-second delay between reading from firehose
    if slack_client.rtm_connect():
        print "Librarian connected and running!"
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print "Connection failed. Invalid Slack token or bot ID?"
