import requests
from requests.auth import HTTPBasicAuth
import json
import argparse
import re
import urllib.parse
import os
import traceback
from flask import abort, Flask, jsonify, request
from zappa.asynchronous import task
from datetime import datetime
from notion_page import *

# URL Data
jira_host = os.environ.get('JIRA_HOST')
jira_url = f"https://{jira_host}/rest/agile/1.0/"
greenhopper_url = f"https://{jira_host}/rest/greenhopper/1.0/"
jira_query_url = f"https://{jira_host}/issues/?jql="
jira_query_jql = "issueKey in ("

# Auth Data
JIRA_USER = os.environ.get('JIRA_USER')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN')
auth = HTTPBasicAuth(JIRA_USER, JIRA_TOKEN)

# Header Data
headers = { 'Accept': 'application/json' }

# Google Form Data
google_form_response_url = 'https://docs.google.com/forms/d/e/1FAIpQLSdF__V1ZMfl6H5q3xIQhSkeZMeCNkOHUdTBFdYA1HBavH31hA/formResponse'
google_view_form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSdF__V1ZMfl6H5q3xIQhSkeZMeCNkOHUdTBFdYA1HBavH31hA/viewform'

google_entry_translations = {
"metrics": {
    "items": {
        "bugs_completed": 'entry.448087930',
        "committed": 'entry.2095001800',
        "completed": 'entry.1399119358',
        "not_completed": 'entry.128659456',
        "planned_completed": 'entry.954885633',
        "removed": 'entry.1137054034',
        "stories_completed": 'entry.1980453543',
        "unplanned_bugs_completed": 'entry.1252702382',
        "unplanned_completed": 'entry.485777497',
        "unplanned_stories_completed": 'entry.370334542'
    },
    "points": {
        "committed": 'entry.1427603868',
        "completed": 'entry.1486076673',
        "feature_completed": 'entry.254612996',
        "not_completed": 'entry.611444996',
        "optimization_completed": 'entry.2092919144',
        "planned_completed": 'entry.493624591',
        "removed": 'entry.976792423',
        "unplanned_completed": 'entry.1333444050'
    }
},
#TODO: We're assuming that the project name IS the team name, which isn't always the case
"project_name": "entry.1082637073",
"sprint_number": "entry.1975251686"
}

def getSprintReportURL(project_key, board_id, sprint_id):

    return f"https://{jira_host}/secure/RapidBoard.jspa?rapidView={board_id}&projectKey={project_key}&view=reporting&chart=sprintRetrospective&sprint={sprint_id}"

def generateGoogleFormURL(sprint_data):
    url = f"{google_view_form_url}?"

    for entry in ["project_name", "sprint_number"]:
        sprint_data[entry] = re.sub(r'[^\w ]', '', sprint_data[entry])
        sprint_data[entry] = urllib.parse.quote(sprint_data[entry])
        url += f"{google_entry_translations[entry]}={sprint_data[entry]}&"

    for metric_type in sprint_data['metrics'].keys():
        if metric_type is "meta":
            continue
        for item in sprint_data['metrics'][metric_type].keys():
            url += f"{google_entry_translations['metrics'][metric_type][item]}={sprint_data['metrics'][metric_type][item]}&"

    return url

def pprint(json_obj):
    print(json.dumps(json_obj, sort_keys=True, indent=4, separators=(",", ": ")))

def makeRequest(verb, url, params=None):
    response = requests.request(verb, url, headers=headers, auth=auth, params=params)
    if response.status_code == 200:
        return(json.loads(response.text))
    else:
        return(False)
def getBoardById(board_id):
    url = f"{jira_url}board/{board_id}"

    return makeRequest('GET', url)

def getBoards(name=None):
    url = f"{jira_url}board?"

    if name != None:
        url = f"{url}projectKeyOrId={name}"

    return makeRequest('GET', url)

def getCurrentSprintFromBoard(boardID):
    url = f"{jira_url}board/{boardID}/sprint?state=active"

    return makeRequest('GET', url)

def getSprintFromID(sprintID):
    url = f"{jira_url}sprint/{sprintID}"

    return makeRequest('GET', url)

def getSprintReport(board_id, sprint_id):
    url = f"{greenhopper_url}rapid/charts/sprintreport?rapidViewId={board_id}&sprintId={sprint_id}"

    return makeRequest('GET', url)

