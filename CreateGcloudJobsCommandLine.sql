select
	bucket grp, concat(min(t.Symbol), '-', max(t.Symbol)) ,
	'CALL gcloud scheduler jobs create http ' cmd,
	CONCAT('refresh_ticker_info_', bucket,'_', min(t.Symbol), '-', max(t.Symbol)) job_name,
	CONCAT(' --location ', 'us-central1 ') loc,
	CONCAT(' --time-zone ', '"America/New_York" ')tz,
	CONCAT(' --schedule "', bucket, ' 3 * * *" ') sched,
	CONCAT(' --http-method ', 'GET') method,
	CONCAT('--uri "', 'https://yahoosp500etl-vlw6tjp5aa-uc.a.run.app/load_ticker_info?ticker=', STRING_AGG(Symbol , '|'), '"' ) uri, 
	count(*)
from
	(
	select
		Symbol,
		ntile(50) OVER(
		ORDER BY Symbol) bucket
	from
		dbo.sp500 s) t
group by
	bucket
order by
	1;
            
/* gcloud scheduler jobs create http my-http-job --schedule "45 23 * * *" --uri "http://myproject/my-url.com" --http-method GET */
