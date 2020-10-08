from collections import Counter
from IPython.display import clear_output, display 
import itertools
import ipywidgets as widgets
import json
import matplotlib.pyplot as plt
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.util import ngrams, everygrams
import numpy as np
import re
from urllib.error import HTTPError
from wordcloud import WordCloud
from .pmq import PubMedQuery

class App(object):

    def __init__(self):

        with open('utils/stopWords.json', encoding="utf8") as json_file:
            self.stopWords = json.load(json_file)['words']

        self.search_ids = []

        self.raw_data = []
        self.cleanedData = []

        self.cleanedData = []
        self.authors_cloud_words = []
        self.title_cloud_words = []
        self.journal_cloud_words = []
        self.abstract_cloud_words = []
        self.result_cloud_words = []
        self.publication_year_cloud_words = []
        self.keyword_cloud_words = []
        self.conclusion_cloud_words = []
        self.publication_cloud_words = []
        self.overal_cloud_words = []

        self.min_grams = widgets.IntSlider(
            value=2,
            min=1,
            max=3,
            step=1,
            description='Min Grams:',
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
            layout=widgets.Layout(width='auto', grid_area='min_grams'),
        )

        self.max_grams = widgets.IntSlider(
            value=5,
            min=3,
            max=5,
            step=1,
            description='Max Grams:',
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
            layout=widgets.Layout(width='auto', grid_area='max_grams'),
        )

        self.top_journals = widgets.IntSlider(
            value=10,
            min=3,
            max=50,
            step=1,
            description='Top Journals:',
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
            layout=widgets.Layout(width='auto', grid_area='top_journals'),
        )

        self.long_grams_weight = widgets.Checkbox(
            value=True,
            description='Long Gram Weight',
            disabled=False,
            indent=False
        )

        self.ignore_incomplete_author_names = widgets.Checkbox(
            value=True,
            description='Remove incomplete author names',
            disabled=False,
            indent=False
        )

        self.remove_isolated_numbers = widgets.Checkbox(
            value=True,
            description='Remove Isolated Numbers',
            disabled=False,
            indent=False
        )

        self.output = widgets.Output()

        self.cloud_size = widgets.IntSlider(
            value=100,
            min=10,
            max=200,
            step=1,
            description='Cloud Size:',
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
            layout=widgets.Layout(width='auto', grid_area='cloud_size'),
        )

        self.email_field = widgets.Text(
            value='peter.just@intonumbers.com',
            placeholder='enter your email',
            layout=widgets.Layout(width='auto', grid_area='email_field'),
        )

        self.generate_graphs_button  = widgets.Button(description='GENERATE GRAPHS',
                 layout=widgets.Layout(width='auto', grid_area='generate_graphs_button'),
                 style=widgets.ButtonStyle(button_color='lightblue'))

        self.max_results = widgets.IntSlider(
            value=10,
            min=1,
            max=500,
            step=1,
            description='Max Results:',
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
            layout=widgets.Layout(width='auto', grid_area='max_results'),
        )
        
        self.search_ids_button  = widgets.Button(description='SEARCH FOR ID(s)',
                 layout=widgets.Layout(width='auto', grid_area='search_ids_button'),
                 style=widgets.ButtonStyle(button_color='lightblue'))
        
        self.search_ids_field = widgets.Textarea(
            value='',
            placeholder='enter PubMed IDs (comma seperated)',
            layout=widgets.Layout(width='auto', height="200px", grid_area='search_ids_field'),
        )
        
        self.search_term_button  = widgets.Button(description='SEARCH FOR TERM(s)',
                 layout=widgets.Layout(width='auto', grid_area='search_term_button'),
                 style=widgets.ButtonStyle(button_color='lightblue'))

        self.search_term_field = widgets.Textarea(
            value=self.stringify_search_ids(),
            placeholder='enter search term',
            layout=widgets.Layout(width='auto', height="200px", grid_area='search_term_field'),
        )

        self.ignore_words_field = widgets.Textarea(
            value='',
            placeholder='enter ignore words (comma seperated)',
            layout=widgets.Layout(width='auto', height="250px", grid_area='ignore_words_field'),
        )

        self.control_box = widgets.GridBox(children=[
            self.cloud_size,
            self.long_grams_weight,  
            self.ignore_incomplete_author_names,  
            self.max_grams,
            self.min_grams, 
            self.remove_isolated_numbers,
            self.top_journals,  
            ],
            layout=widgets.Layout(
                width='200%',
                grid_template_rows='auto',
                grid_template_columns='1fr',
                grid_template_areas='''
                "cloud_size"
                "min_grams"
                "max_grams"
                "top_journals"
                "long_grams_weight"
                ''')
        )

        self.search_box = widgets.GridBox(children=[
            self.email_field,
            self.max_results,
            self.search_ids_button, 
            self.search_ids_field,
            self.search_term_button, 
            self.search_term_field
            ],
            layout=widgets.Layout(
                width='90%',
                grid_template_rows='auto',
                grid_template_columns='1fr 1fr 1fr 1fr',
                grid_template_areas='''
                "email_field email_field max_results max_results"
                "search_ids_field search_ids_field search_term_field search_term_field"
                "search_ids_button search_ids_button search_term_button search_term_button"
                "ignore_words_field ignore_words_field . ."
                ''')
        )

        self.cloud_box = widgets.GridBox(children=[
            self.control_box,
            self.generate_graphs_button,
            self.ignore_words_field,
            ],
            layout=widgets.Layout(
                width='90%',
                grid_template_rows='auto',
                grid_template_columns='1fr 1fr 1fr 1fr',
                grid_template_areas='''
                "ignore_words_field ignore_words_field control_box control_box"
                "generate_graphs_button generate_graphs_button generate_graphs_button generate_graphs_button "
                ''')
        )

        self.generate_graphs_button.on_click(self.generate_graphs_button_clicked)
        self.search_ids_button.on_click(self.search_ids_button_clicked)
        self.search_term_button.on_click(self.search_term_button_clicked)
        
        display(self.search_box, self.output)
        
    def generate_graphs_button_clicked(self, generate_graphs_button):
        with self.output:
            clear_output()
            
            print('Downloaded publications based on your search term: {}'.format(len(self.raw_data)))
            display(self.cloud_box)

            self.clean_data()
            self.generate_wordclouds()
            
    def search_ids_button_clicked(self, search_ids_button):
        self.raw_data = []
        with self.output:
            clear_output()
            print('Downloading data')
            pmq = PubMedQuery(email=self.email_field.value)


            results = pmq.query_ids(id_string=self.search_ids_field.value)


            try:
                for article in results:
                    self.raw_data.append(article.toJSON()) 
            except:
                clear_output()
                print('Please provide valid PubMedIDs')
                return None

            clear_output()
            print('Downloaded publications based on your search term: {}'.format(len(self.raw_data)))
            display(self.cloud_box)
    
    def search_term_button_clicked(self, search_term_button):
        self.raw_data = []
        with self.output:
            clear_output()
            print('Downloading data')

            pmq = PubMedQuery(email=self.email_field.value)
            
            try:
                results = pmq.query(query=self.search_term_field.value, max_results=self.max_results.value)
            except:
                clear_output()
                print('Please provide a search term')
                return None

            for article in results:
                self.raw_data.append(article.toJSON()) 

            clear_output()
            print('Downloaded publications based on your search term: {}'.format(len(self.raw_data)))
            display(self.cloud_box)
    
    def stringify_search_ids(self):
        return ', '.join(self.search_ids)
    
    def listify_search_ids(self):
        return self.search_ids_field.value.replace(' ', '').replace('\n', '').split(',')

    def _clean_text(self, ct_text):

        if ct_text:
            ct_text_list = ct_text.split()
            ct_cleaned_text_list = []

            for ct_element in ct_text_list:
                if self.remove_isolated_numbers.value:
                    ct_element = re.sub(r"\b(\d+|[a-z])\b *","",ct_element)
                ct_element = re.sub('[^a-zA-Z0-9 .,]|(?<!\\d)[.,]|[.,](?!\\d)', '', ct_element)
                ct_element = ct_element.replace(' ', '')

                if ct_element is not '':
                    ct_cleaned_text_list.append(ct_element.lower())

            return ' '.join(ct_cleaned_text_list)
        return ''

    def _remove_stopwords(self, rs_text):

        rs_text_list = rs_text.split()
        rs_cleaned_text_list = []

        for rs_element in rs_text_list:
            if rs_element.lower() not in self.stopWords:
                rs_cleaned_text_list.append(rs_element)

        return ' '.join(rs_cleaned_text_list)

    def _stem_text(self, st_text):

        stemmer = WordNetLemmatizer()

        st_text_list = st_text.split()
        st_cleaned_text_list = []

        for st_element in st_text_list:
            st_cleaned_text_list.append(stemmer.lemmatize(st_element))
        
        return ' '.join(st_cleaned_text_list)

    def _underscore_join(self, uj_text):
        return '_'.join(uj_text.split())

    def _tokenize_authors(self, t_authors):
        cleaned_authors = []

        if type(t_authors) is list:
            for t_author in t_authors:
                firstname = ''
                lastname = ''
                if 'firstname' in t_author and t_author['firstname']:
                    firstname = t_author['firstname'].replace(' ', '_')
                    firstname = firstname.replace('-', '_')
                if 'lastname' in t_author and t_author['lastname']:
                    lastname = t_author['lastname'].replace(' ', '_')
                    lastname = lastname.replace('-', '_')

                if self.ignore_incomplete_author_names.value:
                    if firstname != '' and lastname != '':
                        complete_name = (firstname + '_' + lastname).lower()
                        cleaned_authors.append(complete_name)

                else: 
                    cleaned_authors.append((firstname + '_' + lastname).lower())

            return ' '.join(cleaned_authors)

        return ''

    def _tokenice(self, t_text):
        nltk_tokens = word_tokenize(t_text)
        every_gram_list = list(everygrams(nltk_tokens, min_len=self.min_grams.value, max_len=self.max_grams.value))
        return(every_gram_list)

    def _validate_mail(self, mail):  
            if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', mail)):  
                return(mail)       
            else:  
                raise Exception("Please enter a valid Mailadress in the Config Section (first cell)")

    def _data_process(self, dp_text):

        dp_text = self._clean_text(dp_text)
        dp_text = self._remove_stopwords(dp_text)
        dp_text = self._stem_text(dp_text)
        dp_text = self._tokenice(dp_text)
        dp_text = ['_'.join(w) for w in dp_text]

        return dp_text

    def _keywords_process(self, kp_list):

        cleaned_keywords = []

        for keyword_phrase in kp_list:
            keyword_phrase = self._clean_text(keyword_phrase)
            keyword_phrase = self._remove_stopwords(keyword_phrase)
            keyword_phrase = self._stem_text(keyword_phrase)

            cleaned_keywords.append(keyword_phrase.replace(' ', '_'))

        return(cleaned_keywords)

    def _long_gram_weight(self, lgw_list):
        weight_list = []

        for lgw_entry in lgw_list:
            weight = len(lgw_entry.split('_'))
            for _ in itertools.repeat(None, weight):
                weight_list.append(lgw_entry)
        
        return(weight_list)

    def generate_wordcloud(self, cloud_words):
        if len(cloud_words) > 0:
            wordcloud = WordCloud(max_words=self.cloud_size.value, width=900, height=600, background_color="white", collocations=False).generate(cloud_words)
            plt.figure(figsize = (15, 10), facecolor = None)
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis("off")
            plt.show()
        else:
            print('no words for printing wordcloud')
    
    def generate_wordclouds(self):
        print('\n')
        print('Overall Wordcloud:')
        self.generate_wordcloud(self.overal_cloud_words)

        print('\n')
        print('Publication Wordcloud:')
        self.generate_wordcloud(self.publication_cloud_words)

        print('\n')
        print('Authors Wordcloud:')
        self.generate_wordcloud(self.authors_cloud_words)

        print('\n')
        print('Conclusion Wordcloud:')
        self.generate_wordcloud(self.conclusion_cloud_words)

        print('\n')
        print('Keyword Wordcloud:')
        self.generate_wordcloud(self.keyword_cloud_words)

        print('\n')
        print('Journal Barchart:')
        self.generate_journal_chart(self.journal_cloud_words)

        print('\n')
        print('Publication Year Chart:')
        self.generate_publication_year_chart(self.publication_year_cloud_words)

    def generate_journal_chart(self, ch_authors):

        journal_list = []
        frequency_list = []
        most_common_journals = Counter(ch_authors.split()).most_common(self.top_journals.value)

        for entry in most_common_journals:
            journal_list.append(entry[0].replace('_', ' '))
            frequency_list.append(entry[1])
        
        objects = tuple(list(reversed(journal_list))) 
        y_pos = np.arange(len(objects))
        performance = list(reversed(frequency_list))

        plt.barh(y_pos, performance, align='center', alpha=0.8)
        plt.yticks(y_pos, objects)
        fig = plt.gcf()
        fig.set_size_inches(15, 10, forward=True)

        plt.show()

    def generate_publication_year_chart(self, ch_years):

        ch_years = ' '.join(sorted(str(ch_years).split()))
        year_list = []
        frequency_list = []

        history = Counter(ch_years.split()).items()

        for entry in history:
            year_list.append(entry[0])
            frequency_list.append(entry[1])
        
        objects = tuple(list(year_list)) 
        y_pos = np.arange(len(objects))
        performance = list(frequency_list)

        plt.bar(y_pos, performance, align='center', alpha=0.8)
        plt.xticks(y_pos, objects)
        fig = plt.gcf()
        fig.set_size_inches(15, 10, forward=True)

        plt.show()
    
    def _remove_ignorewords(self, ri_list):

        ignore_words = self.ignore_words_field.value.replace(' ', '').replace('\n', '').split(',')

        ri_cleaned_list = []

        for ri_element in ri_list:
            if ri_element not in ignore_words:
                ri_cleaned_list.append(ri_element)

        return ri_cleaned_list
    
    def clean_data(self):

        self.cleanedData = []
        self.authors_cloud_words = []
        self.title_cloud_words = []
        self.journal_cloud_words = []
        self.abstract_cloud_words = []
        self.result_cloud_words = []
        self.publication_year_cloud_words = []
        self.keyword_cloud_words = []
        self.conclusion_cloud_words = []
        self.publication_cloud_words = []
        self.overal_cloud_words = []

        for entry in self.raw_data:

            pubmed_id = ''
            title = ''
            journal = ''
            authors = ''
            abstract = ''
            results = ''
            keywords = ''
            conclusions = ''
            publication_date = ''
            publication_year = ''
            title_tokens = ''
            abstract_tokens = ''
            keyword_tokens = ''
            author_tokens = ''
            result_tokens = ''
            conclusion_tokens = ''

            key_list = []

            # ToDo: delete TestPrint
            for key, value in json.loads(entry).items():
                key_list.append(key)

            if 'pubmed_id' in key_list:
                pubmed_id = json.loads(entry)['pubmed_id']
            if 'title' in key_list:  
                title = json.loads(entry)['title']
                title_tokens = self._data_process(title)
            if 'journal' in key_list:
                journal = self._underscore_join(json.loads(entry)['journal'])
            if 'authors' in key_list:
                authors = json.loads(entry)['authors']
                author_tokens = self._tokenize_authors(authors) 
            if 'abstract' in key_list:
                abstract = json.loads(entry)['abstract'] 
                abstract_tokens = self._data_process(abstract)
            if 'results' in key_list:
                results = json.loads(entry)['results'] 
                result_tokens = self._data_process(results)
            if 'keywords' in key_list:
                keywords = json.loads(entry)['keywords'] 
                keyword_tokens = self._keywords_process(keywords)
            if 'conclusions' in key_list:
                conclusions = json.loads(entry)['conclusions'] 
                conclusion_tokens = self._data_process(conclusions)
            if 'publication_date' in key_list:
                publication_date = json.loads(entry)['publication_date']
                publication_year = json.loads(entry)['publication_date'].split('-')[0]
            
            self.cleanedData.append({
                'pmid': pubmed_id,
                "title": title,
                "authors": authors,
                "journal": journal,
                "abstract": abstract,
                "results": results,
                "keywords": keywords,
                "conclusions": conclusions,
                "publication_date": publication_date,
                "publication_year": publication_year,
                "title_tokens": title_tokens,
                "abstract_tokens": abstract_tokens,
                "keyword_tokens": keyword_tokens,
                "author_tokens": author_tokens,
                "result_tokens": result_tokens,
                "conclusion_tokens": conclusion_tokens,
            })


        authors_list = []
        title_list = []
        journal_list = []
        abstract_list = []
        result_list = []
        publication_year_list = []
        keyword_list = []
        conclusion_list = []

        publication_list = []
        overall_list = []

        for c_entry in self.cleanedData:
            authors_list.append(c_entry['author_tokens'])
            title_list.append(list(set(c_entry['title_tokens'])))
            journal_list.append(c_entry['journal'])
            abstract_list.append(list(set(c_entry['abstract_tokens'])))
            result_list.append(list(set(c_entry['result_tokens'])))
            publication_year_list.append(c_entry['publication_year'])
            keyword_list.append(list(set(c_entry['keyword_tokens'])))
            conclusion_list.append(list(set(c_entry['conclusion_tokens'])))

            temp_publication_list = []
            temp_publication_list.append(list(set(c_entry['title_tokens'])))
            temp_publication_list.append(list(set(c_entry['abstract_tokens'])))
            temp_publication_list.append(list(set(c_entry['result_tokens'])))
            temp_publication_list.append(list(set(c_entry['keyword_tokens'])))
            temp_publication_list.append(list(set(c_entry['conclusion_tokens'])))

            publication_list.append(sum(temp_publication_list, []))

            if len(c_entry['title_tokens']) > 0:
                overall_list.append(c_entry['title_tokens'])
            if len(c_entry['abstract_tokens']) > 0:
                overall_list.append(c_entry['abstract_tokens'])
            if len(c_entry['result_tokens']) > 0:
                overall_list.append(c_entry['result_tokens'])
            if len(c_entry['keyword_tokens']) > 0:
                overall_list.append(c_entry['keyword_tokens'])
            if len(c_entry['conclusion_tokens']) > 0:
                overall_list.append(c_entry['conclusion_tokens'])


        title_list = sum(title_list, [])
        abstract_list = sum(abstract_list, [])
        result_list = sum(result_list, [])
        keyword_list = sum(keyword_list, [])
        conclusion_list = sum(conclusion_list, [])
        publication_list = sum(publication_list, [])
        overall_list = sum(overall_list, [])

        title_list = self._remove_ignorewords(title_list)
        authors_list = self._remove_ignorewords(authors_list)
        abstract_list = self._remove_ignorewords(abstract_list)
        result_list = self._remove_ignorewords(result_list)
        keyword_list = self._remove_ignorewords(keyword_list)
        conclusion_list = self._remove_ignorewords(conclusion_list)
        publication_list = self._remove_ignorewords(publication_list)
        overall_list = self._remove_ignorewords(overall_list)

        if self.long_grams_weight.value:
            title_list = self._long_gram_weight(title_list)
            abstract_list = self._long_gram_weight(abstract_list)
            result_list = self._long_gram_weight(result_list)
            conclusion_list = self._long_gram_weight(conclusion_list)
            publication_list = self._long_gram_weight(publication_list)
            overall_list = self._long_gram_weight(overall_list)

        self.authors_cloud_words = ' '.join(authors_list)
        self.title_cloud_words = ' '.join(title_list)
        self.journal_cloud_words = ' '.join(journal_list)
        self.abstract_cloud_words = ' '.join(abstract_list)
        self.result_cloud_words = ' '.join(result_list)
        self.publication_year_cloud_words = ' '.join(publication_year_list)
        self.keyword_cloud_words = ' '.join(keyword_list)
        self.conclusion_cloud_words = ' '.join(conclusion_list)
        self.publication_cloud_words = ' '.join(publication_list)
        self.overal_cloud_words = ' '.join(overall_list)


    


