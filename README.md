# Patent Text Variables 

<a href = "https://tooomm.github.io/github-release-stats/?username=donbowen&repository=patent-text-variables"><img src="https://img.shields.io/github/downloads/donbowen/patent-text-variables/total.svg">	</a>

This folder creates and contains the key new variables from Rapidly Evolving Technologies and Startup Exits ([SSRN link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3245839)) by [Donald Bowen](https://bowen.finance), [Gerard Hoberg](http://www-bcf.usc.edu/~hoberg/), and [Laurent Fresard](https://people.lu.usi.ch/fresal/), which is forthcoming in Management Science. (A full replication kit for the analysis in the paper [is available here.](https://github.com/donbowen/BFH)) _Please cite that study when using or referring to any data or code in this repository._ 

_The "front door" to this repo is [my website, which contains more background information on the measures.](https://bowen.finance/bfh_data/)_

---

<p align="center"> :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star:  
	<br> <br> 
	<b> To download a patent-level dataset with RETech and Tech Breadth: </b>
	<br><br>   <a href="https://github.com/donbowen/Patent-Text-Variables/releases/download/data-to-2018/Pat_text_vars_NotWinsored.zip"><b>Click this link, which covers patent applications through 2018!</b></a>
	<br><br>   <a href="https://github.com/donbowen/Patent-Text-Variables/blob/main/pnum_gvkey.zip"><b>(Click this for a PNUM-GVKEY mapping.)</b></a>	
	<br> <br> :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star:   
</p>

---

## Quick description of RETech and Tech Breadth

The variables provided here are based on the text in the section of patents describing the innovation. **They provide researchers a new way to characterize innovation within public firms, startups, places and more. Importantly, they are distinct from existing measures and do not have look-ahead bias: they only use information available in the patent itself.**

"RETech" measures whether the patent pertains to a technological area that is rapidly evolving (i.e., following breakthroughs) or stable. Higher levels of our measure detects patents in new areas and those in subsequent waves of development. High RETech patents substitute for existing technologies rather than complement them, receive more citations and get higher stock market reactions. Among measures without look-ahead bias, RETech has the strongest association with notable breakthrough patents (like lasers, DNA modifications, satellites, Google's PageRank, and more).

"Tech Breadth" measures how much (or little) the patent's text is spread across technological fields. Patents with low levels of breadth (i.e. 0) are niche and can be understood by scientists familiar with a single field of study. High values of breadth indicate that the patent imbues ideas from many fields and will likely require teams with diverse knowledge to implement. As such, we expect low breadth patents to be more redeployable and complementary to the technology stacks outside the inventing firm.
	
## Important notes for using the data

1. The file above contains patents applied for by Dec 31, 2018 and granted by Dec 31, 2021. 
1. The dataset above contains raw values (i.e. not winsorized) and we recommend winsorizing by _application_ year before using them.
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

