import json

# Read using UTF-8 encoding to avoid decode errors
with open("reddit_scraped_data.json", "r", encoding="utf-8") as infile:
    data = json.load(infile)

# Filter out entries where "results" is empty
filtered_data = [entry for entry in data if entry["results"]]

# Write the filtered data using UTF-8 encoding as well
with open("reddit.json", "w", encoding="utf-8") as outfile:
    json.dump(filtered_data, outfile, indent=4)
