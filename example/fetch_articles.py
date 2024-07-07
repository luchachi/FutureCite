import urllib.request
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime
import re
import time
import csv

def parse_arxiv_data(root, start_year, end_year):
    batch_articles = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text
        journal_ref = entry.find('{http://www.w3.org/2005/Atom}arxiv:journal_ref')
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        doi = entry.find('{http://www.w3.org/2005/Atom}arxiv:doi')
        
        journal = journal_ref.text if journal_ref is not None else "Not available"
        doi = doi.text if doi is not None else "Not available"
        
        year = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').year
        
        # Filter conditions
        word_count = len(re.findall(r'\w+', abstract))
        has_doi = True # doi != "Not available"
        
        if (start_year is None or year >= start_year) and (end_year is None or year <= end_year) and word_count >= 100 and has_doi:
            batch_articles.append({
                'title': title,
                'abstract': abstract,
                'journal': journal,
                'year': year,
                'doi': doi,
                'source': 'arXiv'
            })
            
    return batch_articles

def fetch_data(api_name, search_query, excluded_dois, max_results, start_year=None, end_year=None):
    base_urls = {
        'arxiv': 'http://export.arxiv.org/api/query?',
    }
    
    articles = []
    start = 0
    batch_size = 100
    previous_length = 0
    consecutive_no_increase = 0

    while len(articles) < max_results:
        if api_name == 'arxiv':
            encoded_query = urllib.parse.quote(search_query)
            query = f'search_query=all:{encoded_query}&start={start}&max_results={batch_size}'
            response = urllib.request.urlopen(base_urls[api_name] + query).read()
            root = ET.fromstring(response)
            batch_articles = parse_arxiv_data(root, start_year, end_year)

        # Filter out articles with DOIs already fetched
        batch_articles = [article for article in batch_articles if article['doi'] not in excluded_dois]
        
        articles.extend(batch_articles)
        start += batch_size
        
        # Check if there are no new results
        if len(articles) == previous_length:
            consecutive_no_increase += 1
            if consecutive_no_increase >= 2:
                if len(articles) == 0:
                    print(f"No results found for {api_name} search.")
                else:
                    print(f"No new results for {api_name} search. Stopping.")
                break
        else:
            consecutive_no_increase = 0
        
        previous_length = len(articles)

        # Delay to avoid rate limiting
        time.sleep(1)
        
        # Exit if no more results
        if len(batch_articles) == 0:
            break

    return articles[:max_results]

def fetch_and_combine_data(search_query, max_results, start_year=None, end_year=None):
    api_names = ['arxiv']
    all_articles = []
    excluded_dois = set()

    for api_name in api_names:
        print(f"Fetching data from {api_name}...")
        articles = fetch_data(api_name, search_query, excluded_dois, max_results, start_year, end_year)
        all_articles.extend(articles)
        excluded_dois.update([article['doi'] for article in articles])
        if len(all_articles) >= max_results:
            break
    
    return all_articles[:max_results]

def multiple_queries(queries, max_results, start_year, end_year):
    articles = []
    for q in queries:
        articles.append(fetch_and_combine_data(q, max_results, start_year, end_year))
    return articles

# Query articles    

search_query = [
    "carbon capture",
    "carbon removal",
    "rock weathering",
    "hydrogen electrochemical",
    "sustainability",
    ]

start_year = 2010
end_year = 2024
max_results = 100

# Multiple query
searched_articles = multiple_queries(search_query, max_results, start_year, end_year)
articles = [b for a in searched_articles for b in a]

# Single query
# articles = fetch_and_combine_data(search_query, max_results, start_year, end_year)

#%% Specify the CSV file name
csv_file = "Demo_articles.csv"

# Get the keys from the first dictionary as the header
header = list(articles[0].keys())

# Open the CSV file in write mode
with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=header)

    # Write the header
    writer.writeheader()

    # Write the rows
    for row in articles:
        writer.writerow(row)