def getSprintMetrics(sprint_report):
    points = {
        "committed": 0,
        "completed": 0,
        "planned_completed": 0,
        "unplanned_completed": 0,
        "feature_completed": 0,
        "optimization_completed": 0,
        "not_completed": 0,
        "removed": 0
    }

    items = {
        "committed": 0,
        "completed": 0,
        "planned_completed": 0,
        "unplanned_completed": 0,
        "stories_completed": 0,
        "unplanned_stories_completed": 0,
        "bugs_completed": 0,
        "unplanned_bugs_completed": 0,
        "not_completed": 0,
        "removed": 0
    }

    issue_keys = {
        "committed": [],
        "completed": [],
        "incomplete": [],
        "removed": []
    }

    feature_work = ["Story", "Design", "Spike"]
    optimization = ["Optimization"]
    bug = ["Bug"]
    ignore = ["Task", "Epic"]

    # Completed Work
    for completed in sprint_report["contents"]["completedIssues"]:

        issue_keys["completed"].append(completed["key"])

        # Short-circuit for things we don't track
        if completed["typeName"] in ignore:
            continue

        try:
            issue_points_original = int(completed["estimateStatistic"]["statFieldValue"]["value"])
        except:
            issue_points_original = 0

        try:
            issue_points = int(completed["currentEstimateStatistic"]["statFieldValue"]["value"])
        except:
            issue_points = 0

        points["completed"] += issue_points
        items["completed"] += 1

        unplanned = False
        if completed["key"] in sprint_report["contents"]["issueKeysAddedDuringSprint"].keys():
            unplanned = True
            points["unplanned_completed"] += issue_points_original
            items["unplanned_completed"] += 1
        else:
            issue_keys["committed"].append(completed["key"])
            points["committed"] += issue_points_original
            items["committed"] += 1
            points["planned_completed"] += issue_points
            items["planned_completed"] += 1
            if issue_points_original < issue_points:
                points["unplanned_completed"] += issue_points-issue_points_original

        # Story
        if completed["typeName"] == "Story":
            items["stories_completed"] += 1
            if unplanned:
                items["unplanned_stories_completed"] += 1

        # Story / Design / Spike (Feature Work)
        if completed["typeName"] in feature_work:
            points["feature_completed"] += issue_points

        # Optimization
        if completed["typeName"] in optimization:
            points["optimization_completed"] += issue_points

        # Bugs
        if completed["typeName"] in bug:
            items["bugs_completed"] += 1
            if unplanned:
                items["unplanned_bugs_completed"] += 1


    # Incomplete Work
    for incomplete in sprint_report["contents"]["issuesNotCompletedInCurrentSprint"]:

        issue_keys["incomplete"].append(incomplete["key"])

        # Short-circuit for things we don't track
        if incomplete["typeName"] in ignore:
            continue

        try:
            issue_points = int(incomplete["currentEstimateStatistic"]["statFieldValue"]["value"])
        except:
            issue_points = 0

        points["not_completed"] += issue_points
        items["not_completed"] += 1

        if incomplete["key"] not in sprint_report["contents"]["issueKeysAddedDuringSprint"].keys():
            issue_keys["committed"].append(incomplete["key"])
            points["committed"] += issue_points
            items["committed"] += 1

    # Removed Work
    for removed in sprint_report["contents"]["puntedIssues"]:

        issue_keys["removed"].append(removed["key"])

        # Short-circuit for things we don't track
        if removed["typeName"] in ignore:
            continue

        try:
            issue_points = int(removed["currentEstimateStatistic"]["statFieldValue"]["value"])
        except:
            issue_points = 0

        if removed["key"] not in sprint_report["contents"]["issueKeysAddedDuringSprint"].keys():
            points["committed"] += issue_points
            items["committed"] += 1
            issue_keys["committed"].append(removed["key"])

        points["removed"] += issue_points
        items["removed"] += 1

    return {
        "points" : points,
        "items" : items,
    }, issue_keys
def getVelocityReport(board_id):
    url = f"{greenhopper_url}rapid/charts/velocity?rapidViewId={board_id}"

    return makeRequest('GET', url)

def getAvgVelocity(board_id, sprintID):
    velocityReport = getVelocityReport(board_id)
    velocityEntries = velocityReport['velocityStatEntries']

    threeSprintVelocityTotal = 0
    sprintCounter = 0
    for velocityEntryKey in sorted(velocityEntries.keys(), reverse=True):

        if sprintCounter > 2:
            continue
        elif sprintCounter > 0:
            sprintCounter = sprintCounter + 1
            threeSprintVelocityTotal = threeSprintVelocityTotal+velocityEntries[velocityEntryKey]['completed']['value']
        elif str(velocityEntryKey) == str(sprintID):
            threeSprintVelocityTotal = velocityEntries[velocityEntryKey]['completed']['value']
            sprintCounter = sprintCounter + 1
    if sprintCounter == 0:
         sprintCounter=1
    return threeSprintVelocityTotal/sprintCounter

