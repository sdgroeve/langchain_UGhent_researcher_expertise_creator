from langchain.llms import Ollama
import json

# Initialize Ollama LLM
llm = Ollama(model="llama3", temperature=0)

# Define a function to generate expertise descriptions
def generate_expertise_description(abstract):
    prompt = (
        f"Based on the following abstract, describe the expertise of the authors and any technology or software they used. "
        f"Make it concise, professional, and no longer than 80 words:\n\n"
        f"Abstract: {abstract}\n\n"
        f"Expertise:"
    )
    response = llm(prompt)
    return response.strip()

# Define a function to summarize expertise by researcher
def summarize_researcher_expertise(researcher, expertise_list):
    combined_expertise = "\n".join(expertise_list)
    prompt = (
        f"The following is a collection of expertise descriptions from publications associated with a researcher. "
        f"Create a cohesive, detailed, and professional summary of the researcher's expertise in no more than 150 words:\n\n"
        f"{combined_expertise}\n\n"
        f"Researcher's Expertise:"
    )
    response = llm(prompt)
    return response.strip()

# Load the JSON data
with open('test.publications_data.json', 'r') as file:
    data = json.load(file)

# Process each publication and group expertise by researcher
expertise_by_researcher = {}
for author, publications in data.items():
    expertise_by_researcher[author] = []
    for pub in publications:
        abstract = pub.get("abstract", "")
        if abstract:
            expertise = generate_expertise_description(abstract)
            pub["expertise"] = expertise
            # Add the expertise for this paper to the author's group
            expertise_by_researcher[author].append(expertise)

# Generate a detailed expertise description for each researcher
final_expertise_by_researcher = {}
for researcher, expertise_list in expertise_by_researcher.items():
    if expertise_list:
        final_expertise_by_researcher[researcher] = summarize_researcher_expertise(researcher, expertise_list)

# Save the final expertise descriptions to a new JSON file
with open('test.publications_data_expertise_summary.json', 'w') as file:
    json.dump(final_expertise_by_researcher, file, indent=4)

# Save the updated publications data with individual expertise descriptions
with open('test.publications_data_expertise.json', 'w') as file:
    json.dump(data, file, indent=4)

print("Final expertise descriptions generated and saved successfully.")
