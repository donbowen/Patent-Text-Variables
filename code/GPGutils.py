# -*- coding: utf-8 -*-
"""
Change log: 
    2023: update_bags split up for easier maintenance in future (dl, parse, clean)
    
Download during 2023:
     patents view updated URLS, variable names, and other things. for example, 
     no country variable in applications now. 
"""

def set_up_onetime():
    '''
    Sets up the directory struture and gets the files you need where you need
    them!
    
    Downloads four files:

    1. `bad_ocr_words.csv` 
    	- Words that only exist in the patent corpus before 1976, assumed to be 
          bad OCR words, and will drop from corpus.
    	- Assembled for Bowen, Fresard and Hoberg Forthcoming.
    	- Will keep static for backward compatibility because updating will 
          alter set of stopwords.
    2. `nber_CURRENT.csv` - the nber 1 digit code for patents
    3. `pat_dates_CURRENT.csv` - the nber 1 digit code for patents
    4. `word_index.csv` - words found in patents, and a corresponding integer 
        (the "word_index") representing that word 
    	
    The first file will never change. After you use the code to update the 
    patent corpus, the other three files will update as well.
    '''
    
    import os
    import urllib.request 
    import zipfile

    url = 'https://github.com/donbowen/Patent-Text-Variables/releases/download/Pat_Text_Vars_StarterInputs/Pat_Text_Vars_StarterInputs.zip'    
    
    if not os.path.exists('../data/word_bags/'): # don't run if we've already downloaded!
    
        # set up directory structure
        os.makedirs('../data/patent_level_info/',exist_ok=True)
        os.makedirs('../data/word_bags/descriptONLY/wordspace',exist_ok=True)
        os.makedirs('../inputs/',exist_ok=True)    
        
        # download zip
        print('Downloading initial word_index and other large inputs...')
        urllib.request.urlretrieve(url, "inputs.zip")    
    
        # extract and place files
        with zipfile.ZipFile("inputs.zip","r") as zip_ref:
            zip_ref.extract("bad_ocr_words.csv",     path='../inputs/')
            zip_ref.extract("word_index.csv",        path='../data/word_bags/')
            zip_ref.extract("nber_CURRENT.csv",      path='../data/patent_level_info/')
            zip_ref.extract("pat_dates_CURRENT.csv", path='../data/patent_level_info/')
    
        # delete the zip download
        
        os.remove("inputs.zip")


def update_pat_dates(max_year=2020,min_year=2000,
                     gyear_url = 'https://s3.amazonaws.com/data.patentsview.org/download/g_patent.tsv.zip',
                     ayear_url = 'https://s3.amazonaws.com/data.patentsview.org/download/g_application.tsv.zip'):
    '''
    Updates 'patent_data_CURRENT.csv' with grant and app years for new patents.
       
    Parameters
    ----------
    
    The output of this dataset is a key input to update_bags(). Thus, the 
    year parameters here control which years/patents will be in that update.
    
    max_year : INT
        Newest allowed GRANT year to add to dataset. Typically used so that 
        if you run this  function in February, grants during Jan-Feb aren't 
        included. In other words, the resulting data structures from this 
        folder only include FULL years of patents.
                
    min_year : INT
        Oldest allowed GRANT year to add to dataset. Mostly used to reduce
        memory use. However, it will ignore new grants that are applied for 
        20 years ago and these won't enter the data structures. Such patents
        are called submarines, are designed to litigate rather than be used,
        and should be ignored. 
        
    Returns
    -------
    None.

    '''
    
    import pandas as pd
        
    print('update_pat_dates now downloading large patent files...')
    
    # download grant year data
    new_gyears = pd.read_csv(gyear_url,sep='\t',
                             usecols=['patent_id','patent_type','patent_date'],
                             parse_dates=['patent_date'])
                                       
    # format grant year data
    new_gyears = (new_gyears
                 .assign(gyear = lambda x: x['patent_date'].dt.year)
                 .query('patent_type == "utility" & gyear <= @max_year & gyear >= @min_year')
                 [['patent_id','gyear']]
                 .rename(columns={'patent_id':'pnum'})
                 )
        
    # download app year data (a few rows have bad dates, so some extra work...)    
    # and format it 
    new_ayears = (pd.read_csv(ayear_url,sep='\t')
                  
                 # filter to US utils 
                 .assign(code_is_int = lambda x: pd.to_numeric(x['series_code'],
                                                            errors='coerce').notnull())
                 .assign(pnum_is_int = lambda x: pd.to_numeric(x['patent_id'],
                                                            errors='coerce').notnull())
                 .assign(date_is_date = lambda x: pd.to_datetime(x['filing_date'],
                                                            errors='coerce').notnull())
                 .query('code_is_int & pnum_is_int & date_is_date')
                 
                 # now that data is nicely behaved, convert the date var  
                 .assign(ayear = lambda x: pd.to_datetime(x['filing_date'],
                                                          errors='coerce').dt.year)
                
                 # output 
                 # key: don't query here
                 [['patent_id','ayear']]
                 .rename(columns={'patent_id':'pnum'}) 
                 )
 
    # merge ayear and gyear together
    # note: pandas merge wasn't playing nice merging with pnum columns as 
    # objects, so let's convert to numbers
    new_ayears['pnum'] = pd.to_numeric(new_ayears['pnum'])
    new_gyears['pnum'] = pd.to_numeric(new_gyears['pnum'])
    
    new_years = new_ayears.merge(new_gyears,on='pnum',how='right') 
    
    # (note: inner merge ensures the year restrictions on the gyear are preserved)
    
    if (new_years.ayear.isnull().sum() > 0 | new_years.gyear.isnull().sum() > 0 ):
        print('WARNING: The new patent data might be missing some date info')
    if len(new_years) != len(new_gyears):
        print('WARNING: Some new grants arent in the appyear data')
        
    # merge this with the existing dates, save update and the prior, as backup.
    
    existing_years = pd.read_csv('../data/patent_level_info/pat_dates_CURRENT.csv')
        
    updated_years = (existing_years.merge(new_years,on='pnum',
                                         how='outer',validate='1:1',
                                         suffixes=(None,'_new')) 
                     # this merge keeps the years in the dataset now fixed as is
                     # for backwards compatibility
                     # any new patents get the years we just downloaded
                    .assign(gyear = lambda x: x.gyear.fillna(x.gyear_new))
                    .assign(ayear = lambda x: x.ayear.fillna(x.ayear_new))
                    [['pnum','ayear','gyear']]
                    )
    
    updated_years = updated_years.astype(int) # no floats! 
             
    existing_years.to_csv('../data/patent_level_info/pat_dates_PRIOR.csv',index=False)
    updated_years.to_csv('../data/patent_level_info/pat_dates_CURRENT.csv',index=False)
    
    
