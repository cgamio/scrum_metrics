# Installation Instructions
1. Install [Homebrew](https://brew.sh)
   - Homebrew is a package manager for OS X (similar to apt or yum). It's an easy way to install 3rd party tools, and what we'll be using to install the rest of the requirements.
2. Install Python
   `brew install python3`
3. Install PipEnv
   `pip3 install pipenv`
   -  If you get this error: `pip: command not found`
        Do this first:
       ```
       curl https://bootstrap.pypa.io/get-pip.py >get-pip.py
       sudo python get-pip.py
       ```

        For more detailed instructions you could check out [this video](https://www.youtube.com/watch?v=yBdZZGPpYxg).
        After this you should be able to start step 3 over
4. [Create Jira API key](https://confluence.atlassian.com/cloud/api-tokens-938839638.html)
4. Set up Environment Variables
   - `touch ~/.bashrc`
   - `open ~/.bash`
   - Add the following lines to the file in the following format, subsituting [things]
   ```
   export JIRA_HOST='thetower.atlassian.net'
   export JIRA_TOKEN='[your jira token]'
   export JIRA_USER='[your jira login]'
   ```
   - Open a new terminal, or run the following command to load new environment variables `source ~/.bashrc`
4. Download / Clone this repository
   - *The rest of these instructions assume that they're being from from within your local repo*
5. Install Dependencies
   `pipenv install`

You should now be ready to go!

# General Usage
Make sure to run the script through pipenv
`pipenv run python3 name_of_script.py` for one-off commands or `pipenv shell` to run multiple commands without needing to specify `pipenv run python3` before each one.

# Scripts
### Sprint Metrics
This script no longer has a main function, and instead the driving force behind the slack slash commands running in Lambda. You can still access the functions in the script locally by running python in interactive mode

Example:
```
$ pipenv shell
(scrum_metrics) bash-3.2$ python -i sprint-metrics.py
>>> sprint_data = collectSprintData("YOSHI")
>>> pprint(sprint_data)
{
    "board_name": "YOSHI BOARD",
    "metrics": {
        "items": {
            "bugs_completed": 0,
            "committed": 10,
            "completed": 0,
            "not_completed": 10,
            "planned_completed": 0,
            "removed": 0,
            "stories_completed": 0,
            "unplanned_bugs_completed": 0,
            "unplanned_completed": 0,
            "unplanned_stories_completed": 0
        },
        "points": {
            "committed": 30,
            "completed": 0,
            "feature_completed": 0,
            "not_completed": 30,
            "optimization_completed": 0,
            "planned_completed": 0,
            "removed": 0,
            "unplanned_completed": 0
        }
    },
    "project_name": "YOSHI",
    "sprint_end": "2019-11-06T20:01:00.000Z",
    "sprint_goals": [
        "Goals:",
        "1. Hide all ads on content and feed pages for \"ads-free\" users",
        "2. Determine the work involved for rendering social images for \"ads-free\" users"
    ],
    "sprint_id": 4013,
    "sprint_number": "22",
    "sprint_start": "2019-10-23T20:01:17.081Z"
}
```

# Notion Integration

The slash command now has the ability to accept a Notion URL, and update that page with relevant Sprint Data. This is useful to generate Sprint Reports using a template [like this](https://www.notion.so/mediaos/Sprint-Review-Template-3edba77b45d2492592286df310b0c819#5217e0db2a914026a5e433ed0901bdce)

So far the available "short codes" are:
- [average-velocity]
- [bugs-completed]
- [completed-issues-link]
- [items-committed]
- [items-completed]
- [items-not-completed-link]
- [items-removed-link]
- [original-committed-link]
- [points-committed]
- [points-completed]
- [predictability-commitments]
- [predictability]
- [sprint-end]
- [sprint-goal]
- [sprint-number]
- [sprint-start]
- [team-name]
