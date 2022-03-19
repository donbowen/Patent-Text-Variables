# Patent Text Variables

This folder creates and contains the data from Rapidly Evolving Technologies and Startup Exits ([SSRN link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3245839)) by [Donald Bowen](https://bowen.finance), [Gerard Hoberg](http://www-bcf.usc.edu/~hoberg/), and [Laurent Fresard](https://people.lu.usi.ch/fresal/), which is forthcoming in Management Science. (A full replication kit for the analysis in the paper [is available here.](https://github.com/donbowen/BFH)) _Please cite that study when using or referring to any data or code in this repository._ 

_The "front door" to this repo is [on my website, here.](https://bowen.finance/bfh_data/)_

---

<p align="center"> :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star:  
	<br> <br> 
	<b> To download a patent-level dataset with RETech and Tech Breadth: </b>
	<br><br>   <a href="https://github.com/donbowen/Patent-Text-Variables/releases/download/data-to-2017/Pat_text_vars_NotWinsored.zip"><b>Click this link, which covers patent applications through 2017!</b></a>
	<br> <br> :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star:   
</p>

---
	
## Important notes for using the data

1. The dataset above contains raw values (i.e. not winsorized) and we recommend winsorizing by application year before using them.
2. We generally recommend using the data above by _**application**_ year to match the timing of the innovation best. 
3. **`code/aggregate_measures.do` contains several Stata functions to convert patent-level variables into group-time variables (e.g. firm-year, state-year, MSA-quarter).** We include the stocking function from our paper, which gets the group's average patent stats over the prior five years, after applying a 20% rate of depreciation. 
 	
Please see the paper for details on the construction of the measures. Questions can be directed to Donald Bowen, and pointers to errors or omissions, and corrections are welcome. 	
				
## Code to obtain and create variables from patent text yourself 

_Warning: Running the code from scratch builds massive directories of many terabytes and will require substantial computer time as written._

The `code` folder includes code (`GPGupdate.py`) to 
- Download all google patent pages. 
- Parse the _**descriptions**_ sections of patent text in those webpages into "bags of words" and then clean them. We use descriptions to avoid legalese in the claims section. _Note: Google does not cleanly separate the abstract, claims, and description sections for patents before 1976, so all three sections are included for such patents._
- Construct textual variables at the patent level. If you create a new variable from these word bags and would like to contribute that function to this package and distribution, please send an email to Donald Bowen. 

This code is designed to make it easy to update annually and easy to add additional variable definitions, and we will push changes to the key "parsing" and "update_bags" functions if Google updates their HTML. 

