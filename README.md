# atlassian-content-checks
A handful of scripts to check Jira, Bitbucket, Confluence pages for missing plugins, macros, broken-links, etc.

## Prerequisites
- Python 3.x

## scripts
| title | description | test |
| ----- | ----------- | ---- |
| [confluence_scrape.py](confluence_scrape.py) | Traverse all pages in a given Confluence space, return all pages using unknown macros | [test_confluence_scrape.py](test_confluence_scrape.py) |

## usage
- Make sure you have Python 3.x installed on your system.
- Create and populate a `config.ini` file with relevant Confluence/Atlassian info. You can find/create an API token [here](https://id.atlassian.com/manage-profile/security/api-tokens).
```ini
[config]
confluence_username = email@example.com
confluence_api_token = token_string
confluence_url = https://test.atlassian.net/wiki
```
- Pass the relevant space name(s) into the script on the command line, in a comma-separated list.

```console
foo@bar:~$ pip install -r requirements.txt
foo@bar:~$ python confluence_scrape.py ENG,MKT
```

This will dump out a csv as `{space}-output.csv`.
![image](https://user-images.githubusercontent.com/87497161/233491176-4545203d-7383-43fa-9430-6590e27cd565.png)
