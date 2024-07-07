import anthropic
import re
import os
import csv

def Claude_Messager(key,text_input):
    client = anthropic.Anthropic(
        api_key=key,
    )
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=300,
        temperature=0,
        messages=text_input
    )
    
    return(message.content)

def Message_Builder(article,Qual_met,Quant_met,Fut_met,Details):
        
    message = []
    
    query = "Here is the abstract of a paper: " + article['abstract']
            
    if Qual_met:
        query = query + "For this paper, strictly only provide relative scores out of 10 for the following: " + "; ".join(Qual_met) + "\n"
    if Quant_met:
        query = query + "For this paper, provide a lower and upper bound value separated by a hyphen for the following: " + "; ".join(Quant_met) + "\n"
    if Fut_met:
        query = query + "For this paper and based on the previous values provided, provide estimated lower and upper bound values separated by a hyphen for the following: " +"; ".join(Fut_met) + "\n"
        
    query = query + "For this paper provide descriptions of the following: " + "; ".join(Details) + "\n"
    query = query + "End non-empty lines with a hashtag, return each value in a different line"
    
    # Message to ask for outputs
    message.append({"role": "user","content": query})
    message.append({"role": "assistant","content": "The values are:"})
    
    return message

def Return_Values(text,Qual_met,Quant_met,Fut_met,details):
    
    # Split the text by '\n'
    sections = [section for section in text.split('\n\n') if section.strip()]
    
    # Extract numerical values from parts after semicolon using regex
    qual_values = []
    quant_values = []
    fut_values = []    
    text_outputs = {}
    
    missing = [idx for idx,item in enumerate([Qual_met,Quant_met,Fut_met]) if not item]
    for miss in missing:
        sections.insert(miss,'')
    
    # Process each section
    for i, section in enumerate(sections):
        lines = section.strip().split('\n')
        
        if len(Qual_met) != 0 and i == 0:  
            # Extract numerical value for qualitative metrics
            for line in lines:
                match = re.search(r':.*?(\d+).*?/', line)
                if match:
                    qual_values.append(int(match.group(1)))      
        elif len(Quant_met) != 0 and i == 1:  
            # Extract numerical value for quantitative metrics
            for line in lines:
                match = re.search(r':.*?(\d+).*?#', line)
                if match:
                    quant_values.append(match.group(1))
        elif len(Fut_met) != 0 and i == 2:
            # Extract numerical value for future metrics
            for line in lines:
                match = re.search(r':.*?(\d+).*?#', line)
                if match:
                    fut_values.append(re.sub(r'(\S)-(\S)', r'\1 - \2', re.sub(r'[:#\s]', '', match.group())))
        else:
            # Store text past the colon and split by semicolon for details
            detail_index = len(details) - (len(sections) - i)
            if detail_index < 0: continue
            colon_split = section.split(':', 1)
            if len(colon_split) > 1:
                detail_text = colon_split[1].strip()
                text_outputs[details[detail_index]] = [re.sub(r'[:#]', '', item.strip()) for item in detail_text.split(';')]
            elif ':' not in section:
                detail_text = colon_split[0].strip()
                text_outputs[details[detail_index]] = [re.search(r'^(.*?)(?=#|$)', item.strip()).group() for item in detail_text.split(';')]
            else:
                text_outputs[details[detail_index]] = ["N/A"]

    # Check if we have the correct number of values
    if len(qual_values) != len(Qual_met) or len(quant_values) != len(Quant_met) or len(fut_values) != len(Fut_met):
        print("Warning: Mismatched length of output compared to inputted variables")
            
    return dict(zip(Qual_met, qual_values)), dict(zip(Quant_met, quant_values)), dict(zip(Fut_met, fut_values)), text_outputs


# List of articles obtained from fetch_articles.py
csv_input = 'Demo_articles.csv'

# Write results to CSV
csv_output = "Demo_results.csv"

# Key
key = os.environ.get("ANTHROPIC_API_KEY")

# Pre-set outputs to obtain from Claude (No need to change this)
Qualitative_Metrics = [
    "Novelty",
    "How niche is the topic?",
    "Public relevance",
    "Research Impact"
    ]

Quantitative_Metrics = [
    # "Population of research community for this topic"
    ]

Forecasted_Metrics = [
    "Conservative estimate for citations after 3 years"
    ]

Details = [
    "Summarize the abstract in three semicolon delimited sentences",
    "In a sentence explain what problem this research is trying to solve",
    "What research categories does this fall under, name four categories"
    ]

# Read all abstracts and titles from the CSV file
abstracts = []
titles = []
with open(csv_input, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['abstract']:  # Check if abstract is not empty
            abstracts.append(row['abstract'])
            titles.append(row['title'])

# Get results for each article
Results = []
for abstract in abstracts:
    article = {'abstract': abstract}
    output = Claude_Messager(key,Message_Builder(article,Qualitative_Metrics,Quantitative_Metrics,Forecasted_Metrics,Details))[0]
    Scores, Numbers, Predictions, Descriptions = Return_Values(output.text,Qualitative_Metrics,Quantitative_Metrics,Forecasted_Metrics,Details)
    
    # Create a dictionary with all the results
    result_dict = {
        'abstract': abstract,
        'scores': Scores,
        'predictions': Predictions,
        'descriptions': Descriptions
    }
    Results.append(result_dict)

# Get all unique keys from all dictionaries
all_keys = set()
for result in Results:
    for key, value in result.items():
        if isinstance(value, dict):
            all_keys.update(f"{key}_{subkey}" for subkey in value.keys())
        else:
            all_keys.add(key)

# Add 'title' to the beginning of the header
header = ['title'] + sorted(list(all_keys))

# Open the CSV file in write mode
with open(csv_output, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=header)

    # Write the header
    writer.writeheader()

    # Write the rows
    for result, title in zip(Results, titles):
        row = {'title': title}  # Add title to each row
        for key, value in result.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    row[f"{key}_{subkey}"] = subvalue
            else:
                row[key] = value
        writer.writerow(row)
