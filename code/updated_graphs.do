
* for figure title/notes:

local through 2021    // what's the latest applcation year in this data?
local grantsfrom 2024 // what's the latest grants in this data

********************************************************************************	
* load util funcs	
********************************************************************************
{	
	capture program drop winsorby
	program define winsorby
		syntax varlist(min=1 numeric) ,  [ by(varlist)  p(real 0.01) ]
		* Examples:
		*
		* winsorby varlist
		* winsorby varlist, by(year)
		* winsorby varlist, p(0.05)
		* winsorby varlist, by(year) p(0.05)
		*
		* If by() is not specified, winsorizes over all observations.
		* This winsorizes by percentile tails (for now).
		*
		* If p() not specified, 1% tails assumed. P must strictly be between 0 and 0.5
		*
		* AUTOMATICALLY GENERATES NEW WINSORIZED VERSION, NAMED WITH "w_" IN FRONT!!!!!!!!!
		* 		E.g. CALLING winsor return YIELDS A NEW VARIABLE called "w_return".
		*
		****************************************************************************
		****************************************************************************
		*
		*	IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT
		*
		* NOTE: Winsor requires there to be enough non-missing observations to fully
		* ascribe percentile cutoffs. E.g. if 1%, it requires 100 obs, 2% -> 50 obs,
		* 5% -> 20 obs.
		*
		* If a group has fewer non-missing observations than winsor requires, the
		* UNALTERED observations are returned!!!!!
		*
		****************************************************************************
		****************************************************************************
		
		display "varlist now contains |`varlist'|"
		display "byvars now contains |`by'|"
		display "p now contains |`p'|"
		if `p' < 0 | `p' > .5 {
			display "ERROR: p() must be between 0 and 0.5"
			ERROR
		}
		
		tempvar group
		egen `group' = group(`by')
		foreach v of varlist `varlist' {
			gen w_`v' = .
			qui su `group', meanonly
			di "Winsoring `v' across `r(max)' groups"
			forval i  = 1/`r(max)' {
				capture { 
					winsor `v' if `group' == `i', gen(temp) p(`p')		
					replace w_`v' = temp if `group' == `i'
					drop temp
				}
				if _rc != 0 {
					/* If winsor is asked to winsor at 1%, it wants 100 obs, else
					it errors. If 2%, it wants 50 obs. If 5%, it wants 20 obs. Get it?
					Anyways, if a group is too small for winsor - we'll just return the group.
					*/
					replace w_`v' = `v' if `group' == `i'
				}
			}
		}

	end

	* have: patent level dataset with
	* group variable identifiers on patents (eg gvkey, MSA, state, etc)
	* time variable (eg month, quarter, or year of application or grant)
	* X vars you want to aggregate to a group-time panel

	cap prog drop patstat_agg
	prog def patstat_agg
	syntax varlist, Groupvar(varname) Timevar(varname) Depreciation(real) Windowsize(integer) [Idvar(varname)]
	/* 

	You have a dataset with observations belonging to a group and time. Each 
	observation has some statistics X.

	This will create a group-time dataset with

		max(X) for the group over some time window [t-W,t]
		avg(X) for the group over some time window [t-W,t]
		stock(X) for the group over some time window [t-W,t]
		
		where stock is sum(X*(1-deprec)^lag)/count(X). This is the average X but 
		weighted towards more recent time periods. It is intuitively also a stock. 
		This is the method of creating patent stocks in Bowen, Fresard, and Hoberg
		Forthcoming. 

	Notes: 

	1. The resulting dataset will have all possible combinations of group-time.	This
	   means the resulting dataset will likely have excess observations.
	2. Any observations with missing values for group or time will be ignored.
	3. Windowsize = 5 means stats cover [t-4,t]
	4. Depreciation should be *per period*. If 20% a year on annual data, use 0.20.
	   If 20% a year on quarterly data, use 0.05.
	 
	Example:

		// it replicates the stocking function in the paper:
		
		use if retech != . using pat_lv, clear
		keep if ayear > 1970 & ayear <= 2010 // keep some burn in
		patstat_agg retech , g(vxfirm_id) t(aqtr) d(0.05) w(20)	
		drop if year(dofq(aqtr)) < 1980 // drop burn in period 
		rename (aqtr retech_stock) (qtr retech_stock_fcn)
		merge 1:1 vxfirm qtr using startup_qtr_panel, keepusing(retech_stock) keep(3)
		pwcorr *stoc*
		
		// the function is more general. here, used on industry-year variables:
		
		use "http://www.stata-press.com/data/r10/abdata.dta", clear
		patstat_agg emp wage indoutpt , g(ind) t(year) d(0.20) w(4) i(cap)
		
		// if you don't tell it an observation in a group is denoted by cap using
		// the i() option, you have to have a variable called pnum
		
		use "http://www.stata-press.com/data/r10/abdata.dta", clear
		rename cap pnum 
		patstat_agg emp wage indoutpt , g(ind) t(year) d(0.20) w(4)

		
	*/

	qui{ 
		if "`idvar'" == "" {
			local idvar pnum
		}
		
		drop if missing(`groupvar') | missing(`timevar')

		// set up locals for collapse and stat commands 

		local max_collapse
		local sum_collapse
		local count_collapse
		local max_range
		local sum_range 
		local count_range 
		foreach v in `varlist' {
			local max_collapse   "`max_collapse'   max_`v'   = `v'"
			local sum_collapse   "`sum_collapse'   sum_`v'   = `v'"
			local count_collapse "`count_collapse' count_`v' = `v'"
			local max_range      "`max_range'      `v'_max_roll`windowsize'   = max_`v'"
			local sum_range      "`sum_range'      `v'_sum_roll`windowsize'   = sum_`v'"
			local count_range    "`count_range'    `v'_count_roll`windowsize' = count_`v'"
		}

		// collapse to G-T panel, with each group-time's average and max patent stats within the period

		collapse (sum)   `sum_collapse' (max) `max_collapse' ///
				 (count) `count_collapse', by(`groupvar' `timevar')

		// the panel should have no gaps and 0s where missing values exist 
			
		tsset `groupvar' `timevar'
		tsfill, full
		foreach v of varlist max_* sum_* count_* {
			replace `v' = 0 if `v' == .
		}	
		
		// compute the "max" within the windows (honestly), and store sums for the average pat stat in window 
		// yes: both of these can be done in many ways, this is kind of a "free" ride 
		// as we code towards the rolling stock
		
		local lookback = 1-`windowsize' // ex: stats over [-3,0] for win length = 4
		rangestat (max) `max_range' ///
				  (sum) `sum_range'  `count_range' ///
				  , interval(`timevar' `lookback' 0) by(`groupvar') 

		foreach v in `varlist' {
			g `v'_avg_roll = `v'_sum_roll`windowsize' / `v'_count_roll`windowsize'
			lab var `v'_max_roll`win' "max: q+[`lookback', 0])"
			lab var `v'_avg_roll`win' "avg: q+[`lookback', 0])"
		}
			
		// create the rolling window "stocks" (a rolling average weighted towards present)
		//          sum over patents in window ( (1-d)^t * X ) 
		// stock    ------------------------------------------
		//                 count of patents in that window       
		

		local lookback = `windowsize' - 1 // ex Lags 0,1,2,3 for win length = 4 
		local perc = `depreciation'*100

		sort `groupvar' `timevar'

		foreach v in `varlist' {
			g `v'_stock`win' = 0
			forval lag = 0/`lookback' {
				by `groupvar' (`timevar'): replace `v'_stock`win' = `v'_stock`win' + L`lag'.sum_`v' * (1-`depreciation')^`lag' if _n > `lag'
			}
			replace  `v'_stock`win' = `v'_stock`win' / `v'_count_roll`windowsize'
			replace  `v'_stock`win' = 0 if `v'_count_roll`windowsize' == 0
			lab var `v'_stock`win' "`v' stock: [t-`lookback',t] (`perc'% deprec) "
			
		}
		
		
		// output
		
		order `groupvar' `timevar' 
		keep `groupvar' `timevar'  *_max_roll* *_avg_roll* *_stock* 		
	}
	end
}
********************************************************************************	
* plots	
********************************************************************************
	
