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
