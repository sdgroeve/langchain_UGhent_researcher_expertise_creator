import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
import unicodedata

def clean_html(text):
    """Remove HTML tags and clean up whitespace."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_name(name):
    """Normalize the researcher's name to create a valid URL."""
    print(f"  Original name: {name}")
    
    # Remove titles and degrees in parentheses
    name = re.sub(r'\s*\([^)]*\)', '', name)
    name = re.sub(r'\s*(MD|PhD|DVM|prof\.|dr\.|Prof\.|Dr\.)\s*', ' ', name.lower())
    
    # Normalize unicode characters
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '-', name.strip())
    
    print(f"  Normalized name: {name}")
    return name

def get_research_profile_urls(name):
    """Generate possible research.ugent.be profile URLs for a name."""
    base_name = normalize_name(name)
    
    # Generate variations of the URL
    variations = []
    
    # Basic variations
    base_variations = [
        base_name,
        f"{base_name}-0",
        f"{base_name}--0",
        f"{base_name}-1",
        f"{base_name}--1"
    ]
    
    # For each base variation, create a URL
    for var in base_variations:
        variations.append(f"https://research.ugent.be/web/person/{var}/en")
    
    # Handle names with dashes
    if '-' in base_name:
        # Try without the last part of the name
        parts = base_name.split('-')
        shortened_name = '-'.join(parts[:-1])
        variations.extend([
            f"https://research.ugent.be/web/person/{shortened_name}/en",
            f"https://research.ugent.be/web/person/{shortened_name}-0/en"
        ])
        
        # Try with spaces instead of dashes
        space_version = base_name.replace('-', ' ')
        variations.extend([
            f"https://research.ugent.be/web/person/{space_version}/en",
            f"https://research.ugent.be/web/person/{space_version}-0/en"
        ])
    
    # Try first initial + last name pattern
    if '-' in base_name:
        parts = base_name.split('-')
        if len(parts) >= 2:
            first_initial = parts[0][0] if parts[0] else ''
            last_name = parts[-1]
            initial_version = f"{first_initial}-{last_name}"
            variations.extend([
                f"https://research.ugent.be/web/person/{initial_version}/en",
                f"https://research.ugent.be/web/person/{initial_version}-0/en"
            ])
    
    print("  Attempting URLs:")
    for url in variations:
        print(f"    {url}")
    
    return variations

def get_publications_url(profile_url):
    """Convert profile URL to publications URL."""
    return profile_url.replace('/en', '/publications/en')

def scrape_researcher_details(name):
    """Scrape details from a researcher's profile page."""
    print(f"\nAttempting to find profile for: {name}")
    urls = get_research_profile_urls(name)
    details = {}
    profile_url = None
    
    # Try each possible URL
    for url in urls:
        try:
            response = requests.get(url, timeout=15)  # Increased timeout
            if response.status_code == 200:
                profile_url = url
                print(f"  ✓ Success: {url}")
                break
            elif response.status_code == 404:
                print(f"  ✗ Not found (404): {url}")
            elif response.status_code == 500:
                print(f"  ✗ Server error (500): {url}")
            else:
                print(f"  ✗ Failed ({response.status_code}): {url}")
            time.sleep(1)  # Increased delay between attempts
        except requests.RequestException as e:
            print(f"  ✗ Error: {url} - {str(e)}")
            time.sleep(1)
            continue
    
    if not profile_url:
        print(f"  ! No working profile URL found for {name}")
        return {}
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract research disciplines
        disciplines_div = soup.find('div', {'id': 'id23'})
        if disciplines_div:
            disciplines = set()
            for li in disciplines_div.find_all('li'):
                normal_span = li.find('span', class_='normal')
                if normal_span:
                    discipline_name = normal_span.text.strip()
                    if discipline_name:
                        disciplines.add(discipline_name)
            
            if disciplines:
                details['research_disciplines'] = list(disciplines)
                print(f"  Found {len(disciplines)} research disciplines")

        # Extract expertise
        expertise_div = soup.find('div', {'id': 'id24'})
        if expertise_div:
            keywords_div = expertise_div.find('div', class_='keywords')
            if keywords_div:
                expertise = []
                for keyword in keywords_div.find_all('span', class_='keyword-label'):
                    if keyword.text.strip():
                        expertise.append(keyword.text.strip())
                
                if expertise:
                    details['expertise'] = expertise
                    print(f"  Found {len(expertise)} expertise keywords")

        # Scrape publications
        publications_url = get_publications_url(profile_url)
        try:
            publications_response = requests.get(publications_url, timeout=15)
            if publications_response.status_code == 200:
                publications_soup = BeautifulSoup(publications_response.text, 'html.parser')
                
                publications = []
                current_year = datetime.now().year
                cutoff_year = current_year - 7  # Last 7 years
                
                processed_titles = set()
                
                year_sections = publications_soup.find_all('div', class_='margin-bottom-gl')
                
                for section in year_sections:
                    year_header = section.find('div', class_='header-5')
                    if not year_header:
                        continue
                    
                    try:
                        year = int(year_header.find('span').text.strip())
                        if year < cutoff_year:
                            continue
                        
                        pubs_container = section.find('div', style='margin-left: 4em;')
                        if not pubs_container:
                            continue
                        
                        for pub_div in pubs_container.find_all('div', class_='bg-blue-hover'):
                            title_span = pub_div.find('span', {'data-type': 'title'})
                            if not title_span:
                                continue
                            
                            title = title_span.text.strip()
                            if title in processed_titles:
                                continue
                            processed_titles.add(title)
                            
                            publications.append(title)
                            
                    except (ValueError, AttributeError):
                        continue

                if publications:
                    details['publications'] = publications
                    print(f"  Found {len(publications)} publications")
                    
        except requests.RequestException as e:
            print(f"  Error fetching publications: {str(e)}")

    except Exception as e:
        print(f"  Error processing profile: {str(e)}")

    return details

