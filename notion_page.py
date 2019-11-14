import os

from notion.client import NotionClient
from notion.block import PageBlock, HeaderBlock, DividerBlock
from sprint_metrics import *
from datetime import datetime

class NotionPage:

    def __init__(self, url):
        self.__client = NotionClient(token_v2=os.environ.get('NOTION_TOKEN'))
        self.blocks = self.__client.get_block(url)

    def createSprintReport(self, sprint_data):
        sprint_report = self.blocks.children.add_new(PageBlock, title=f"{sprint_data['project_name']} Sprint {sprint_data['sprint_number']} Report")

        sprint_report.children.add_new(DividerBlock)

        start_date = datetime.strptime(sprint_data['sprint_start'].split('T')[0], '%Y-%m-%d')
        end_date = datetime.strptime(sprint_data['sprint_end'].split('T')[0], '%Y-%m-%d')
        date_string = datetime.strftime(start_date, '%m/%d/%Y')
        date_string += " - "
        date_string += datetime.strftime(end_date, '%m/%d/%Y')

        sprint_report.children.add_new(HeaderBlock, title=f"[{sprint_data['project_name']} Sprint {sprint_data['sprint_number']} Report ({date_string})]({sprint_data['sprint_report_url']})")

        return sprint_report

    def searchAndReplace(self, replacement_dictionary):
        queue = []

        queue.extend(self.blocks.children)

        while queue:
            block = queue.pop()
            print(f"Processing Block: {block}")

            try:
                queue.extend(block.children)
            except AttributeError:
                print("Block has no more children, end of the line")

            try:
                new_title = block.title
                for search, replace in replacement_dictionary.items():
                    new_title = new_title.replace(search, replace)

                if block.title != new_title:
                    print(f"{block.title} -> {new_title}")
                    block.title = new_title
            except AttributeError:
                print("Block has no title, moving on")
