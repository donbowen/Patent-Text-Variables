from requests_html import HTMLSession
import pandas as pd
from github import Github 
import os
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

# get total DL count as of now

count_url =  'https://img.shields.io/github/downloads/donbowen/patent-text-variables/total.svg'
session = HTMLSession()
r = session.get(count_url)
count = r.html.search('Downloads: {:n}')[0]

# download and add to DL tracker dataframe

DL_df_url = 'https://raw.githubusercontent.com/donbowen/Patent-Text-Variables/main/admin/DL_tracker.csv'
df = pd.read_csv(DL_df_url)
df.loc[len(df.index)] = [pd.to_datetime('today').date(),count] 

# upload that file 

token = os.environ['key']
g = Github(token)
repo = g.get_repo('donbowen/Patent-Text-Variables')
file_to_update = repo.get_contents('admin/DL_tracker.csv')
repo.update_file('admin/DL_tracker.csv',
                 'updating DL tracker',
                 df.to_csv(index=False),
                 file_to_update.sha
                 )

# let's plot DLs over time 
# the first 10 months are interpolated (no weekly data), so a little extra work
# here to make that part of the line dotted

df2 = df.copy()
df2.loc[:,'interpolated']  = df2.iloc[:2,1]
df2.loc[:,'weekly'] = df2.iloc[1:,1]
df2.Date = pd.to_datetime(df2.Date) 
plot = df2.plot.line(x='Date',y=['interpolated','weekly'],
                     style=['b-.','b-'],legend=False,title='RETech Downloads')

plot.get_figure().savefig('temp.png', format="png")

with open('temp.png','rb') as f:
    file_to_update = repo.get_contents('admin/historical_DLs.png')
    repo.update_file('admin/historical_DLs.png',
                     'updating DL tracker fig',
                     f.read(),
                     file_to_update.sha
                     )
