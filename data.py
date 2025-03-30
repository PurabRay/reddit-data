import praw
import json
import os
import time
import random
from sentence_transformers import SentenceTransformer, util


with open("data.json", "r", encoding="utf-8") as f:
    startup_data = json.load(f)

search_queries = set()

for entry in startup_data:
    # Extract founder name
    first_name = entry.get("firstName", "").strip()
    last_name = entry.get("lastName", "").strip()
    if first_name or last_name:
        full_name = f"{first_name} {last_name}".strip()
        search_queries.add(f"founder {full_name}")

    # Extract company name from linkedinCompanyUrl
    linkedin_url = entry.get("linkedinCompanyUrl", "").strip()
    if linkedin_url and "/" in linkedin_url:
        company_slug = linkedin_url.rstrip("/").split("/")[-1]
        if company_slug:
            search_queries.add(f"startup {company_slug}")
            search_queries.add(f"company {company_slug}")

search_queries = list(search_queries)
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
    checkpoint_file = "data-reddit.json"

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
with open("reddit-data.json", "w", encoding="utf-8") as f:
    json.dump(scraped_data, f, ensure_ascii=False, indent=4)

print("Scraping complete. Data saved in 'reddit-data.json'.")
