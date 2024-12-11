import requests
import urllib.parse

# Define the input and output file paths
input_file = "hint.researchers.txt"  # Text file containing researcher names (one per line)
log_file = "invalid_urls.log"


def construct_urls(name):
    """Constructs multiple potential URLs for a researcher given their name."""
    base_url = "https://research.ugent.be/web/person/"

    # Remove unnecessary parts like parentheses and their contents
    name = name.split("(")[0].strip()

    # Split the name into parts
    parts = name.split()
    urls = []

    # Construct URLs by combining name parts without spaces
    combined_name = "".join(parts).lower()
    urls.append(f"{base_url}{combined_name}-0/en")

    # Construct URLs by testing different orderings and combinations
    if len(parts) > 1:
        # First name-last name
        urls.append(f"{base_url}{parts[-1].lower()}-{'-'.join(parts[:-1]).lower()}-0/en")
        # Last name-first name
        urls.append(f"{base_url}{'-'.join(parts[:-1]).lower()}-{parts[-1].lower()}-0/en")
    # Single part name
    urls.append(f"{base_url}{parts[0].lower()}-0/en")

    sanitized_urls = []
    for url in urls:
        sanitized_url = url
        replacements = {
            " ": "-",
            "\u00fc": "u",
            "\u00e9": "e",
            "\u00f6": "o",
            "\u011f": "g",
            "\u00e7": "c",
            "\u0131": "i",
            "\u00e2": "a",
            "\u00fb": "u",
        }
        for original, replacement in replacements.items():
            sanitized_url = sanitized_url.replace(original, replacement)
        sanitized_urls.append(urllib.parse.quote(sanitized_url, safe="/:"))

    return sanitized_urls


def check_url_exists(url):
    """Checks if a URL exists by sending a HEAD request."""
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def main():
    invalid_urls = []

    # Read the names from the input file
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            names = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
        return

    # Process each name
    for name in names:
        possible_urls = construct_urls(name)
        valid = False
        for url in possible_urls:
            if check_url_exists(url):
                valid = True
                break

        if not valid:
            invalid_urls.append((name, possible_urls))

    # Write invalid URLs and tested URLs to the log file
    if invalid_urls:
        with open(log_file, "w", encoding="utf-8") as log:
            log.write("The following names had no valid URLs. Tested URLs are listed below:\n")
            for name, urls in invalid_urls:
                log.write(f"Name: {name}\n")
                log.write("Tested URLs:\n")
                for url in urls:
                    log.write(f"  {url}\n")
                log.write("\n")

        print(f"Invalid URLs have been logged to '{log_file}'.")
    else:
        print("All URLs were constructed and verified successfully.")


if __name__ == "__main__":
    main()
