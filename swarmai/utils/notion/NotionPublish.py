# publish_to_notion.py
import json
import os
from datetime import datetime
from notion_client import Client

def publish_to_notion(NOTION_API_KEY, NOTION_DATABASE_ID, json_path):
    with open(json_path) as f:
        data = json.load(f)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    properties = {
        "Name": {"title": [{"text": {"content": timestamp}}]},
    }

    # Read in the JSON data
    with open(json_path) as f:
        data = json.load(f)

    # Get the current timestamp for the page title
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Create the new page properties
    properties = {
        "Name": {"title": [{"text": {"content": timestamp}}]},
    }

    # Prepare the children blocks
    children = []
    for key, value in data.items():
        answer_content = f"Answer {key}: {value['Answer']}\n\n"
        answer_paragraphs = [answer_content[i:i + 2000] for i in range(0, len(answer_content), 2000)]

        answer_children = []
        for paragraph in answer_paragraphs:
            answer_children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": paragraph}}
                        ]
                    }
                }
            )

        children.append(
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"Question {key}: {value['Question']}\n"}}
                    ],
                    "children": answer_children
                }
            }
        )

    # Create a new page in Notion with children content
    notion = Client(auth=NOTION_API_KEY)
    new_page = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children": children,
    }

    try:
        page = notion.pages.create(**new_page)
        print(f"New page created with title {timestamp}")
        print(f"Page URL: https://www.notion.so/{page['id'].replace('-', '')}")
    except Exception as e:
        print("Error creating page:", e)
