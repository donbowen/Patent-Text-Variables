# -*- coding: utf-8 -*-
"""
Needed to start:
    
1. data/patent_level_info/pat_dates_CURRENT.csv
2. data/patent_level_info/nber_CURRENT.csv
3. data/word_bags/word_index.csv
3. inputs/bad_ocr_words.csv

pip install mechanize
pip install tqdm
    
"""

import GPGutils 

#TODO add a DL function to ensure the needed files exist 

../data/patent_level_info/
../data/word_bags/descriptONLY/wordspace
../inputs/

GPGutils.update_pat_dates()     

GPGutils.update_pat_nber_class() 

# downloads GPG pages for pats in year, parses raw text if any new DLs found, 
# and cleans that raw text
GPGutils.update_bags(2010,2020) 

clean_bags(list(range(2010,2020+1)))  # delete once done

GPGutils.make_RETech('../outputs 2021/RETech.csv')  # RUN TO CHECK

GPGutils.make_breadth('../outputs 2021/Breadth.csv')      # TODO

GPGutils.ship_outputs(in1='../outputs 2021-11/RETech.csv',
                      in2='../outputs 2021-11/Breadth.csv',
                      out='../outputs 2021-11/Pat_text_vars.csv'
                      ) # merge and output