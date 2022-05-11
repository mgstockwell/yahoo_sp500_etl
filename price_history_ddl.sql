DROP TABLE IF EXISTS stock_trading.dbo.price_history;
DROP TABLE IF EXISTS stock_trading.dbo.price_history_tmp;

CREATE TABLE stock_trading.dbo.price_history (
	[Datetime] varchar(25)  NOT NULL,
	[Open] real NULL,
	High real NULL,
	Low real NULL,
	[Close] real NULL,
	Volume int NULL,
	ticker varchar(4)  NOT NULL,
	CONSTRAINT PK__price_history PRIMARY KEY ([Datetime], ticker)
);

CREATE TABLE stock_trading.dbo.price_history_tmp (
	[Datetime] varchar(25)  NOT NULL,
	[Open] real NULL,
	High real NULL,
	Low real NULL,
	[Close] real NULL,
	Volume int NULL,
	ticker varchar(4)  NOT NULL,
	CONSTRAINT PK__price_history_tmp PRIMARY KEY ([Datetime], ticker)
);