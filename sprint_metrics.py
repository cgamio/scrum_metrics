import requests
from requests.auth import HTTPBasicAuth
import json
import netrc
import argparse
import re

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

def pprint(json_obj):
    print(json.dumps(json_obj, sort_keys=True, indent=4, separators=(",", ": ")))

def makeRequest(verb, url, params=None):
    response = requests.request(verb, url, headers=headers, auth=auth, params=params)
    if response.status_code == 200:
        return(json.loads(response.text))
    else:
        return(False)

def getBoards(name=None):
    url = f"{jira_url}board?"

    if name != None:
        url = f"{url}name={name}"

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
    ignore = ["Task"]

    # Completed Work
    for completed in sprint_report["contents"]["completedIssues"]:

        # Short-circuit for things we don't track
        if completed["typeName"] in ignore:
            continue

        try:
            issue_points = completed["currentEstimateStatistic"]["statFieldValue"]["value"]
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
            issue_points = incomplete["currentEstimateStatistic"]["statFieldValue"]["value"]
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
            issue_points = removed["currentEstimateStatistic"]["statFieldValue"]["value"]
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

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("project", help="Project Key")
    ap.add_argument("-s", "--sprint", required=False, help="Sprint ID (default to current sprint)")

    args = vars(ap.parse_args())

    boards = getBoards(args["project"])
    if boards == False or boards["total"] == 0:
        print ("Sorry, I couldn't find that project's board")
        exit()

    board_id = boards["values"][0]["id"]
    project_name = boards["values"][0]["location"]["projectName"]
    print(f"Team: {project_name}")

    current_sprint_id = None
    if args["sprint"]:
        current_sprint_id = args["sprint"]
        current_sprint = getSprintFromID(current_sprint_id)
    else:
        try:
            current_sprint = getCurrentSprintFromBoard(board_id)["values"][0]
        except:
            print ("Sorry, I couldn't find that project's current sprint")
            exit()

    current_sprint_id = current_sprint["id"]
    print(f"Sprint ID: {current_sprint_id}")
    try:
        sprint_number = re.search("(S|Sprint )(?P<number>\d+)", current_sprint["name"]).group('number')
        print(f"Sprint Number: {sprint_number}")
    except:
        print(f"Unable to determine Sprint Number from Sprint Name: {current_sprint['name']}")


    sprint_report = getSprintReport(board_id, current_sprint_id)

    if not sprint_report:
        print("Unable to find that sprint :(")
        exit()

    metrics = getSprintMetrics(sprint_report)

    pprint(metrics)

if __name__ == "__main__":
    main()