def update_pat_nber_class(cpc_url = 'https://s3.amazonaws.com/data.patentsview.org/download/g_cpc_current.tsv.zip' ):
    '''
    Warning: Slow download of 1+GB file!
    
    NBER broad tech classes can be estabilished for grants until 2015 using 
    PatentsView. Thereafter, we will get CPC codes from PView, and then bridge 
    those to NBER1 based on the existing correspondence. 
    
    As of 2020 Dec 31, only 3 patents (with CPC group = G16Y) have no nber 
    code.
    '''
    
    import pandas as pd
    
    # This includes 1 digit NBER codes from BFH's sample period, then NBER 
    # codes from PView through 2015 grants, then PView match
    
    nber = pd.read_csv('../data/patent_level_info/nber_CURRENT.csv')
    nber.to_csv('../data/patent_level_info/nber_PRIOR.csv',index=False) # save backup of existing
   
    # load patsview  file with up to date cpc codes
    # keep the first CPC code for the patent 
   
    print('update_pat_nber_class now downloading large files...')
    
    cpc = pd.read_csv(cpc_url,sep='\t',
                      usecols=['patent_id','cpc_subclass','cpc_sequence'])\
         .query('cpc_sequence == 0')[['patent_id','cpc_subclass']]
    cpc.columns = ['pnum','cpc_group']  #"cpc_subclass" is patentviews name for the group
    
    # create uspc 1-->1 nber bridge
    
    bridge =   (
                cpc.merge(nber)
                
                # frac of patents with a given cpc assigned to a particular NBER1 
                .groupby(['cpc_group','nber'],as_index=False,)['pnum'].count()
                .assign(tot=lambda x: x.groupby('cpc_group')['pnum'].transform(sum),
                        frac = lambda x: x.pnum/x.tot
                        )
                
                # output the most common nber1
                .sort_values(['cpc_group','frac'])
                .groupby('cpc_group',as_index=False).tail(1)
                [['cpc_group','nber']]
                )
    
    # in the new pat-cpc data, replace cpc codes with nber via bridge, call nber_new
    
    cpc = cpc.merge(bridge)[['pnum','nber']]
    cpc.columns = ['pnum','nber_new']
    
    # merge outer with "nber" df, then update as before    
    
    nber = nber.merge(cpc,on='pnum',how='outer')
    update = (nber.nber.isna() & (~nber.nber_new.isna()))
    nber.loc[update,'nber']=nber.loc[update,'nber_new']
    nber = nber.drop('nber_new',axis=1)
    
    nber = nber.drop_duplicates(subset=['pnum','nber'], keep='first')
        
    nber.to_csv('../data/patent_level_info/nber_CURRENT.csv',index=False)    
   
   
def download_gpg_pages(list_of_patent_nums,num_fetch_threads=20):
    """
    Downloads Google Patent pages for utility patents by iterating over the 
    numbers. Will produce 1 html file (as a txt) per patent, so this requires a lot 
    of time. Google doesn't seem to throttle with the settings below, and it 
    downloads about 1M patents/day. 
    
    Saves downloads within data/html_DL_in_<YYYY> where YYYY is the current 
    year. This is intended to make the code backward compatible and "future
    proof" for users that update the data from year to year when the google 
    html structure changes and users want to return to the raw HTML to extract
    more info than the word bags already parsed. (Or to repeat the parsing 
    for some reason.)
    """

    import os, time, mechanize, threading
    from queue import Queue
    from threading import Thread
    from datetime import datetime
    
    # here we go. build the file directory here for these files.

    save_dir = '../data/html_DL_in_'+str(datetime.now().year)+'/'    
    os.makedirs(save_dir,exist_ok=True)
    
    for p_stem in set([ str(p).zfill(8)[:4] for p in list_of_patent_nums]):
        os.makedirs(save_dir +p_stem,exist_ok=True)  
        
    # the worker function that downloads GPG pages

    def download_patents(i, q):
        """
        This is the worker thread function. It processes items in the queue 
        one after another.  These daemon threads go into an infinite loop, and  
        only exit when the main thread ends.
        
        i is "an instance", a "thread"
        q is the queue, the list of items to work on (here, patents)
        """
        while True:

            patent_num = q.get() # pull the patent num from the queue

            # will save to <save_dir>/<first 4 patent digits of 8 digit representation >/html_<patent number>.txt
            # pnum  8,123,456  --> eight digits: 08123456 --> folder html_0812
            # pnum 18,123,456  --> eight digits: 18123456 --> folder html_1812
            # pnum    812,345  --> eight digits: 00812345 --> folder html_0081

            html_file_path = '%s%s/html_%i.txt' % (save_dir, 
                                                   str(patent_num).zfill(8)[:4], 
                                                   patent_num)
            
            # DL if we don't have the file
            
            if os.path.exists(html_file_path):                    
                # print status, sometimes...
                if patent_num % 25000 == 0:
                    print("Have        " + str(patent_num))
            
            else: 
                # print status, sometimes...
                if patent_num % 25000 == 0:
                    print("Looking for " + str(patent_num))

                br = mechanize.Browser()
                br.set_handle_robots(False)
                br.set_handle_refresh(False)
                br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

                url         = 'https://patents.google.com/patent/US' + str(patent_num)

                now_parse = False
                try:
                    response = br.open(url)
                    if response.code == 200: # successful
                        now_parse = True
                except:
                    pass                        
                

                if now_parse: 
                    results_html = response.read()  # html as a text file   

                    # write to file, ensure accuracy by locking
                    with lock:
                        with open(html_file_path,'wb') as fname:
                            fname.write(results_html)

                # else:
                #     print(str(patent_num) + 'Failed')
            
#            finally:
                #signals to queue job is done
            q.task_done()

    # now, let's put that worker to use and do the job

    start = time.time()

    my_queue = Queue() # initiate the queue
    lock = threading.Lock() # when we are writing a file, stop everything else to avoid errors

    #spawn a pool of threads, and pass them queue instance
    
    for i in range(num_fetch_threads):
        worker = Thread(target=download_patents, args=(i, my_queue,))
        worker.setDaemon(True)
        worker.start()

    #populate queue with data

    for item in list_of_patent_nums:
        my_queue.put(item)

    #wait on the queue until everything has been processed
    
    my_queue.join()

    end = time.time()
    print("Elapsed seconds (rounded up): %d" %(end-start+1))
    print("Elapsed minutes (rounded up): %d" %((end-start)/60+1))

   
