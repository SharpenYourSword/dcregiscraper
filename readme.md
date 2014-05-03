# DCRegiScraper

An application, written in Python, powered by ElasticSearch, and served with Flask for the simple purpose of actually giving a text searchable DC Register.

## The Goal

1. Get each of the PDFs of the DC Register [organized by year](http://dcregs.dc.gov/Gateway/IssueList.aspx?IssueYear=2013)
2. Convert the PDFs into text files
3. Take the text files and load them into ElasticSearch
4. Basic REST API to query by date and by keyword