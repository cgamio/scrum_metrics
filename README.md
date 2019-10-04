# Installation Instructions
1. Install [Homebrew](https://brew.sh)
   Homebrew is a package manager for OS X (similar to apt or yum). It's an easy way to install 3rd party tools, and what we'll be using to install the rest of the requirements.
2. Install Python
   `brew install python3`
3. Install PipEnv
   `pip install pipenv` 
4. Download / Clone this repository
   *The rest of these instructions assume that they're being from from within your local repo*
5. Install Dependencies
   `pipenv install`

You should now be ready to go!

# General Usage
Make sure to run the script through pipenv
`pipenv run python name_of_script.py`

# Scripts
### Sprint Metrics
Takes a project key, and optional sprint ID as parameters and returns metrics
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
$ pipenv run python sprint_metrics.py BWSR
Team: BOWSER
Sprint Number: 20
{
    "items": {
        "bugs_completed": 0,
        "committed": 11,
        "completed": 8,
        "not_completed": 4,
        "planned_completed": 7,
        "removed": 0,
        "stories_completed": 6,
        "unplanned_bugs_completed": 0,
        "unplanned_completed": 1,
        "unplanned_stories_completed": 0
    },
    "points": {
        "committed": 29.0,
        "completed": 21.0,
        "feature_completed": 21.0,
        "not_completed": 11.0,
        "optimization_completed": 0,
        "planned_completed": 18.0,
        "removed": 0,
        "unplanned_completed": 3.0
    }
}
```