def getURLS(issue_keys):

    urls = {
        "completed_issues": jira_query_url +  urllib.parse.quote(jira_query_jql + ",".join(issue_keys["completed"]) + ")"),
        "incomplete_issues": jira_query_url+ urllib.parse.quote(jira_query_jql + ",".join(issue_keys["incomplete"]) + ")"),
        "removed_issues": jira_query_url+ urllib.parse.quote(jira_query_jql + ",".join(issue_keys["removed"]) + ")"),
        "committed_issues": jira_query_url+ urllib.parse.quote(jira_query_jql + ",".join(issue_keys["committed"]) + ")")
    }

    return urls

def generateSearchAndReplaceDict(sprint_data):
    dict = {}

    dict['[team-name]'] = sprint_data['project_name']
    dict['[sprint-number]'] = sprint_data['sprint_number']
    start_date = datetime.strptime(sprint_data['sprint_start'].split('T')[0], '%Y-%m-%d')
    dict['[sprint-start]'] = datetime.strftime(start_date, '%m/%d/%Y')
    end_date = datetime.strptime(sprint_data['sprint_end'].split('T')[0], '%Y-%m-%d')
    dict['[sprint-end]'] = datetime.strftime(end_date, '%m/%d/%Y')
    dict['[sprint-goal]'] = "\n".join(sprint_data['sprint_goals'])
    dict['[points-committed]'] = str(sprint_data['metrics']['points']['committed'])
    dict['[points-completed]'] = str(sprint_data['metrics']['points']['completed'])

    dict['[items-committed]'] = str(sprint_data['metrics']['items']['committed'])
    dict['[items-completed]'] = str(sprint_data['metrics']['items']['completed'])
    dict['[bugs-completed]'] = str(sprint_data['metrics']['items']['bugs_completed'])

    dict['[predictability]'] = str(sprint_data['metrics']['meta']['predictability']) + "%"
    dict['[predictability-commitments]'] = str(sprint_data['metrics']['meta']['predictability_of_commitments']) + "%"
    dict['[average-velocity]'] = str(sprint_data['metrics']['meta']['average_velocity'])

    dict['[original-committed-link]'] =f"[{sprint_data['metrics']['items']['committed']} Originally Committed Issues]( {sprint_data['urls']['committed_issues']})"

    dict['[completed-issues-link]'] = f"[{sprint_data['metrics']['items']['completed']} Completed Issues]( {sprint_data['urls']['completed_issues']})"

    dict['[items-not-completed-link]'] = f"[{sprint_data['metrics']['items']['not_completed']} Incomplete Issues]( {sprint_data['urls']['incomplete_issues']})"

    dict['[items-removed-link]'] = f"[{sprint_data['metrics']['items']['removed']} Removed Issues]( {sprint_data['urls']['removed_issues']})"

    return dict

def collectSprintData(projectKey, sprintID=False, notionPageUrl=False):
    sprint_data = {}
    board_id = None
    boards = getBoards(projectKey)
    if boards == False or boards["total"] == 0:
        raise Exception ("I couldn't find that project's board")
        exit()

    if sprintID:
        sprint_data['sprint_id'] = sprintID
        current_sprint = getSprintFromID(sprint_data['sprint_id'])

        if not current_sprint:
            raise Exception("I couldn't find that sprint id")
            exit()

        board_id = current_sprint['originBoardId']
        board = getBoardById(board_id)
        sprint_data['board_name'] = board['name']
        sprint_data['project_name'] = board["location"]["projectName"]

    else:
        # This is a pretty awful way to handle the fact that projects can have multiple boards, with no specific 'default'
        #TODO: If using a Slack Bot, we should have a store for projects and their preferred boards. If one isn't registered, we should prompt for a board id and save that.
        for board in boards['values']:
            try:
                current_sprint = getCurrentSprintFromBoard(board['id'])["values"][0]
                board_id = board['id']
                sprint_data['board_name'] = board['name']
                sprint_data['project_name'] = board["location"]["projectName"]
            except:
                continue

        if not board_id:
            raise Exception("I couldn't a board with an active sprint for that project")
            exit()

    sprint_data['sprint_id'] = current_sprint['id']
    sprint_data['sprint_start'] = current_sprint['startDate']
    sprint_data['sprint_end'] = current_sprint['endDate']
    sprint_data['sprint_report_url'] = getSprintReportURL(projectKey, board_id, sprint_data['sprint_id'])

    try:
        sprint_data['sprint_number'] = re.search("(S|Sprint )(?P<number>\d+)", current_sprint["name"]).group('number')
    except:
        raise Exception("I couldn't determine the sprint number from that sprint's name")

    sprint_data['sprint_goals'] = current_sprint['goal'].split("\n")

    sprint_report = getSprintReport(board_id, sprint_data['sprint_id'])

    if not sprint_report:
        raise Exception("I couldn't find that sprint")
        exit()

    sprint_data['metrics'], sprint_data['issue_keys'] = getSprintMetrics(sprint_report)

    meta = {}
    meta['average_velocity'] = int(getAvgVelocity(board_id, sprint_data['sprint_id']))
    meta['predictability'] = int(sprint_data['metrics']['points']['completed']/sprint_data['metrics']['points']['committed']*100)
    meta['predictability_of_commitments'] = int(sprint_data['metrics']['points']['planned_completed']/sprint_data['metrics']['points']['committed']*100)

    sprint_data['metrics']['meta'] = meta

    sprint_data['urls'] = getURLS(sprint_data['issue_keys'])

    return sprint_data