def download_patent_HTML(min_year=2019,max_year=2019):
    '''
    For all patents in the "pat_dates_CURRENT.csv" with application years in 
    [min_year, max_year], download the google patent page's html if the patent
    isn't in an HTML folder.    
    '''
    
    import os, logging
    import pandas as pd 
    
    # ======================================================================= #
    # %%   set up     
    # ======================================================================= #
    
    # directory structure - fixed components
    
    bag_dir = '../data/word_bags/'
    
    # directory structure - these parts change if you want to parse the whole patent 
    
    log_fname        = os.path.join(bag_dir,'descriptONLY','logger.log')
    os.makedirs(os.path.join(bag_dir,       'descriptONLY'), exist_ok=True)
    
    # start logging 

    logging.basicConfig(level=logging.INFO,
                        filename=log_fname,
                        format='%(asctime)s - %(message)s')

    # detect years we've DLed files (the parser we use depends on the 
    # formatting of GPG at the time a given page is downloaded)
    
    yS_of_DL = [int(y_path[-4:]) 
                for y_path in os.listdir('../data/')
                if y_path[:-4] == 'html_DL_in_' ] 
  
    # df of all patents/appyears applied for in this time period
    # this is a key input, this is the set of patents we will try to parse 
    
    print('Figuring out what to DL')
    
    pnum_years_df = pd.read_csv('../data/patent_level_info/pat_dates_CURRENT.csv')\
                   .query("ayear <= @max_year & ayear >= @min_year")    
    
    # Function to check if the file exists
    def file_exists(pnum, year):
        'year is a year we might have downloaded the patent'
        file_path = f'../data/html_DL_in_{year}/{str(pnum).zfill(8)[:4]}/html_{pnum}.txt'
        return os.path.exists(file_path)
    
    # List to store pnum with no corresponding files
    pnums_to_DL = []
    
    # Loop through each row in the DataFrame
    for pnum in pnum_years_df['pnum'].to_list():
    
        # Check if the file is found for any of the possible years
        found_file = any(file_exists(pnum, year) for year in yS_of_DL)
        
        # If the file is not found for any of the possible years, add pnum to the list
        if not found_file:
            pnums_to_DL.append(pnum)
    
    print('Pnums to DL:',len(pnums_to_DL))
    logging.info("DLing HTML for:  %i-%i" % (min_year,max_year))
    logging.info("Pnums to DL:     %i" % (len(pnums_to_DL)))
   
    download_gpg_pages(pnums_to_DL)
    
