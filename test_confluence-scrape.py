#!/usr/bin/env python3

import unittest
import configparser
from unittest.mock import MagicMock, patch
from collections import defaultdict
from datetime import datetime
from atlassian import Confluence
from confluence_scrape import process_pages, main

class TestConfluenceScrape(unittest.TestCase):
    def test_process_pages(self):
        confluence_mock = MagicMock(spec=Confluence)
        config = configparser.ConfigParser()
        config.read('config.ini')
        confluence_url = config.get('config', 'confluence_url')

        pages = [
            {
                'id': '12345',
                'title': 'Sample Page 1',
                'space': {'key': 'QA', 'id': '1'},
                'version': {'number': 1},
                'created_date': '2021-09-01T12:34:56Z',
            },
            {
                'id': '67890',
                'title': 'Sample Page 2',
                'space': {'key': 'QA', 'id': '1'},
                'version': {'number': 2},
                'created_date': '2021-09-02T12:34:56Z',
            },
        ]

        space = 'QA'

        confluence_mock.get_page_by_id.side_effect = [
            {
                'title': 'Sample Page 1',
                'history': {'createdDate': '2021-09-01T12:34:56Z'},
                'version': {'when': '2021-09-01T12:34:56Z'},
                'body': {'view': {'value': 'unknown-macro?name=test1<br>wysiwyg-unknown-macro'}},
            },
            {
                'title': 'Sample Page 2',
                'history': {'createdDate': '2021-09-02T12:34:56Z'},
                'version': {'when': '2021-09-02T12:34:56Z'},
                'body': {'view': {'value': ''}},
            },
        ]

        expected_page_info_list = [
            {
                'title': 'Sample Page 1',  # Change the title to match the title in the pages list
                'url': f'{confluence_url}/spaces/QA/pages/12345',
                'created_date': '2021-09-01',
                'modified_date': '2021-09-01',
                'counts': {
                    'unknown-macro?name=test1': 1,
                    'wysiwyg-unknown-macro': 1
                }
            }
        ]


        self.assertEqual(process_pages(confluence_mock, pages, space, config), expected_page_info_list)

if __name__ == '__main__':
    unittest.main()
