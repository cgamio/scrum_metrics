import requests
from requests.auth import HTTPBasicAuth
import json
import netrc
import argparse
import re
import urllib.parse

# URL Data
jira_host = 'thetower.atlassian.net'
jira_url = f"https://{jira_host}/rest/agile/1.0/"
greenhopper_url = f"https://{jira_host}/rest/greenhopper/1.0/"

# Auth Data
netrc = netrc.netrc()
authTokens = netrc.authenticators(jira_host)
auth = HTTPBasicAuth(authTokens[0], authTokens[2])

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

def generateGoogleFormURL(sprint_data):
    url = f"{google_view_form_url}?"

    for entry in ["project_name", "sprint_number"]:
        sprint_data[entry] = re.sub(r'[^\w ]', '', sprint_data[entry])
        sprint_data[entry] = urllib.parse.quote(sprint_data[entry])
        url += f"{google_entry_translations[entry]}={sprint_data[entry]}&"

    for metric_type in sprint_data['metrics'].keys():
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

    feature_work = ["Story", "Design", "Spike"]
    optimization = ["Optimization"]
    bug = ["Bug"]
    ignore = ["Task", "Epic"]

    # Completed Work
    for completed in sprint_report["contents"]["completedIssues"]:

        # Short-circuit for things we don't track
        if completed["typeName"] in ignore:
            continue

        try:
            issue_points = int(completed["currentEstimateStatistic"]["statFieldValue"]["value"])
        except:
            issue_points = 0

        points["completed"] += issue_points
        items["completed"] += 1

        unplanned = False
        if completed["key"] in sprint_report["contents"]["issueKeysAddedDuringSprint"].keys():
            unplanned = True
            points["unplanned_completed"] += issue_points
            items["unplanned_completed"] += 1
        else:
            points["committed"] += issue_points
            items["committed"] += 1
            points["planned_completed"] += issue_points
            items["planned_completed"] += 1

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
            points["committed"] += issue_points
            items["committed"] += 1

    # Removed Work
    for removed in sprint_report["contents"]["puntedIssues"]:

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

        points["removed"] += issue_points
        items["removed"] += 1

    return {
        "points" : points,
        "items" : items
    }

def getNotionSection(sprint_data):
    points = sprint_data['metrics']['points']
    items = sprint_data['metrics']['items']
    return {
        "Points committed": points['committed'],
        "Points completed": points['completed'],
        "Items committed": items['committed'],
        "Items completed": items['completed'],
        "Predictability" : points['completed']/points['committed']*100,
        "Predictability of Commitments" : points['planned_completed']/points['committed']*100,
        "Velocity": points['completed'],
        "Bugs": items['bugs_completed']
    }

def collectSprintData(projectKey, sprintID=False):
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

    try:
        sprint_data['sprint_number'] = re.search("(S|Sprint )(?P<number>\d+)", current_sprint["name"]).group('number')
    except:
        raise Exception("I couldn't determine the sprint number from that sprint's name")

    sprint_data['sprint_goals'] = current_sprint['goal'].split("\n")

    sprint_report = getSprintReport(board_id, sprint_data['sprint_id'])

    if not sprint_report:
        raise Exception("I couldn't find that sprint")
        exit()

    sprint_data['metrics'] = getSprintMetrics(sprint_report)

    sprint_data['notion'] = getNotionSection(sprint_data)
    return sprint_data

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("project", help="Project Key")
    ap.add_argument("-s", "--sprint", required=False, help="Sprint ID (default to current sprint)")

    args = vars(ap.parse_args())

    data = collectSprintData(args['project'], args['sprint'])

    pprint(data)

    print("URL:")
    print(generateGoogleFormURL(data))

if __name__ == "__main__":
    main()