def updateNotionPage(data, url):
    dict = generateSearchAndReplaceDict(data)
    pprint(dict)
    print(f"URL: {url}")
    page = NotionPage(url)
    page.searchAndReplace(dict)

def get_sprint_report_slack_blocks(data):
    blocks = []
    divider_block = {
			"type": "divider"
		}

    gif_block = {
			"type": "image",
			"title": {
				"type": "plain_text",
				"text": "Order Up!"
			},
			"image_url": "https://media.giphy.com/media/l1JojmmBMELYFKJc4/giphy.gif",
			"alt_text": "Order Up!"
		}
    blocks.append(gif_block)
    blocks.append(divider_block)

    goals_string = '\n'.join(data['sprint_goals'])
    report_details_block = {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*Project Name*: {data['project_name']}\n*Sprint {data['sprint_number']}*\n{goals_string}"
			}
		}
    blocks.append(report_details_block)

    blocks.append(divider_block)

    sprint_metrics = []
    for type in data['metrics'].keys():
        type_block = {
    			"type": "section",
    			"text": {
    				"type": "mrkdwn",
    				"text": f"*{type}*"
    			}
    		}
        blocks.append(type_block)

        for metric in data['metrics'][type].keys():
            sprint_metrics.append({
					"type": "plain_text",
					"text": f"{metric}"
				})
            sprint_metrics.append({
					"type": "plain_text",
					"text": f"{data['metrics'][type][metric]}"
				})
            if len(sprint_metrics) > 8:
                blocks.append({
            			"type": "section",
            			"fields": sprint_metrics
                })
                sprint_metrics = []

        if len(sprint_metrics) > 0:
            sprint_metrics_block = {
        			"type": "section",
        			"fields": sprint_metrics
            }
            blocks.append(sprint_metrics_block)
            sprint_metrics = []

    blocks.append(divider_block)
    blocks.append({
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": f"<{generateGoogleFormURL(data)}|Google Form URL>"
		}
	})

    return {
        "blocks": blocks
        }

app = Flask(__name__)

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid

@task
def sprint_report_task(response_url, text):
    args = text.split()
    data = {}

    try:
        sprint_data = collectSprintData(*args)
        data = get_sprint_report_slack_blocks(sprint_data)
        data['response_type'] = 'in_channel'

        if len(args) > 2:
            requests.post(response_url, json=data)

            data = {
                'response_type': 'in_channel',
                'text': "Updating that Notion page... please give me up to 5 minutes. I'll let you know when it's done.",
            }
            requests.post(response_url, json=data)

            updateNotionPage(sprint_data, args[2])

            data = {
                'response_type': 'in_channel',
                'text': "All done!",
            }
    except BaseException as e:
        print(e)
        traceback.print_exc()
        data = {
            'response_type': 'in_channel',
            'text': str(e),
        }

    requests.post(response_url, json=data)

@app.route('/sprint-report', methods=['POST'])
def sprint_report():
    if not is_request_valid(request):
        abort(400)

    request_text = request.form['text']

    if 'help' in request_text:
        response_text = (
            'Use this generate sprint report information\n' +
            'Call it with just a team name (i.e., `/sprint-report YOSHI`) to use the currently open sprint for that board.\n' +
            'Call it with a team name and a sprint ID (e.g., `/sprint-report YOSHI 1234 `) to use a specific sprint.\n' +
            'Call it with a team name, a sprint ID and a Notion URL to update that page with sprint data `/sprint-report YOSHI 1234 https://www.notion.so/mediaos/Sprint-22-Review-3edba77b45d2492592286df310b0c819#5217e0db2a914026a5e433ed0901`.\n' 
        )

        return jsonify(
            response_type='in_channel',
            text=response_text,
        )
    else:
        sprint_report_task(request.form['response_url'], request_text)

        return jsonify(
            response_type='in_channel',
            text="Let me think...",
        )

@app.route('/bot-event', methods=['POST'])
def bot_handler():

    request.data = request.get_data()
    pprint(request.form)
    if request.form['type'] == 'url_verification':
        return request

    if not is_request_valid(request):
        abort(400)
