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
4. Store API key in .netrc
   - `touch ~/.netrc`
   - `chmod 600 ~/.netrc`
   - `open ~/.netrc`
   - Copy the following format, subsituting [things]
   ```
   machine thetower.atlassian.net
   login [your_jira_login]
   password [your_generated_jira_api_key]
   ```
4. Download / Clone this repository
   - *The rest of these instructions assume that they're being from from within your local repo*
5. Install Dependencies
   `pipenv install`

You should now be ready to go!

# General Usage
Make sure to run the script through pipenv
`pipenv run python3 name_of_script.py`

# Scripts
### Sprint Metrics
Takes a project key, and optional sprint ID as parameters and returns metrics and other sprint information
```
sprint_metrics.py [-h] [-s SPRINT] project

positional arguments:
  project               Project Key

optional arguments:
  -h, --help            show this help message and exit
  -s SPRINT, --sprint SPRINT
                        Sprint ID (default to current sprint)
```

Example:
```
$ pipenv run python3 sprint_metrics.py YOSHI -s 3864
{
    "metrics": {
        "items": {
            "bugs_completed": 3,
            "committed": 17,
            "completed": 17,
            "not_completed": 1,
            "planned_completed": 16,
            "removed": 0,
            "stories_completed": 10,
            "unplanned_bugs_completed": 1,
            "unplanned_completed": 1,
            "unplanned_stories_completed": 0
        },
        "points": {
            "committed": 38.0,
            "completed": 33.0,
            "feature_completed": 33.0,
            "not_completed": 5.0,
            "optimization_completed": 0,
            "planned_completed": 33.0,
            "removed": 0,
            "unplanned_completed": 0
        }
    },
    "project_name": "YOSHI",
    "sprint_goals": [
        "- Unblock ourselves from finishing Swahili MVP in Sprint 20",
        "- Begin work on Badging"
    ],
    "sprint_id": 3864,
    "sprint_number": "19"
}
URL:
https://docs.google.com/forms/d/e/1FAIpQLSdF__V1ZMfl6H5q3xIQhSkeZMeCNkOHUdTBFdYA1HBavH31hA/viewform?entry.1082637073=YOSHI&entry.1975251686=19&entry.1427603868=38&entry.1486076673=33&entry.493624591=33&entry.1333444050=0&entry.254612996=33&entry.2092919144=0&entry.611444996=5&entry.976792423=0&entry.2095001800=17&entry.1399119358=17&entry.954885633=16&entry.485777497=1&entry.1980453543=10&entry.370334542=0&entry.448087930=3&entry.1252702382=1&entry.128659456=1&entry.976792423=0&
```
