#!/usr/bin/env python3

import re
import csv
import time
import sys
import configparser
from datetime import datetime
from collections import defaultdict
from atlassian import Confluence

def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def create_confluence_client(config):
    username = config.get('config', 'confluence_username')
    api_token = config.get('config', 'confluence_api_token')

    confluence = Confluence(
        url='https://pinger.atlassian.net/wiki',
        username=username,
        password=api_token)

    return confluence

def get_all_pages_from_spaces(confluence, spaces, limit=100):
    all_pages = []

    for space in spaces:
        start = 0
        has_more_pages = True

        while has_more_pages:
            all_pages_in_space = confluence.get_all_pages_from_space(space, start=start, limit=limit, status=None, expand=None, content_type='page')

            if not all_pages_in_space:
                has_more_pages = False
                continue

            all_pages.extend(all_pages_in_space)
            start += limit

    return all_pages

def process_pages(confluence, pages, space):
    page_info_list = []

    for page in pages:
        content = confluence.get_page_by_id(page['id'], expand='history,version,body.view', status=None, version=None)
        title = content['title']

        url = 'https://pinger.atlassian.net/wiki/spaces/{}/pages/{}'.format(space, page['id'])

        # ... rest of the content processing ...
        
        counts = defaultdict(int)

        if any(val > 0 for val in counts.values()):
            page_info = {
                'title': title,
                'url': url,
                'created_date': created_date_formatted,
                'modified_date': modified_date_formatted,
                'counts': counts
            }
            page_info_list.append(page_info)

    return page_info_list

def write_csv(space, page_info_list, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'url', 'created_date', 'modified_date', 'counts']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for page_info in page_info_list:
            counts_string = ', '.join(f'{key}: {value}' for key, value in page_info['counts'].items())
            page_info['counts'] = counts_string
            writer.writerow(page_info)

def main():
    config = load_config('config.ini')
    confluence = create_confluence_client(config)
    spaces = sys.argv[1].split(',')

    start_time = time.time()

    for space in spaces:
        start = 0
        limit = 100
        page_info_list = []
        has_more_pages = True

        while has_more_pages:
            all_pages_in_space = confluence.get_all_pages_from_space(space, start=start, limit=limit, status=None, expand=None, content_type='page')
            has_more_pages = len(all_pages_in_space) == limit

            pages = [page for page in all_pages_in_space if page['type'] == 'page']
            page_info_list.extend(process_pages(confluence, pages, space))

            start += limit

        write_csv(space, page_info_list, f'{space}-output.csv')
    
    end_time = time.time()

    execution_time = end_time - start_time
    execution_time_minutes = execution_time / 60
    print(f"Execution time: {execution_time_minutes:.2f} minutes")

if __name__ == "__main__":
    main()
