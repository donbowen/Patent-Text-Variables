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

    while_clean_bags()          
        prep website 
        prep bfh / ms folder 

    after clean_bags()
        rename this cd as "code", update gitignore
        check if parse(), from new downloads of pre- and post 1976 patent, 
        
            matches description bag for pre-1976 patent   
            matches description bag for post-1976 patent   (maybe these include abstract?)
                basically, for the 2014 switch, do we need to remove the abs/claims part
            >>> Might need a switch inside that! or to remove parts. 
        
        ship commits
        
        retech()
        breadth()
        compare to existing 
        
        ship(), copy csv to dropbox, then into existing shared file 
        update link in readme to the new patent data if link changes
        
        call this whole directory E:/data/Patent-Text-Vars, update gitdesktop link
    
import GPGutils
import os

GPGutils.set_up_onetime()         # initialize directory structure, download needed files

GPGutils.update_pat_dates()       # get numbers/dates of new grants since last run

GPGutils.update_pat_nber_class()  # get nber class for those grants (needed for breadth)

GPGutils.update_bags(2010,2020)   # DL, parse to raw bags, clean into annual bags 

# note: the output files are too big to store via github, and i'm not doing a git workaround
# so I store them in folders with the date of the update, oh yeah...

output_dir_name = 'outputs 2021-11' # update me each time you run update to save prior outputs (for error checks, rerunning, etc)

if os.path.exists('../'+output_dir_name+'/'):
    print('You might want to rename the output dir, so you dont')
    print('overwrite existing prior outputs. Or maybe not. Idk.')
else:
    
    GPGutils.make_RETech('../'+output_dir_name+'/RETech.csv',end=2017)  
        
    GPGutils.make_breadth('../'+output_dir_name+'/Breadth.csv',end=2017)     

    # TODO comp to prior
    
    GPGutils.ship_outputs(in1='../'+output_dir_name+'/RETech.csv',
                          in2='../'+output_dir_name+'/Breadth.csv',
                          out='../'+output_dir_name+'/Pat_text_vars_NotWinsored.csv'
                      ) # merge and output