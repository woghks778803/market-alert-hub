INSERT INTO exchange_instruments(exchange_id,instrument_id,exchange_symbol,price_precision,qty_precision,min_notional,active)
VALUES
 ( (SELECT id FROM exchanges WHERE code='BINANCE'),
   (SELECT id FROM instruments WHERE symbol='BTCUSDT'),
   'BTCUSDT', 8, 8, 10.0, TRUE ),
 ( (SELECT id FROM exchanges WHERE code='UPBIT'),
   (SELECT id FROM instruments WHERE symbol='BTCUSDT'),
   'BTC/USDT', 8, 8, 10.0, TRUE );