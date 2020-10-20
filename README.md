# PubMed Insights
A Jupyter notebook for creating word-clouds based on titles, abstracts, keywords, results, authors, and conclusions from Pubmed publications.

## Installation

    pip install -r requirements.txt

## Quick Guide

1. run the code cell and wait until the user interface appears

2. enter your email address (reqired for PubMed)

3. execute your search
    - you can search for specific PubMed IDs (comma seperated), eg: 31351196, 29782946, 27019357
    - or query for a search term ("Max Results" defines them maximum number of downloaded publications based on your search term)
4. after clicking "search for ..." you can change the folowing settings for your visualization:
    - **Ignore Words:** here you can exclude terms from your visualization (comma seperated, word combinations have to be combined with "_"), eg: cancer, bone_cancer, cancer_patient. 
    - **Cloud Size:** how many terms appear in the word-clouds
    - **Min Grams & Max Grams:** the minimum and maximum number of grams to which the visualized terms correspond ("cancer" = 1-gram, "bone_cancer" = 2-gram, etc)
    - **Top Jpurnals:** the number of journals which appear in the "most frequent journals" graph
    - **Long Gram Weight:** defines if terms with more words should be weighted higher in the wordclouds
    - **Remove Incomplete Author Names:** defines if authors with missing given- or family-names should appear in the author wordcloud
    - **Remove Isolated Numbers:** defines if numbers should be ignored for the visualization

5. click "GENERATE GRAPHS"
    - **IMPORTANT:** if you only want to change any visualization settings, you don't have to repeat your search, just change the desired parameters and re-generate the grpahs. 

6. Visualization description:
    - **Overall Wordcloud:** represents the frequency of each term
    - **Publication Wordcloud:** represents the frequency of publications each term is found in
    - **Authors Wordcloud:** represents the frequency of authors
    - **Conclusion Wordcloud:** represents the frequency of terms found in the publications "conclusion" section
    - **Keyword Wordcloud:** represents the frequency of terms found in the publications "keywords" section
    - **Journal Barchart:** represents the journal distribution of the queried publications
    - **Publication Year Chart:** represents the publication year distribution of the queried publications

## Credits & special thanks
Dr. Georg Feichtinger 
- for inspiration and testing

Gijs Wobben 
- for his pymed library, which was a great foundation for my PubMed queries 
- https://github.com/gijswobben/pymed

## Notice of Non-Affiliation and Disclaimer
The author of this notebook is not affiliated, associated, authorized, endorsed by, or in any way officially connected with PubMed, or any of its subsidiaries or its affiliates. The official PubMed website can be found at https://www.ncbi.nlm.nih.gov/pubmed/.