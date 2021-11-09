Static inputs (no need to update)

1. pat_dates_pre_2013.dta - Assembled for Bowen, Fresard and Hoberg 2021.
2. bad_ocr_words.csv - Assembled for Bowen, Fresard and Hoberg 2021.
	- Will keep static for backward compatibility because updating will alter set of stopwords.
	- Constructed with "make_bad_ocr.py" which won't work on any computer except mine due to needed input files. Keeping here for documentation.
3. withdrawn.txt - from USPTO. Not used except in a check. 

Dynamic input - **need to update to add new years**
	
1. patent.tsv.zip - From PatentsView
2. application.tsv.zip - From PatentsView
