# yahoo_sp500_etl
ETL routines to pull data from Yahoo Finance and load to Azure

## Setup
- Pull repo to local directory using git clone http://....
- setup Azure database, or use alternate ODBC connection. see <CreateAzureDB.ps1>
- create tables in database <sp500_ddl.sql><ticker_info_ddl.sql><price_history_ddl.sql>
- run gcloud init to authorize account and set default project/region
- deploy using "gc"
- Add secret to secret manager: https://cloud.google.com/run/docs/configuring/secrets
  - Add the build service acct to secret https://cloud.google.com/build/docs/securing-builds/use-secrets
- Add to code as env variable, see https://cloud.google.com/run/docs/tutorials/identity-platform#secret-manager

## Job Run setup
- Use "gcloud scheduler jobs create", see <gcloud_jobs_ticker_info.bat> and <CreateGcloudJobsCommandLinePriceHistory.sql>
- Note for 5 min updates during week the crontab is "*/5 9-17 * * 1-5", meaning 
*“At every 5th minute from 1 through 59 past every hour from 9 through 17 on every day-of-week from Monday through Friday.”* see https://crontab.guru/#*/5_9-17_*_*_1-5
- 