def parse_bags(min_year=2019,max_year=2019,force_clean=False):
    '''
    For all patents in the "pat_dates_CURRENT.csv" with application years in 
    [min_year, max_year], parse the patents.
    
    '''
    
    import os, csv, logging, time, lxml, cchardet, re
    import pandas as pd 
    from datetime import datetime
    from tqdm import tqdm 
    from collections import defaultdict
    from itertools import count
    
    # ======================================================================= #
    # %%   set up     
    # ======================================================================= #
    
    # directory structure - fixed components
    
    bag_dir = '../data/word_bags/'
    word_index_fname = os.path.join(bag_dir,'word_index.csv')
    
    # directory structure - these parts change if you want to parse the whole patent 
    
    log_fname        = os.path.join(bag_dir,'descriptONLY','logger.log')
    failure_fname    = os.path.join(bag_dir,'descriptONLY','parse_failures.csv')
    count_dir        = os.path.join(bag_dir,'descriptONLY','bags_raw_file_per_pat')
    os.makedirs(os.path.join(bag_dir,       'descriptONLY'), exist_ok=True)
    
    # start logging 

    logging.basicConfig(level=logging.INFO,
                        filename=log_fname,
                        format='%(asctime)s - %(message)s')

    # detect years we've DLed files (the parser we use depends on the 
    # formatting of GPG at the time a given page is downloaded)
    
    yS_of_DL = [int(y_path[-4:]) 
                for y_path in os.listdir('../data/')
                if y_path[:-4] == 'html_DL_in_' ] 
  
    # df of all patents/appyears applied for in this time period
    # this is a key input, this is the set of patents we will try to parse 
    
    print('Figuring out what to DL, and what to parse')
    
    pnum_years_df = pd.read_csv('../data/patent_level_info/pat_dates_CURRENT.csv')\
                    .query("ayear <= @max_year & ayear >= @min_year")    
     
    # we don't need to parse all those! some might already be done!
    # so get the subset of patents without bags yet
    # using set types here is WAY faster than the alternatives :)
    
    folder_num_stems = {str(pnum).zfill(8)[:4] for pnum in 
                        pnum_years_df.pnum.tolist()} # folders w our pats   
    existing_pnums = {int(p[6:-4]) 
                      for stem in folder_num_stems 
                      if os.path.exists(count_dir +'/'+ stem +'/')
                      for p in os.listdir(count_dir +'/'+ stem +'/')  }    
    pnums_without_bags = list(set(pnum_years_df.pnum.tolist()) 
                        - existing_pnums) # pats to bag but haven't already
    pnums_without_bags = pd.DataFrame(pnums_without_bags,
                                      columns=['pnum'])\
                          .merge(pnum_years_df,on='pnum')  # bring in the year info
    
    del existing_pnums

    # of this subset, some have not yet been DLed  
    # and the rest are DLed but need to be parsed 
    # find out which is true for all the bagless pnums
    
    paths_to_HTMLs = [] # DLed but not yet parsed, elements=[pnum,year_of_DL]  
    pnum_to_DL = []     # not yet been DLed
    
    # we have to check the folder_num_stems across all yS_of_DL  
    existing_htmls = {int(p[5:-4]):y_of_DL
                      for stem in folder_num_stems 
                      for y_of_DL in yS_of_DL  
                      if os.path.exists('../data/html_DL_in_'+str(y_of_DL)+'/'+stem+'/')
                      for p in os.listdir('../data/html_DL_in_'+str(y_of_DL)+'/'+stem+'/')  }   
    
    for pnum in tqdm(pnums_without_bags.pnum.tolist(),desc='Finding pnum to DL:')  :
        if pnum in existing_htmls.keys():
            paths_to_HTMLs.append([pnum,existing_htmls[pnum]])
        else:
            pnum_to_DL.append(pnum)
        
    # attach the app year to those two structures, so the loop below can find
    # the patents it needs for a given app year
    
    pnums_to_parse = pd.DataFrame(paths_to_HTMLs,columns=['pnum','year_of_DL']).merge(pnums_without_bags,on='pnum')
    pnums_to_DL = pnums_without_bags.query('pnum in @pnum_to_DL')   
    del pnum_to_DL, paths_to_HTMLs
               
    # ======================================================================= #
    # %%=========== Load or Build word_index.csv ============================ #
    # ======================================================================= #
    
    print("Loading word index")
    
    global word_index, failure_dict # passing this obj between parse_HTML() and clean_bags()    
    
    # will be dictionary, allows for easily adding new words with incremented index
        
    if os.path.exists(word_index_fname): 
        
        # open it    
        with open(word_index_fname, 'r') as f_csv:
            csv_reader = csv.reader(f_csv, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
            oldwordindex = [row for row in csv_reader]
            del csv_reader
        
        # set up a dictionary where new words get an incremented index
        # key step! what should the index value of next new word be?
        # -> next new word's index is large enough that it doesn't exist yet
        restartindexat = 1 + max([int(row[1]) for row in oldwordindex])
        word_index = defaultdict(lambda x=count(restartindexat): next(x))  # py3.7 change
        # py 2.7: count(restartindexat).next
    
        # reload old word index file into this dictionary
        for row in oldwordindex:
            word_index[row[0]] = int(row[1])
        del oldwordindex
    
    else:
        
        # start word_index the first time
        word_index = defaultdict(lambda x=count(1): next(x))  # py3.7 change
        # py 2.7: word_index = defaultdict(count(1).next)
        
    # logging.info("Current length of word index:  %i" % len(word_index))
        
    # ======================================================================= #
    # %%=========== Load or Build failures.csv  ============================= #
    # ======================================================================= #
    
    # will be dictionary, allows for easily adding new failures
    
    if os.path.exists(failure_fname): 
        with open(failure_fname, 'r', newline='\n') as f_csv:
            csv_reader = csv.reader(f_csv, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)          
            failure_dict = {row[0]: str(row[1]) for row in csv_reader}
            
    else:
        failure_dict = {}

    print('Pnums to DL:',len(pnums_to_DL))
    logging.info("Pnums to DL:  %i" % (len(pnums_to_DL)))

    # ======================================================================= #
    # %% PARSE IT > UPDATED WORD INDEX, CLEAN WORD BAGS
    #
    # loop over APPLICATION years (because we do our cleaning within a 
    # given app year)  
    # and download what's needed, and then get bags from those and any 
    # previously downloaded but unparsed patents 
    # ======================================================================= #
    
    print("Loop over years to download and parse patents")
    
    pnums_parsed = [] 
    
    for y in range(min_year,max_year+1):
                
        print('year',y)
        
        # %%% WITHIN YEAR Y, PARSE NEW PATENTS 
        # Note: most of the code here is just printing info or saving objects
        
        if len(pnums_to_parse.query('ayear == @y')) > 0:  
            
            logging.info("STARTING PARSE NOW for year %i:  %i" % (y,len(word_index)))
    
            start = time.time()            
            
            for idx, row in tqdm(pnums_to_parse.query('ayear == @y').iterrows(),desc='Parsing...'): 

                # parse_HTML() needs to alter global word_index and failures
                # and it should return a success value when it saves a new bag
                teeeemp = parse_HTML(row['pnum'],row['year_of_DL'])  
                pnums_parsed.append(teeeemp)
                
                # intermittently, it's time to save and print a bunch of info
                
                if idx % 5000 == 0 and idx > 0: # intermittent print
                            
                    logging.info( "At patent pat      %i"% (pnum) )
                    logging.info( "Elapsed minutes    %d" %((time.time()-start)/60+1))  
                    logging.info( "Word index length  %i" % ( len(word_index)) )
            
                if idx % 35000 == 0 and idx > 0: # lower freq saving
                    
                    logging.info( " " )
                    logging.info( "Saving..." )
                    logging.info( "At patent pat      %i"% (pnum) )
                    logging.info( "Elapsed minutes    %d" %((time.time()-start)/60+1))
                    logging.info( "Word index length  %i" % ( len(word_index)) )
                    logging.info( " " )
                    
                    with open(word_index_fname,"w",newline='') as f_csv:
                        out_csv = csv.writer(f_csv, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
                        out_csv.writerows(word_index.items())                     
                        
                    with open(failure_fname,"wb") as f_csv:
                        out_csv = csv.writer(f_csv, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
                        out_csv.writerows(failure_dict.items())               
                
            end = time.time()
            logging.info( "Elapsed seconds (rounded up): %d" %(end-start+1) )
            logging.info( "Elapsed minutes (rounded up): %d" %((end-start)/60+1))
            
            # save word_index at the end of each year
             
            logging.info( "Saving at the end of year %i. Len Index: %i" % (y,len(word_index)))
            with open(word_index_fname,"w",newline='') as f_csv:
                out_csv = csv.writer(f_csv, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
                out_csv.writerows(word_index.items())                
            
            with open(failure_fname,"w") as f_csv:
                out_csv = csv.writer(f_csv, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
                out_csv.writerows(failure_dict.items())                
                           
    years_to_parse = pd.DataFrame(pnums_parsed,columns=['pnum'])\
                    .merge(pnum_years_df,on='pnum').ayear.to_list()

    print('We parsed',len(pnums_parsed),'patents across',len(set(years_to_parse)),'years')
    logging.info('We parsed',len(pnums_parsed),'patents across',len(set(years_to_parse)),'years')
   

def parse_HTML(pnum,year_of_DL):
    '''
    Parses one patent's HTML. year_of_DL indicates the location of the file 
    and tells this function which set of parsing rules to use (which is based
    on the HTML structure google used in a given year)
    '''
 
    import lxml, cchardet # speed! leave, these are actually used 
    from bs4 import BeautifulSoup
    from collections import Counter
    from bs4 import SoupStrainer
    import os
    import pandas as pd
        
    # input/output file paths 
    
    html_file_path = '../data/html_DL_in_%s/%s/html_%i.txt'\
        % (year_of_DL, str(pnum).zfill(8)[:4], pnum)
      
    pnum_count_path = os.path.join('../data/word_bags/','descriptONLY','bags_raw_file_per_pat',
                             str(pnum).zfill(8)[:4],'count_'+str(pnum)+'.csv')
        
    os.makedirs(os.path.dirname(pnum_count_path), exist_ok=True) # make sure dst folder exists
        
    # only proceed if input exists and output does not
    
    if not os.path.exists(html_file_path) or os.path.exists(pnum_count_path):
        return 0 # exits function 
       
    # ----- Open the html file ----- #
    
    if year_of_DL > 2019:
        with open(html_file_path, 'r', encoding="utf8") as html_file:
            html = html_file.read()       
    else:     
        with open(html_file_path, 'r') as html_file:
            html = html_file.read()
    
    # ----- Get the patent text ----- #
    
    # print('have html')
    successes = 0
    failures    = ''     
    abstract_text, claims_text, descrip_text = '','',''
    
    if year_of_DL > 2014: # 2020 and 2021 confirmed here. 
    
        try: # some patents are missing descrip and/or claim and/or abs            
            soup=BeautifulSoup(html,'lxml',parse_only=SoupStrainer('section',itemprop='description')) #parse_only is SPEED!            
            descrip_text    = u' '.join(soup.find('div',{'class':'description'}).findAll(text=True))
            successes = 1
            # print('have descrip')
        except:
            failures        += ' desc'
            # print(3)
         
    elif year_of_DL == 2014:
        
        soup = BeautifulSoup(html,'lxml')
        
        try:
            s               = soup.find('div',{'class':"patent-section patent-abstract-section"})
            abstract_text   = s.find('div',{'class':"abstract"}).contents[0]
            successes       += 1
        except:
            abstract_text   = ' '
            failures        += 'abs'
            
        try:
            s               = soup.find('div',{'class':"patent-section patent-claims-section"})
            claims_text     = u' '.join(s.findAll(text=True))                
            successes       += 1
        except:
            claims_text     = ' '
            failures        += ' claim'
            
        try:
            s               = soup.find('div',{'class':"patent-section patent-description-section"})
            descrip_text    = u' '.join(s.findAll(text=True))                
            successes       += 1
        except:
            descrip_text    = ' '
            failures        += ' desc'
           
    if len(failures) > 0:
        
        failure_dict[pnum] = failures # failure_dict is a global var (from clean_bags), this modifies the global
        
    # ----- Clean/save the bag of words, update/save the word index ----- #

    if successes > 0:        
        
        # clean text a-zA-Z --> lower, all else --> deleted as a space
        
        pat_text = ''.join([i.lower() if (ord(i) <= 90 and ord(i)>=65) or (ord(i) >= 97 and ord(i) <= 122 ) 
                            else ' '  
                            for i in abstract_text + " " + claims_text + " " + descrip_text
                            ]).split()                                
               
        # update master word index
        
        [word_index[k] for k in pat_text] # word_index is a global var (from clean_bags), this modifies the global
        
        # replace words in this patent with index number

        pat_text  = [word_index.get(item,item) for item in pat_text] #2
        text_counter = Counter(pat_text) #3
        
        # save this patent to file
        pd.DataFrame(text_counter.items(),
                     columns=['word_index','count'])\
            .to_csv(pnum_count_path,index=False,header=False)
            
        return pnum # so we can track which years to run the corpus cleaning on
    
    
def clean_bags(min_year,max_year):
    """    
    Update: This is MUCH more memory efficient than previous version, but reads
    the raw patent count files twice instead of once.
    
    As a result, the slowest years take about 8 hours on my computer, but <3GB
    of memory is needed!
    
    Inputs:
        
        1. word_index.csv, 
        2. all the word bags, 
        3. bad_ocr_words.csv
        4. pat_dates_CURRENT.csv
        
    Key outputs are in data/words_bags/descriptONLY/wordspace:
        
        short_words_to_drop.csv       
            DESCRIPT:   word_index of short words
            INPUT NEED: word_index.csv
            
        potential_stopwords.csv       
            DESCRIPT:   words that are common enough in a given year that we drop
            INPUT NEED: all RAW word bags, loop by ayear
         
    And in data/words_bags/descriptONLY/bags_cleaned_annualbatch_by_ayear:
            
        bag_ayear_<YYYY>.csv
            DESCRIPT:   all of the word bags for patents applied for in year YYYY
                        after dropping short words, potential stopwords, and 
                        bad ocr words
                
    Notes:
    
        The output word bags for years covered by Bowen, Fresard, and Hoberg 2021
        are identical except for the inclusion of a small fraction of patents that
        weren't available when the original data collection was done, and patents
        granted after the original parse whose application dates are pre-2010. 
        
        Additionally, adding new patents to a year could change the 
        potential_stopwords, which would alter the cleaned bags somewhat. 
        
    """

    import os, csv, logging
    import pandas as pd 
    from datetime import datetime
    from tqdm import tqdm 
    from collections import defaultdict
    
    # ======================================================================= #
    # %%   set up     
    # ======================================================================= #
    
    # directory structure - fixed components
    
    bag_dir = '../data/word_bags/'
    word_index_fname = os.path.join(bag_dir,'word_index.csv')
    
    # directory structure - these parts change if you want to parse the whole patent 
    
    log_fname        = os.path.join(bag_dir,'descriptONLY','logger.log')
    count_dir        = os.path.join(bag_dir,'descriptONLY','bags_raw_file_per_pat')
    os.makedirs(os.path.join(bag_dir,       'descriptONLY'), exist_ok=True)
    
    short_stop_fname     = '../data/word_bags/descriptONLY/wordspace/short_words_to_drop.csv'
    potential_stop_fname = '../data/word_bags/descriptONLY/wordspace/potential_stopwords.csv'
    batchdir             = '../data/word_bags/descriptONLY/bags_cleaned_annualbatch_by_ayear/'
        
    os.makedirs(batchdir,exist_ok=True)    
        
    # start logging 

    logging.basicConfig(level=logging.INFO,
                        filename=log_fname,
                        format='%(asctime)s - %(message)s')

    print("Cleaning the word bags...")
    logging.info("STARTING TO CLEAN THE BAGS")
            
    # what years to clean (and thus what patents to clean)
    
    list_of_years = list(range(min_year,max_year+1))        
    new_pat_dates = pd.read_csv('../data/patent_level_info/pat_dates_CURRENT.csv').query('ayear in @list_of_years').astype('int32')      
        
    ##############################################################################
    #   CREATE short_words_to_drop.csv (updates off of new word_index)
    #
    # create list of (indexes of) short words that will be dropped
    ##############################################################################
    	
    # Get the indices of short words (recreate incase word_index changed )
    short_word_indices = []
    
    # Load the CSV file and filter rows with string length less than 4
    with open(word_index_fname, 'r') as f_csv:
        csv_reader = csv.reader(f_csv)
        
        for row in csv_reader:
            if len(row[0]) < 4:
                short_word_indices.append(int(row[1]))
    
    # put into df (to save, and bc code below was written using df)
    short_stop_ALLYEARS = pd.DataFrame({'word_index': short_word_indices})
    
    # int32 saves some memory, cheap pre-sort might speed up merges/filters    
    short_stop_ALLYEARS = short_stop_ALLYEARS.astype('int32').sort_values('word_index')
    short_stop_ALLYEARS.to_csv(short_stop_fname,index=False)
    
    ##############################################################################
    #   LOAD old_bad_ocr words (words than only exist before patents were digitized)
    ##############################################################################
    
    old_bad_ocr          = (pd.read_csv('../inputs/bad_ocr_words.csv',names=['word_index'],)
                            .astype('int32').sort_values('word_index')  )  
    
    ##############################################################################
    #   LOAD words used in >25% of patents in a year
    #
    # cols: word_index, year
    #
    # load existing, and then purge current stops from that year (we  
    # rebuild stopword list completely when the below is run.)
    ##############################################################################
    
    if os.path.exists(potential_stop_fname):
        potential_stopwords = pd.read_csv(potential_stop_fname)\
            .query('ayear not in @list_of_years').astype('int32')  
        
    else:
        potential_stopwords = pd.DataFrame()
    
    ##############################################################################
    #   LOOP OVER YEARS, WITHIN EACH:
    #
    #   (1) FIGURE OUT stopwords (building up potential_stopwords.csv)
    #
    # words used in >25% of patent applications in a given year
    #
    #   (2) OUTPUT CLEAN WORD BAGS 
    #
    # Output: 1 csv per year, containing (pnum, word_index, count) for all pnums
    #         applied for in that year, after removing 
    #         - short words "short_words_to_drop.csv"
    #         - badocr words "bad_ocr_words.csv" (in input folder)
    #         - stopwords in (too frequent usage)   "potential_stopwords.csv"
    #
    ############################################################################## 
    
    logging.info("preliminaries complete, now cleaning+getting annual stopwords")
    
    def pd_concat_subfunc(pnum):
        '''
        Helper function to quickly load many csv files into one df
        
        Example usage, two steps: (1) set list of pnums to load, (2) load pnums:
            
            pnums = range(9000000,9001000)
            batch_pats = pd.concat(map(pd_concat_subfunc, pnums))       
    
        This function accounts for the way patents are stored in this folder and
        the possibility of missing patent files
    
        '''
        p_path = f'{count_dir}/{str(pnum).zfill(8)[:4]}/count_{str(pnum)}.csv'
        
        if os.path.exists(p_path):          
            # int32 will cover our needs, half the data of int64
            return pd.read_csv(p_path, names=['word_index','count']).assign(pnum=pnum).astype('int32')  

    def filter_data(batch):
        'Efficient removal of rows of a df for our problem'
        batch = batch[~batch['word_index'].isin(purge['word_index'])]
        return batch[['pnum', 'word_index', 'count']].sort_values(['pnum', 'word_index'])

    def write_to_csv(pnums, yyyy, batch_size=10000):
        'In batches, load pnums and apply filtering, and save annual csv'
        output_path = f'{batchdir}/bag_ayear_{yyyy}.csv'  # Replace with your desired output path
        with open(output_path, 'w') as f:
            for i in tqdm(range(0, len(pnums), batch_size),
                          desc=f'Purging and saving word bags for {yyyy}',
                          total = 1+len(pnums)//batch_size):
                batch_pnums = pnums[i:i+batch_size]
                batch_pats = pd.concat(map(pd_concat_subfunc, batch_pnums))
                filtered_batch_pats = filter_data(batch_pats)
                filtered_batch_pats.to_csv(f, index=False, header=(i == 0))
    
    for yyyy in list_of_years:
        
        pnums = new_pat_dates.query('ayear == @yyyy').pnum.to_list()

        logging.info( "Finding annual stopwords for year: %i" %(yyyy) )
        
        # find this years stop words 
        # ==> find out how many patents use a given word this year
        # ==> load patent and increment dict = word_index:pnum_count
        # this obj is, at max, size len(word_index) long by 2(pnum+count)
    
        n_pats = 0 # count the patents we've parsed
        word_index_counts = defaultdict(int)
        
        for pnum in tqdm(pnums, desc='Getting stopwords'):
            p_path = '../data/word_bags/descriptONLY/bags_raw_file_per_pat/' + \
                     str(pnum).zfill(8)[:4] + '/count_' + str(pnum) + '.csv'
                     
            if os.path.exists(p_path):
                n_pats += 1
                with open(p_path, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        word_idx = int(row[0])  # word_index is the first column in csv
                        word_index_counts[word_idx] += 1        
                             
        threshold = n_pats * 0.25
        filtered_word_counts = {k: v for k, v in word_index_counts.items() if v >= threshold}
        
        # update the stopwords dataset 
        
        stopwords_this_year = pd.DataFrame({
            'word_index': list(filtered_word_counts.keys()),
            # 'frac': [count / n_pats for count in filtered_word_counts.values()]
        }).assign(ayear=yyyy)

        potential_stopwords = potential_stopwords.append(stopwords_this_year)

        # this is the total set of word_indices to drop:

        purge = (pd.concat([stopwords_this_year[['word_index']],short_stop_ALLYEARS,old_bad_ocr])
                 .drop_duplicates('word_index')
                 .sort_values('word_index'))
                
        logging.info('stopwords_this_year figured')
            
        # now, load and clean
        
        logging.info( "outputting cleaned word_bags for year: %i" %(yyyy) )
    
        write_to_csv(pnums, yyyy, 25000)
        
        logging.info('output of '+str(yyyy)+' complete')
        
    # output potential stopwords             
    potential_stopwords.to_csv(potential_stop_fname,
                                index=False)


    
      
def make_RETech(outf,beg=1910,end=2010):
    '''
    Parameters
    ----------
    outf : str, ends with .csv
        Path for output file of RETech
    beg : int, optional
        What year to start? The default is 1929.
    end : int, optional
        What year to start? The default is 2010.        

    Returns
    -------
    None. Saves a patent level csv with pnum, year, and RETech[_name].
    
    Inputs: 
        
        Annual csvs with (pnum, word_index, nwords) for all pnums in a given year.
        We sort by application year to more closely match the timing of the 
        invention. 
        
        Some extensions of this function might require additional inputs (e.g. a
        patent level dataset with information on the country of origin, or type
        of inventor.)
    
    Outputs:
        
        (pnum,RETech) dataset    

    '''
    from tqdm import trange
    import pandas as pd
    import os

    os.makedirs(os.path.dirname(outf) ,exist_ok=True)

    big_RETech = pd.DataFrame() # we will store results in this           
        
    for yyyy in trange(beg-1,end+1,desc='Making RETech...'): 
        
        # keep the last year's agg vector around to create deltas
        # ie what was z(t) from last step in this loop is now z(t-1)
        
        if yyyy > beg - 1: 
            agg_last_year = agg_this_year.copy()
            agg_last_year.columns = ['word_index','nwords_lastyear']
    
        # load cleaned bagOwords (contains all Vjt for this t) 
        
        batchdir = '../data/word_bags/descriptONLY/bags_cleaned_annualbatch_by_ayear/'

        bagOwords = pd.read_csv(batchdir + 'bag_ayear_'+str(yyyy)+'.csv',)
        bagOwords.columns = ['pnum','word_index','nwords']
        
        # create this year's agg vector (zt, equation 1 in the paper)
                            
        agg_this_year = (bagOwords                     
                        # normalize within patent 
  # ie turn “raw counts” (Vjt in paper) into vjt to control for doc length
                        .assign(nwords = lambda xdf: xdf.groupby('pnum')['nwords'].transform(lambda x: x/x.sum()))
                
                        # sum the shares across all patents and control for number of patents (eq 1)
                        .groupby('word_index')['nwords'].sum().reset_index()
                        .assign(nwords = lambda x: x.nwords / x.nwords.sum())
                        )
                                    
        # as long as this isn't the first year, get delta(t) and all the RETech(jt)

        if yyyy > beg-1:
                   
            # create delta, equation 2 in the paper
            
            delta = (pd.merge(agg_last_year,agg_this_year,on='word_index',how='outer')        
                    .fillna(0) # some words aren't in both years, the value becomes 0
                    .assign(delta = lambda x: (x.nwords-x.nwords_lastyear)/(x.nwords+x.nwords_lastyear))
                    [['word_index','delta']] # only output these 
                    )          
            
            # create RETech, equation 3 in the paper
            
            RETech = (bagOwords
                        .merge(delta,how='inner')

                        # bagOwords is all Vjt for the year, compute B/||B|| in the paper
                        # which is just 1/number of words in the patent for each word patent j uses 
                        .assign(nwords_frac = lambda x: 1/x.groupby('pnum')['nwords'].transform(len))                     
                        # dot product --> sum within patent
                        .assign(RETech = lambda x: 100*x.delta*x.nwords_frac)
                        .groupby('pnum')['RETech'].sum()

                        # output patent level measure
                        .reset_index().sort_values('pnum')                
                        .assign(year = yyyy)
                        )
            
            # append RETech for year t to existing
            big_RETech = big_RETech.append(RETech)
            
    big_RETech.to_csv(outf,index=False)   

def make_breadth(outf,beg=1910,end=2017):
	'''
	'''
	
	from tqdm import trange
	import pandas as pd
	import numpy as np
	import os
	
	coarse_class = pd.read_csv('../data/patent_level_info/nber_CURRENT.csv',)
	coarse_class.columns = ['pnum','coarse'] # to match the legacy var names below...
	
	big_breadth = pd.DataFrame() # we will store results in this      
	
	for yyyy in trange(beg,end+1,desc='Creating Breadth...'): #1929,2011
		
		# load cleaned bagOwords and merge in bfh_codes
		
		batchdir = '../data/word_bags/descriptONLY/bags_cleaned_annualbatch_by_ayear/'
		
		bagOwords = pd.read_csv(batchdir + 'bag_ayear_'+str(yyyy)+'.csv',)
		bagOwords.columns = ['pnum','word_index','nwords']
		
		# get the word specializations
		
		spec = (bagOwords.merge(coarse_class,how='inner',on='pnum')
		
				# for each word-cat combo, count the number of pats and total word count
				
				.groupby(['word_index','coarse'])
				.agg(ccnt=('coarse','count'),ncnt=('nwords','sum'))        # ncnt = # times that word is in those patents, ccnt = number of cats the 
				
				# how many more times is a word used in one cat than the next most common cat? 
				
				.reset_index().sort_values(['word_index','ncnt','ccnt'])
				.assign(ng = lambda x: x.groupby('word_index')['ncnt'].pct_change(),
						cg = lambda x: x.groupby('word_index')['ccnt'].pct_change(),
						)
				
				# pct_change puts Nan in the first row of group
				# put 1 in the first row instead of nan, so that one-cat 
				# words survive the query below (it's specialized!) 
				
				.assign(ng = lambda x: x.ng.fillna(1), 
						cg = lambda x: x.cg.fillna(1), 
						)
				
				# keep the most common category for a word and call a word specialized
				# if the most common cat is 50% more used (# words & # of pats) 
				# than the second place cat.
				# also require a word to be used in 10+ pats to be specialized 
				
				.groupby('word_index').tail(1)            
				.query('ng >= .5 & cg >= .5 & ccnt >= 10')
				
				[['word_index','coarse']]            
					
				)
		
		# compute patent level breadth
		
		breadth = (bagOwords.merge(spec,how='inner',on='word_index')
				# get the pat-class word counts 
				.groupby(['pnum','coarse'])['nwords'].sum().reset_index()
					
				# HHI: convert counts to SQUARED shares,
				.assign(tot     = lambda x: x.groupby('pnum').nwords.transform(sum),
						shares2 = lambda x: (x.nwords/x.tot)**2)             
					
				.groupby('pnum',as_index=False)['shares2'].sum()    
							
				)
		breadth['breadth'] = 1 - breadth['shares2']
		breadth.drop('shares2',axis=1,inplace=True)
		
		# add to the main
		
		big_breadth = big_breadth.append(breadth)
		
	# done with loop
	
	big_breadth.to_csv(outf,index=False)



# def ship_outputs(in_retech,in_breadth,outf):
def ship_outputs(output_dir_name):
    '''
    Inputs are paths to the input and output file names. 
    '''
   
    import pandas as pd
    import os
    import numpy as np 
    
    output_dir = '../'+output_dir_name
    in_retech  = '../'+output_dir_name+'/RETech.csv'
    in_breadth = '../'+output_dir_name+'/Breadth.csv'
    
    os.makedirs(output_dir ,exist_ok=True)
    
    ##########################################################################
    # stitch data frames together and output as zipped csv
    ##########################################################################
    
    # pandas is being a pain importing these... being explicit on loading 
    
    # retech and ayear
    
    df1 = pd.read_csv(in_retech,names=['pnum','RETech','ayear'],
                      header=0,
                      dtype={'pnum':np.int64,'RETech':np.float,'ayear':np.int64})
    
    # breadth
    
    df2 = pd.read_csv(in_breadth,names=['pnum','Breadth'],
                      header=0,
                      dtype={'pnum':np.int64,'Breadth':np.float})
        
    # gyear
    
    df3 = pd.read_csv('../data/patent_level_info/pat_dates_CURRENT.csv')
    df3 = df3.drop('ayear',axis=1) # ayear is in the retech output
    
    # nber 1 digit 
    
    df4 = pd.read_csv('../data/patent_level_info/nber_CURRENT.csv')
    df4['nber'] = df4['nber'].astype('Int64') # pd's builtin Int type allows for missing values
        
    out = (df1.merge(df2,on='pnum',how='outer',validate='1:1')
           .merge(df3,how='left',on='pnum',validate='1:1')
           .merge(df4,how='left',on='pnum',validate='1:1')           
           )
    
    # key output!
    
    out.to_csv(output_dir+'/Pat_text_vars_NotWinsored.zip', index=False,
               compression={'method': 'zip', 'archive_name': 'Pat_text_vars_NotWinsored.csv'})    
    
    print('Main data output done!')
    
    ##########################################################################
    # build a "top 20" patent apps table
    ##########################################################################
        
    print('Creating Top-20 table, the slow part is calls to google')
    
    # will show breadth as perentile across last decade, so compute that 
    
    last_10_years = out.query('ayear >= @out.ayear.max()-10')
    last_10_years["Breadth (Percentile)"] = round(last_10_years['Breadth'].rank(pct=True)*100,0)
    last_10_years["Breadth (Percentile)"] = last_10_years["Breadth (Percentile)"].astype('int')

    # get top 20
    
    top_20 = last_10_years.sort_values('RETech',ascending=False).head(20)
    
    # add url to google page    

    top_20['url'] = 'https://patents.google.com/patent/US' + top_20['pnum'].astype(str)
    
    # add title of patent
    
    import requests    
    from requests_html import HTMLSession
    session = HTMLSession()
    
    def get_title(url):        
        try:
            response = session.get(url)             
        except requests.exceptions.RequestException as e:
            print(e)   
            return None
        else:
            return response.html.find('title',first=True).text

    # get_title(top_20.iloc[0,-1])
    
    top_20['title_raw'] = top_20['url'].apply(get_title)
    
    # format it
    
    top_20['Title'] = top_20['title_raw'].str.replace(r'^([A-Z0-9]+ - )', '',regex=True)\
                                      .str.replace(' - Google Patents$','',regex=True)
    
    # prep before creating table
    
    top_20['nber'] = top_20.nber.replace(to_replace=[1,2,3,4,5,6],value=["Chemicals","Comps & Commun","Drugs & Medicine", "Electricity","Mechanics","Other"])
    top_20 = top_20.rename(columns={'nber':'NBER Cat'})
    top_20 = top_20.rename(columns={'ayear':'App Year','gyear':'Grant Year'})
    top_20['Patent'] = '<a href="'+top_20['url'] +'">'+top_20['pnum'].astype(str)+'</a>'    
    
    # html table   
    
    cell_hover = {  #  highlights row you're on
        'selector': 'tr:hover',
        'props': [('background-color', '#ffffb3')]
    }
    
    
    html = top_20[['Patent','RETech','NBER Cat','App Year','Grant Year','Title']]\
        .style\
        .hide_index()\
        .set_properties(subset=['RETech','App Year','Grant Year'],
                        **{'text-align':'center'})\
        .set_properties(subset=['NBER Cat','Patent','Title'],
                        **{'text-align':'left'})\
        .format(lambda x: '{:,.0f}'.format(x),subset=['RETech'])\
        .set_table_styles([cell_hover,
            {'selector': 'th.col_heading:nth-child(1)',
                       'props': [('text-align', 'left')]},
            {'selector': 'th.col_heading:nth-child(3)',
                       'props': [('text-align', 'left')]},
            {'selector': 'th.col_heading:nth-child(6)',
                       'props': [('text-align', 'left')]}
            ])\
        .to_html(doctype_html=True)
    
    with open("updated_graphs/top20_pats.html", "w") as text_file:
        text_file.write(html)
    

def delete_recent_raw_bags():
    '''
    
    DESCRIPTION:
    
    This is NOT meant to be run as a function. Just run the code interactively.
    
    The reason to use this code is: You started parsing HTML into raw word 
    bags, but before the word_index could be saved and updated, the code 
    stopped. So, this code lets you delete recent raw word bag files. Now,
    you can re-run the parsing code without worrying about errant patents 
    having some invalid word_index entries. 
    
    USAGE:
    
    Just set the date you want to delete from in the "delete_after" variable.
    
    WARNING: IT DELETES FILES!

    '''
    
    stop # yes, this is meant to prevent the code from running any way but interactively.     

    import os , time, datetime, calendar
    import pandas as pd
    from tqdm import tqdm
    
    # option 1: delete based on exact last time word_index file is modified
    fp = '../data/word_bags/word_index.csv'
    delete_after_ctime = os.path.getmtime(fp) # Unix timestamp 
    del fp
   
    # option 2: specify a date
    # delete_after = datetime.datetime(2022, 4, 8) # any files created on or after this get struck
    # delete_after_ctime = calendar.timegm(delete_after.timetuple())
    # del delete_after

    print(datetime.datetime.fromtimestamp(delete_after_ctime))

    # only look for pnums in these app years (speeds up lookup)
    min_year = 2010
    max_year = 2022
    
    pnum_years_df = pd.read_csv('../data/patent_level_info/pat_dates_CURRENT.csv')\
                   .query("ayear <= @max_year & ayear >= @min_year")   
    pnum_years_df['stems'] = pnum_years_df['pnum'].astype(str).str.zfill(8).str[:4]
    
    stems = list({ stem for stem in pnum_years_df.stems.to_list()})
    
    delete_these = []
    base      = '../data/word_bags/descriptONLY/bags_raw_file_per_pat/'
    
    for stem in tqdm(stems):
        for pnum in pnum_years_df.query('stems == @stem').pnum.to_list():
        
            filep = base + stem + '/count_' + str(pnum) + '.csv'
            
            if os.path.exists(filep):
        
                if     os.path.getctime(filep) > delete_after_ctime:
                    delete_these.append(filep)
     
     
    print('Prepared to delete',len(delete_these),'files')
    print('Does that sound right? Only proceed if so')
     
    for f in delete_these:
        os.remove(f)    
 

    

