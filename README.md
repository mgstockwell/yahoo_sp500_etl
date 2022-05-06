# yahoo_sp500_etl
ETL routines to pull data from Yahoo Finance and load to Azure

# Setup
- Pull repo to local directory using git clone http://....
- run gcloud init to authorize account and set default project/region
- deploy using "gcloud run deploy --source ."
- Add secret to secret manager: https://cloud.google.com/run/docs/configuring/secrets
  - Add the build service acct to secret https://cloud.google.com/build/docs/securing-builds/use-secrets
- Add to code as env variable, see https://cloud.google.com/run/docs/tutorials/identity-platform#secret-manager
