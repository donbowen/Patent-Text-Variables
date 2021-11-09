


* have: patent level dataset with 
* observation level variable is called pnum 
* group variable identifiers on patents (eg gvkey, MSA, state, etc)
* time variable (eg month, quarter, or year of application or grant)

cap prog drop patstat_agg
prog def patstat_agg
syntax varlist, Groupvar(varname) Timevar(varname) Depreciation(real) Windowsize(integer) [Idvar(varname)]
* Windowsize = 5 means stats cover [t-4,t]

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

1. The resulting dataset will have all possible combinations of group-time.	
2. The input 
 
Example:

	use pat_lv, clear
	patstat_agg RETech , g(vxfirm_id) t(qtr) d(0.05) w(5)	
 
	use "http://www.stata-press.com/data/r10/abdata.dta", clear
	rename cap pnum
	patstat_agg emp wage indoutpt , g(ind) t(year) d(0.20) w(4)

	use "http://www.stata-press.com/data/r10/abdata.dta", clear
	patstat_agg emp wage indoutpt , g(ind) t(year) d(0.20) w(4) i(cap)
	
*/

qui{ 
	if "`idvar'" == "" {
		local idvar pnum
	}

	// set up locals for collapse and stat commands 

	local max_collapse
	local sum_collapse
	local max_range
	local sum_range 
	foreach v in `varlist' {
		local max_collapse "`max_collapse' max_`v' = `v'"
		local sum_collapse "`sum_collapse' sum_`v' = `v'"
		local max_range    "`max_range' `v'_max_roll`windowsize' = max_`v'"
		local sum_range    "`sum_range' `v'_sum_roll`windowsize' = sum_`v'"
	}

	// collapse to G-T panel, with each group-time's average and max patent stats within the period

	collapse (sum) `sum_collapse' (max) `max_collapse' ///
			(count) n_pnum=`idvar', by(`groupvar' `timevar')

	// the panel should have no gaps and 0s where missing values exist 
		
	tsset `groupvar' `timevar'
	tsfill, full
	foreach v of varlist max_* sum_* n_pnum {
		replace `v' = 0 if `v' == .
	}	
	
	// compute the "max" within the windows (honestly), and store sums for the average pat stat in window 
	// yes: both of these can be done in many ways, this is kind of a "free" ride 
	// as we code towards the rolling stock
	
	local lookback = 1-`windowsize' // ex: stats over [-3,0] for win length = 4
	rangestat (max) `max_range' ///
			  (sum) `sum_range'  n_pnum_roll`windowsize' = n_pnum ///
			  , interval(`timevar' `lookback' 0) by(`groupvar') 

	foreach v in `varlist' {
		g `v'_avg_roll = `v'_sum_roll`windowsize' / n_pnum_roll`windowsize'
		lab var `v'_max_roll`win' "max: q+[`lookback', 0])"
		lab var `v'_avg_roll`win' "avg: q+[`lookback', 0])"
	}
		
	// create the rolling window "stocks" (a rolling average weighted towards present)
	//          sum over patents in window ( (1-d)^t * X ) 
	// stock    ------------------------------------------
	//                 count of patents in that window       <<< n_pnum_roll
	

	local lookback = `windowsize' - 1 // ex Lags 0,1,2,3 for win length = 4 
	local perc = `depreciation'*100

	sort `groupvar' `timevar'

	foreach v in `varlist' {
		g `v'_stock`win' = 0
		forval lag = 0/`lookback' {
			by `groupvar' (`timevar'): replace `v'_stock`win' = `v'_stock`win' + L`lag'.sum_`v' * (1-`depreciation')^`lag' if _n > `lag'
		}
		replace  `v'_stock`win' = `v'_stock`win' / n_pnum_roll
		replace  `v'_stock`win' = 0 if n_pnum_roll == 0
		lab var `v'_stock`win' "`v' stock: [t-`lookback',t] (`perc'% deprec) "
		
	}
	
	
	// output
	
	order `groupvar' `timevar' n_pnum_roll
	keep `groupvar' `timevar' n_pnum_roll *_max_roll* *_avg_roll* *_stock* 		
}
end

/* 
*/
