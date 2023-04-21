#!/usr/bin/env python3

import re
import csv
import time
import sys
import configparser
import threading
import pytz
from retry import retry
from datetime import datetime
from collections import defaultdict
from atlassian import Confluence
from requests.exceptions import ReadTimeout

def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def create_confluence_client(config):
    username = config.get('config', 'confluence_username')
    api_token = config.get('config', 'confluence_api_token')
    confluence_url = config.get('config', 'confluence_url')

    confluence = Confluence(
        url=confluence_url,
        username=username,
        password=api_token)

    return confluence


@retry((ConnectionError, ReadTimeout), tries=10, delay=10, backoff=2)
def get_page_with_retry(confluence, page_id):
    return confluence.get_page_by_id(page_id, expand='history,version,body.view', status=None, version=None)

def print_list_length_every_5_minutes(page_info_list):
    print(f"The current length of the list is: {len(page_info_list)} items")
    threading.Timer(300, print_list_length_every_5_minutes, args=[page_info_list]).start()
    
def get_content_macro_counts(body_text):
    pattern1 = r'unknown-macro\?name=(\w+)'
    pattern2 = r'wysiwyg-unknown-macro'
    matches1 = re.findall(pattern1, body_text)
    matches2 = re.findall(pattern2, body_text)

    counts = defaultdict(int)
    for match in matches1:
        key = f'unknown-macro?name={match}'
        counts[key] += 1

    counts['wysiwyg-unknown-macro'] = len(matches2)

    return counts

def process_pages(confluence, pages, space, config, output_file, total_pages):
    processed_pages = []
    for index, page in enumerate(pages):
        try:
            content = get_page_with_retry(confluence, page['id'])
            title = content['title']

            url = '{}/spaces/{}/pages/{}'.format(config.get('config', 'confluence_url'), space, page['id'])

            created_date = content['history']['createdDate']
            modified_date = content['version']['when']

            created_date_obj = datetime.fromisoformat(created_date.replace("Z", ""))
            modified_date_obj = datetime.fromisoformat(modified_date.replace("Z", ""))

            created_date_formatted = created_date_obj.strftime("%Y-%m-%d")
            modified_date_formatted = modified_date_obj.strftime("%Y-%m-%d")

            body_text = content['body']['view']['value']
            counts = get_content_macro_counts(body_text)

            if any(val > 0 for val in counts.values()):
                page_info = {
                    'title': title,
                    'url': url,
                    'created_date': created_date_formatted,
                    'modified_date': modified_date_formatted,
                    'counts': counts
                }
                processed_pages.append(page_info)

            print(f"Processing page {index+1}/{total_pages}: {title}")

        except Exception as e:
            print(f"Error processing page {page['id']} ({page['title']}): {str(e)}")

    write_csv(space, processed_pages, output_file, mode='a')
    return processed_pages

def write_csv(space, page_info_list, output_file, mode='a'):
    with open(output_file, mode, newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'url', 'created_date', 'modified_date', 'counts']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if mode == 'w':
            writer.writeheader()

        for page_info in page_info_list:
            counts_string = ', '.join(f'{key}: {value}' for key, value in page_info['counts'].items())
            # Create a new dictionary to avoid modifying the original page_info
            modified_page_info = page_info.copy()
            modified_page_info['counts'] = counts_string
            writer.writerow(modified_page_info)

def main():
    config = load_config('config.ini')
    confluence = create_confluence_client(config)
    spaces = sys.argv[1].split(',')

    start_time = time.time()
    central = pytz.timezone('US/Central')
    current_time = datetime.now(central)
    print("Current time in Central Time Zone:", current_time.strftime('%Y-%m-%d %H:%M:%S'))

    for space in spaces:
        start = 0
        limit = 100
        page_info_list = []
        total_pages = 0
        output_file = f'{space}-output.csv'
        space_info = confluence.get_space(space, expand='homepage')
        print('Processing Confluence Space: {}'.format(space))
        print('---------------------------------------------')

        write_csv(space, [], output_file, mode='w')

        # Calculate the total number of pages in the space
        while True:
            all_pages_in_space = confluence.get_all_pages_from_space(space, start=start, limit=limit, status=None, expand=None, content_type='page')
            fetched_pages = len(all_pages_in_space)
            total_pages += fetched_pages
            if fetched_pages < limit:
                break
            start += limit

        print(f"Total number of pages in space {space}: {total_pages}")

        # Reset the start variable before processing the pages
        start = 0
        has_more_pages = True

        pages = []
        while has_more_pages:
            all_pages_in_space = confluence.get_all_pages_from_space(space, start=start, limit=limit, status=None, expand=None, content_type='page')
            has_more_pages = len(all_pages_in_space) == limit

            pages.extend([page for page in all_pages_in_space if page['type'] == 'page'])
            start += limit

        processed_pages = process_pages(confluence, pages, space, config, output_file, total_pages)
        page_info_list.extend(processed_pages)

        write_csv(space, page_info_list, output_file)

    end_time = time.time()

    execution_time = end_time - start_time
    execution_time_minutes = execution_time / 60
    print(f"Execution time: {execution_time_minutes:.2f} minutes")

if __name__ == "__main__":
    main()
