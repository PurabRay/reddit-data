import praw
import json
import os
import ast
import time
import random
from sentence_transformers import SentenceTransformer, util

# Load founders and companies data
with open("founders_companies.json", "r", encoding="utf-8") as f:
    startup_data = json.load(f)

search_queries = []

for entry in startup_data:
    if "Company" in entry:
        company = entry["Company"].strip()
        if company:
            search_queries.append(f"startup {company}")
            search_queries.append(f"company {company}")

    if "Founders" in entry:
        founders_field = entry["Founders"].strip()
        if founders_field.startswith('[') and founders_field.endswith(']'):
            try:
                founders = ast.literal_eval(founders_field)
                if isinstance(founders, list):
                    for founder in founders:
                        search_queries.append(f"founder {str(founder).strip()}")
                else:
                    search_queries.append(f"founder {str(founders).strip()}")
            except Exception as e:
                print(f"Error parsing Founders for entry {entry}: {e}")
                for founder in founders_field.split(','):
                    if founder.strip():
                        search_queries.append(f"founder {founder.strip()}")
        else:
            for founder in founders_field.split(','):
                if founder.strip():
                    search_queries.append(f"founder {founder.strip()}")

search_queries = list(set(search_queries))
print(f"Total unique queries to search: {len(search_queries)}")

# Setup Reddit client
reddit = praw.Reddit(
    client_id="beTKjKraeFN1liBYyCg9-Q",
    client_secret="HFRJS0_0Hgx7FnNG8MFunNkQcyJJUA",
    user_agent="MyRedditScraper/1.0"
)

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

def is_relevant_to_query(query, text, threshold=0.6):
    try:
        query_emb = model.encode(query, convert_to_tensor=True)
        text_emb = model.encode(text, convert_to_tensor=True)
        score = util.cos_sim(query_emb, text_emb).item()
        return score >= threshold
    except Exception as e:
        print(f"Similarity check error: {e}")
        return False

def scrape_reddit(queries, limit=5):
    scraped_results = []
    processed_count = 0
    total_queries = len(queries)
    checkpoint_file = "reddit_scraped_data.json"

    for query in queries:
        print(f"Scraping Reddit for: {query} ({processed_count+1}/{total_queries})")
        search_results = []
        try:
            for submission in reddit.subreddit("all").search(query, limit=limit):
                body = submission.selftext.strip() if hasattr(submission, 'selftext') else ""
                excerpt_raw = (submission.title + " " + body).strip()
                excerpt = excerpt_raw[:500]
                if is_relevant_to_query(query, excerpt):
                    search_results.append({
                        "title": submission.title,
                        "url": submission.url,
                        "score": submission.score,
                        "comments": submission.num_comments,
                        "excerpt": excerpt
                    })
        except Exception as e:
            print(f"Error scraping query '{query}': {e}")

        scraped_results.append({"query": query, "results": search_results})
        processed_count += 1

        if processed_count % 10 == 0:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(scraped_results, f, ensure_ascii=False, indent=4)
            print(f"Checkpoint saved after {processed_count} queries.")

    return scraped_results

# Run scraper
scraped_data = scrape_reddit(search_queries, limit=5)

# Final save
with open("reddit_scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(scraped_data, f, ensure_ascii=False, indent=4)

print("Scraping complete. Data saved in 'reddit_scraped_data.json'.")
