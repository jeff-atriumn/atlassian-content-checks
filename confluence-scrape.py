#!/usr/bin/env python3

import re
import sys
import csv
import time
import configparser
from datetime import datetime
from collections import defaultdict
from atlassian import Confluence
from tabulate import tabulate

# Read config.ini for API token
config = configparser.ConfigParser()
config.read('config.ini')
username = config.get('config', 'confluence_username')
api_token = config.get('config', 'confluence_api_token')

confluence = Confluence(
    url='https://pinger.atlassian.net/wiki',
    username=username,
    password=api_token)

spaces = sys.argv[1].split(',')
page_info_list = []
limit = 100

def calculate_total_counts(page_info_list):
    total_counts = defaultdict(int)
    for page_info in page_info_list:
        for key, value in page_info['counts'].items():
            total_counts[key] += value
    return total_counts

start_time = time.time()

for space in spaces:
    print(space)
    start = 0
    has_more_pages = True

    while has_more_pages:
        all_pages_in_space = confluence.get_all_pages_from_space(space, start=start, limit=limit, status=None, expand=None, content_type='page')

        if not all_pages_in_space:
            has_more_pages = False
            continue

        for page in all_pages_in_space:
            content = confluence.get_page_by_id(page['id'], expand='history,version,body.view', status=None, version=None)
            title = content['title']
            url = 'https://pinger.atlassian.net/wiki/spaces/{}/pages/{}'.format(space, page['id'])

            created_date = content['history']['createdDate']
            modified_date = content['version']['when']

            created_date_obj = datetime.fromisoformat(created_date.rstrip("Z"))
            modified_date_obj = datetime.fromisoformat(modified_date.rstrip("Z"))

            created_date_formatted = created_date_obj.strftime("%Y-%m-%d")
            modified_date_formatted = modified_date_obj.strftime("%Y-%m-%d")
            
            body_text = content['body']['view']['value']

            pattern1 = r'unknown-macro\?name=(\w+)'
            pattern2 = r'wysiwyg-unknown-macro'
            matches1 = re.findall(pattern1, body_text)
            matches2 = re.findall(pattern2, body_text)

            counts = defaultdict(int)
            for match in matches1:
                key = f'unknown-macro?name={match}'
                counts[key] += 1

            counts['wysiwyg-unknown-macro'] = len(matches2)

            if any(val > 0 for val in counts.values()):
                page_info = {
                    'title': title,
                    'url': url,
                    'created_date': created_date_formatted,
                    'modified_date': modified_date_formatted,
                    'counts': counts
                }
                page_info_list.append(page_info)            

        start += limit

    print(len(page_info_list))
    
    # Calculate and print total counts
    total_counts = calculate_total_counts(page_info_list)
    print("Total counts for each pattern:", total_counts)
    
    with open('{}-output.csv'.format(space), 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'url', 'created_date', 'modified_date', 'counts']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for page_info in page_info_list:
            counts_string = ', '.join(f'{key}: {value}' for key, value in page_info['counts'].items())
            page_info['counts'] = counts_string
            writer.writerow(page_info)

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time: {execution_time:.2f} seconds")