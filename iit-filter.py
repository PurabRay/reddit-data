import json

# Load the original data with UTF-8 encoding
with open("data-reddit.json", "r", encoding="utf-8") as infile:
    data = json.load(infile)

# Filter out objects with empty 'results'
filtered_data = [entry for entry in data if entry["results"]]

# Save the filtered data with UTF-8 encoding
with open("iit-reddit.json", "w", encoding="utf-8") as outfile:
    json.dump(filtered_data, outfile, indent=4, ensure_ascii=False)
