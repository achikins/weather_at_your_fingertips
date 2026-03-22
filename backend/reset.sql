
-- WAYF Weather Database — Reset
-- run this BEFORE schema.sql to start fresh.

 
DROP TABLE IF EXISTS alerts            CASCADE;
DROP TABLE IF EXISTS forecasts         CASCADE;
DROP TABLE IF EXISTS monthly_aggregates CASCADE;
DROP TABLE IF EXISTS daily_weather     CASCADE;
DROP TABLE IF EXISTS stations          CASCADE;