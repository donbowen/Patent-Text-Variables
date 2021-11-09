"""

Py 3.7. Necessary packages:

    packages in the anaconda distribution 
    lxml
    cchardet
    bs4 
    mechanize
    tqdm
    
lxml + cchardet *dramatically* speeds up the parsing. Installing Visual C++ was
necessary on my Windows machine to install cchardet and get the full benefits.
    
"""

to finish 

    clean_bags()
    delete the call to clean_bags() below
    update updated initial data in inputs/Pat_Text_Vars_StarterInputs.zip, copy to 
        dropbox, then to the public folder for easy DL, and if the link 
        changes, update url in set_up() 
    rename this cd as "code", update gitignore
    ship commits
    update Patent-Text-Vars-private-dev with final code, but less important
    delete E/data/fake 
    call this whole directory E:/data/Patent-Text-Vars, update gitdesktop link
    
    
    create E:/Patent-Text-Vars-private-dev
        put the old code (plus make_bag) in that
        rename the GPG repo to Patent-Text-Vars-private-dev
        sync     
    readme for user points to dl (copy from other repo), describes use, asks or cite (no details on code!)







import GPGutils, os

GPGutils.set_up_onetime()         # initialize directory structure, download needed files

GPGutils.update_pat_dates()       # get numbers/dates of new grants since last run

GPGutils.update_pat_nber_class()  # get nber class for those grants (needed for breadth)

GPGutils.update_bags(2010,2020)   # DL, parse to raw bags, clean into annual bags 

clean_bags(list(range(2010,2020+1)))  # delete once done

# note: the output files are too big to store via github, and i'm not doing a git workaround
# so I store them in folders with the date of the update, oh yeah...

output_dir_name = 'outputs 2021-11' # update me each time you run update to save prior outputs (for error checks, rerunning, etc)

if os.path.exists('../'+output_dir_name+'/'):
    print('You might want to rename the output dir, so you dont')
    print('overwrite existing prior outputs')
else:
    
    GPGutils.make_RETech('../'+output_dir_name+'/RETech.csv')  
    
    # TODO comp to prior
    
    GPGutils.make_breadth('../'+output_dir_name+'/Breadth.csv')     
    
    GPGutils.ship_outputs(in1='../'+output_dir_name+'/RETech.csv',
                          in2='../'+output_dir_name+'/Breadth.csv',
                          out='../'+output_dir_name+'/Pat_text_vars.csv'
                      ) # merge and output