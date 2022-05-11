-- Drop table

-- DROP TABLE stock_trading.dbo.sp500;

CREATE TABLE stock_trading.dbo.sp500 (
	Symbol varchar(5)  NOT NULL,
	[Security] varchar(50)  NULL,
	SECfilings varchar(50)  NULL,
	GICSSector varchar(50)  NULL,
	[GICSSub-Industry] varchar(100)  NULL,
	HeadquartersLocation varchar(100)  NULL,
	Datefirstadded varchar(50)  NULL,
	CIK int NULL,
	Founded varchar(50)  NULL,
	CONSTRAINT PK_sp500 PRIMARY KEY (Symbol)
);
