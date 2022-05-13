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

CREATE NONCLUSTERED INDEX nci_wi_price_history_ ON dbo.price_history (  Datetime ASC  , ticker ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;

CREATE NONCLUSTERED INDEX nci_wi_price_history_tmp ON dbo.price_history_tmp (  Datetime ASC  , ticker ASC  )  
	 WITH (  PAD_INDEX = OFF ,FILLFACTOR = 100  ,SORT_IN_TEMPDB = OFF , IGNORE_DUP_KEY = OFF , STATISTICS_NORECOMPUTE = OFF , ONLINE = OFF , ALLOW_ROW_LOCKS = ON , ALLOW_PAGE_LOCKS = ON  )
	 ON [PRIMARY ] ;