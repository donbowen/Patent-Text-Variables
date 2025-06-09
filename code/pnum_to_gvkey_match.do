stop // a lazy way to prevent running the downloads when I hit CTRL+D

	// work in a sub directory

	cap mkdir dev_permco_gvkey_link  // starts with "dev_", so it'll be gitignored
	cd dev_permco_gvkey_link

////////////////////////////////////////////////////////////////////////////////
// manual steps
////////////////////////////////////////////////////////////////////////////////

*** 1. from WRDS: download the CCM-CRSP linking table (LC and LU), call it "wrds_link_table.csv"
	* https://wrds-www.wharton.upenn.edu/pages/get-data/center-research-security-prices-crsp/annual-update/crspcompustat-merged/compustat-crsp-link/

	import delimited "wrds_link_table.csv", delimiter(comma) varnames(1) rowrange(2) clear
	rename lpermco permco
	sort permco
	*duplicates report permco
	save wrds_link_table, replace

*** 2. update URLS here if they changed 

	local permco_fname  "Match_patent_permco_permno_2023"
	local appdate_fname "KPSS_2023"

	local url_permco "https://github.com/KPSS2017/Technological-Innovation-Resource-Allocation-and-Growth-Extended-Data/blob/master/`permco_fname'.csv.zip?raw=true"
	local url_appdate "https://github.com/KPSS2017/Technological-Innovation-Resource-Allocation-and-Growth-Extended-Data/blob/master/`appdate_fname'.csv.zip?raw=true"
	
////////////////////////////////////////////////////////////////////////////////
// download the patent permco link (a recent and comprehensive job)
////////////////////////////////////////////////////////////////////////////////

	 // download to cwd  
	copy "`url_permco'" pnum_permco.zip  

	// unzip in cwd  
	unzipfile pnum_permco.zip  

////////////////////////////////////////////////////////////////////////////////
// download application date (in rare cases where we need to pick a 
// gvkey from multiple choices, do so based on application date)
////////////////////////////////////////////////////////////////////////////////

	 // download to cwd  
	copy "`url_appdate'" `appdate_fname'.csv.zip  

	// unzip in cwd  
	unzipfile `appdate_fname'.csv.zip  
	
	// clean and format it
	import delimited "`appdate_fname'.csv", delimiter(comma) varnames(1) clear
	tostring filing_date, replace
	g appdate = date(filing_date,"YMD")
	keep patent_num appdate
	save pnum_appdate, replace
	
////////////////////////////////////////////////////////////////////////////////
// convert permco to gvkey
////////////////////////////////////////////////////////////////////////////////

	import delimited "`permco_fname'.csv", delimiter(comma) varnames(1) clear
	drop permno // use permco
		
	merge m:m permco using wrds_link_table, keep(3) nogen
	
	// count # of possible gvkey for a given patent
		
	egen tag = tag(patent_num gvkey)
	egen distinct = total(tag), by(patent_num) 

	// save pnum gvkey for patents with only one possible gvkey
	
	preserve 
	keep if distinct == 1
	bysort patent_num: keep if _n == 1
	keep patent_num gvkey
	
	tempfile no_dups_partition	
	save `no_dups_partition', replace
	restore
	
	// in rare cases, we have multiple gvkey options, 
	// so pick based on appdate (is appdate within gvkey permno link date range)
	// first, get appdate and format dates	

	keep if distinct > 1
	drop tag distinct
		
	distinct patent_num 	// how many should we have at end? 41
	local end_with = `r(ndistinct)'

	merge m:1 patent_num using pnum_appdate, keep(1 3) nogen
	
	tostring linkdt, replace
	g start = date(linkdt,"YMD")
	g end = date(linkenddt,"YMD")
	format appdate start end %td
	
	// now make choices
	
	g valid 	= (start <= appdate & end >= appdate) 
	bysort patent_num: egen n_valid = sum(valid)
	bysort patent_num: egen min_start = min(start)
	bysort patent_num: egen max_end = max(end)
	g range = end-start
	bysort patent_num: egen max_range = max(range)
	
	g choice = .
	replace choice = valid            if n_valid == 1
	replace choice = start==min_start if choice == . & n_valid == 0 & appdate < min_start
	replace choice = end==max_end     if choice == . & n_valid == 0 & appdate > max_end
	replace choice = range==max_range if choice == . & n_valid > 1
	replace choice = end==max_end     if choice == . 
	
	distinct patent_num
	distinct patent_num if choice == 1
	
	keep if choice
	keep patent_num gvkey 
	append using `no_dups_partition'
	
	rename patent_num pnum // our naming convention
	export delim using "pnum_gvkey.csv", replace
	zipfile "pnum_gvkey.csv" , saving(pnum_gvkey, replace)
	
	cap erase  "../../pnum_gvkey.zip" 
	copy "pnum_gvkey.zip" "../../pnum_gvkey.zip" 
