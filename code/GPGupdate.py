"""

Set up: 
    
1. This file should be in <dir>/code, where dir is the root directory where you
want all the work this code does. This code will create large directories  
within dir! If you cloned/downloaded the repo, this is taken care of. 

2. The working directory for python should be set to dir/code when this is run.

3. This is Py 3.7. 

4. Necessary packages, can be installed via: pip install <packageName>

    packages in the anaconda distribution 
    cchardet           
    bs4                
    mechanize
    tqdm
    
    lxml + cchardet *dramatically* speeds up the parsing. Installing Visual C++
    was necessary on my Windows machine to install cchardet and get the full 
    benefits.
    
"""
    
##########################
# INPUTS TO SET
##########################

# note: the output files are too big to store via github, 
# and i'm not doing a GLFS workaround
# so I store them in folders with the date of the update (oh yeah...)

output_dir = 'outputs 2021-11' # update to new me each update to save 
                                    # prior outputs (for error checks, etc)

update_from = 2010        # get DLs and parse files in these application years
update_to   = 2020
output_to   = update_to-3 # The latest app year to compute retech/breadth. 
                          # I usually lag given examination/approval lags

##########################
# OK, LET'S DO THIS
##########################

import GPGutils
import os

# initialize directory structure, download needed files (runs one time only)
GPGutils.set_up_onetime()         

# get numbers/dates of new grants since last run
GPGutils.update_pat_dates()       

# get nber class for those grants (needed for breadth)
GPGutils.update_pat_nber_class()  

# DL, parse to raw bags, clean into annual bags 
GPGutils.update_bags(update_from,update_to)  

# create the measures and stitch together
if os.path.exists('../'+output_dir+'/'):
    print('You might want to rename the output dir, so you dont')
    print('overwrite existing prior outputs. Or maybe not. Idk.')
else:
    
    GPGutils.make_RETech('../'+output_dir+'/RETech.csv',end=output_to)  
        
    GPGutils.make_breadth('../'+output_dir+'/Breadth.csv',end=output_to)     
    
    GPGutils.ship_outputs(in_retech='../'+output_dir+'/RETech.csv',
                          in_breadth='../'+output_dir+'/Breadth.csv',
                          outf=      '../'+output_dir+'/Pat_text_vars_NotWinsored.csv'
                      ) # merge and output