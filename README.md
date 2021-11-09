# Patent Text Variables s

This folder creates and contains the data from Rapidly Evolving Technologies and Startup Exits ([SSRN link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3245839)) by [Donald Bowen](https://bowen.finance), [Gerard Hoberg](http://www-bcf.usc.edu/~hoberg/), and [Laurent Fresard](https://people.lu.usi.ch/fresal/), which is forthcoming in Management Science. _Please cite that study when using or referring to any data or code in this repository._ 

---

<p align="center"> :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star:  
	<br> <br> 
	<b> To download a patent-level dataset with RETech and text-based Tech Breadth: </b>
	<br><br>   <a href="https://github.com/donbowen/Patent-Text-Variables"><b>Click this link, which covers patents granted through last year!</b></a>
	<br> <br> :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star: :star:   
</p>

---
	
## Important usage notes 

1. The dataset above contains raw values (i.e. not winsorized) and we recommend winsorizing by application year before using them.
2. We generally recommend using the data above by _**application**_ year to match the timing of the innovation best. When doing so, note that the most recent three years will be incomplete, as applications in _\[t-3, t\]_ are sometimes not granted by the current year given examination and approval delays. 
	
	
## Code to obtain and use patent text 

The `code` folder includes code to 
- Download all google patent pages 
- Parse the _**descriptions**_ sections of patent text in those webpages into "bags of words" and then clean them. 
- Construct textual variables at the patent level
- Convert patent level variables into group-time variables (e.g. firm-year, state-year, MSA-quarter), especially where stocking is important. 

This code is designed to make it easy to update annually and easy to add additional variable definitions, and we will push changes to the key "parsing" and "update_bags" functions if Google updates their HTML. 