def main():
    # Load HTML from the CRIG URL
    url = 'https://www.crig.ugent.be/en/all-crig-group-leaders-and-members'
    print(f"Fetching CRIG members from {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all researcher profile links
        researchers = []
        for node in soup.find_all('div', class_='node-partner'):
            link = node.find('a', class_='field-group-link')
            if link:
                img_tag = node.find('img')
                if img_tag and 'alt' in img_tag.attrs:
                    name = img_tag['alt']
                    profile_url = link['href']
                    if not profile_url.startswith('http'):
                        profile_url = 'https://www.crig.ugent.be' + profile_url
                    researchers.append({'name': name, 'profile_url': profile_url})

        # Parse the additional researcher list
        additional_section = soup.find('div', class_='field--name-field-rich-text')
        if additional_section:
            for li in additional_section.find_all('li'):
                link = li.find('a')
                if link:
                    name = link.text.strip()
                    profile_url = link['href']
                    if not profile_url.startswith('http'):
                        profile_url = 'https://www.crig.ugent.be' + profile_url
                    researchers.append({'name': name, 'profile_url': profile_url})

        print(f"\nFound {len(researchers)} researchers")
        
        # Extract detailed information from each researcher's profile
        for researcher in researchers:
            print(f"\nProcessing {researcher['name']}...")
            
            # Get CRIG profile info
            profile_url = researcher['profile_url']
            try:
                profile_response = requests.get(profile_url, timeout=15)
                profile_response.raise_for_status()
                
                profile_soup = BeautifulSoup(profile_response.text, 'html.parser')

                # Extract description from meta tag
                description_tag = profile_soup.find('meta', {'name': 'description'})
                if description_tag and description_tag['content']:
                    description = description_tag['content'].strip()
                    if description:
                        researcher['description'] = description
                        print("  Found description")

                # Extract research focus
                research_focus_header = profile_soup.find('h2', string='Research focus')
                if research_focus_header:
                    focus_div = research_focus_header.find_next('div', class_='group-right')
                    if focus_div:
                        focus_items = focus_div.find_all('li')
                        research_focus_list = [item.get_text(strip=True) for item in focus_items]
                        if research_focus_list:
                            researcher['research_focus'] = research_focus_list
                            print(f"  Found {len(research_focus_list)} research focus items")

            except requests.RequestException as e:
                print(f"  Error fetching CRIG profile: {str(e)}")

            # Get research.ugent.be profile info
            try:
                details = scrape_researcher_details(researcher['name'])
                researcher.update(details)
            except Exception as e:
                print(f"  Error fetching research profile: {str(e)}")

            # Rate limiting
            time.sleep(2)  # Increased delay between researchers

        # Save the JSON data
        with open('researchers_crig.json', 'w', encoding='utf-8') as f:
            json.dump(researchers, f, indent=2, ensure_ascii=False)

        print("\nScraping completed. Data saved to researchers_crig.json")

    except requests.RequestException as e:
        print(f"Error fetching CRIG members: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