*** load data and prep to plot
	
	cd "../outputs 2025-02/" // unzipfile copies into cd by default, so move cd
	
	unzipfile Pat_text_vars_NotWinsored.zip, replace
	
	import delim using Pat_text_vars_NotWinsored.csv, clear
	
	* winsorize - skip for speed outliers do not impact these charts 
	
	*winsorby retech, by(ayear) p(0.01) // yuck, slow	
	*drop retech 
	*rename w_retech retech
		
	* so we can compute for each tech area	
	
	separate retech, by(nber) g(retech_nber_) 
		
	* compute yearly stocks 
	
	g all = 1 // next fcn needs a group id, lump all pats into a group
	patstat_agg retech breadth retech_*, g(all) t(ayear) d(.2) w(5)
		
	* a check: plot the stock vs the avg versions
	
	line retech_stock retech_avg_roll ayear	
		
	keep ayear *_stock
	drop *nber_7* *nber_8*
	rename *_stock *
		
* fig: overall
	
	local lineparts ayear if ayear >= 1930 & ayear <= `through', c(L) lp(solid)   lcolor(black) lw(thick) ms(i) mlab() mlabpos(9) mlabs(large) mlabc(black)
	twoway (line retech `lineparts') , ///
		title("Updated RETech through `through'", size( vlarge )) ytitle("") xtitle("") legend(off) ///
		xlabel(1930 (10) 2020 ,  labs(large)   ) ///
		ylabel(, labs(large) angle(horizontal) glcolor(p2%10)  ) ///
		graphregion(color(white) lwidth(medium)) ///
		note(" " "{bf:Note:}      The RETech index is based all patents {bf:applied} for in a given year." "{bf:Sample:} Patents granted by Dec 31 `grantsfrom'")
	graph display , ysize(4) xsize(6)
	graph export "../code/updated_graphs/RETech-1930.png", replace		

