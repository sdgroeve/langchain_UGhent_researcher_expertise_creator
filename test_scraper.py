from paperscraper.pubmed import get_and_dump_pubmed_papers
q = ['Degroeve Sven','S Degroeve','S. Degroeve','Degroeve S.']
query = [q]


get_and_dump_pubmed_papers(query, output_filepath='test_scrape.jsonl')
