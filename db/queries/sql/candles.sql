-- name: bulk_upsert_candles*!
INSERT INTO candles_1s (ticker, t, open, close, high, low, volume)
VALUES (:ticker, :t, :open, :close, :high, :low, :volume)
ON CONFLICT (ticker, t)
DO UPDATE SET
    open = EXCLUDED.open,
    close = EXCLUDED.close,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    volume = EXCLUDED.volume;


-- name: remove_old_candles!
DELETE FROM candles_1s WHERE t < :till


-- name: get_candles_in_range
SELECT * FROM candles_1s WHERE t >= :from_ AND t <= :to;


-- name: get_latest_candle^
SELECT * FROM candles_1s WHERE ticker = :ticker AND t <= :till_dt ORDER BY t DESC LIMIT 1