* fig: by category	
	
	{	
		local varnum 1 // will loop over variable labels, explicitly increment var name numbering
		foreach category in "Chemicals" "Comps & Commun" "Drugs & Medicine" "Electricity" "Mechanics" "Other" {
			local graph_name = lower(substr(`"`category'"',1,2)) //
			di  "varnum `varnum' name `graph_name' label `category'"
			
			if `varnum' > 3 {
				local xlab xlabel(1930 (10) 2020 ,  labs(large) angle(vertical) grid )
			}
			else {
				local xlab 	xlabel(1930 (10) 2020,grid)		xscale(off fill) 
			}
			if `varnum' == 1 | `varnum' == 4 {
				local ylab ylabel(, angle(horizontal)  glcolor(p2%10)  labs(large) format(%9.0g) )
			}
			else {
				local ylab 			yscale(off fill) 
			}
			
			twoway  /// plot all in gray 
					(line retech_nber_*        ayear if ayear >= 1930 & ayear <= `through' ///
						, lpattern(solid) lwidth(medium) lcolor(gray gray gray gray gray gray)) ///
					/// plot focus on one variable
					(line retech_nber_`varnum' ayear if ayear >= 1930 & ayear <= `through' ///
						, lpattern(solid) lwidth(vthick) lcolor(blue))  ///
					/// options
					, title("`category'", color(black)) legend(off) ytitle("") xtitle("") ///
					  `xlab' `ylab' ///
					  name(`graph_name', replace)   graphregion(color(white) lwidth(medium))
			
			local varnum = `varnum' + 1
		}
		
		window manage close graph _all

		graph combine ch co dr el me ot,  rows(2) graphregion(color(white) lwidth(medium)) ycommon xcommon imargin(tiny) ///
				title("Updated RETech through `through'", size( vlarge ) margin(b=5))  ///
				note(" " "{bf:Note:}      The RETech index is based all patents {bf:applied} for in a given year." "{bf:Sample:} Patents granted by Dec 31 `grantsfrom'",)

		graph display, xsize(8) ysize(5)
		graph export "../code/updated_graphs/RETech-1930-ByTechCat.png", replace
	}	
	
