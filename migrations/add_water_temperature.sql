-- Migration: Add water_temperature columns to separate air and water temp
-- Date: 2025-01-21
-- Description: Adds water_temperature column to weather_data, forecast_windows, and catches tables

-- Add water_temperature to weather_data table
ALTER TABLE weather_data ADD COLUMN water_temperature REAL;

-- Add water_temperature to forecast_windows table
ALTER TABLE forecast_windows ADD COLUMN water_temperature REAL;

-- Add water_temperature to catches table
ALTER TABLE catches ADD COLUMN water_temperature REAL;

-- Update comments
COMMENT ON COLUMN weather_data.temperature IS 'Air temperature in Fahrenheit';
COMMENT ON COLUMN weather_data.water_temperature IS 'Water temperature in Fahrenheit (from NOAA CO-OPS)';

COMMENT ON COLUMN forecast_windows.temperature IS 'Air temperature in Fahrenheit';
COMMENT ON COLUMN forecast_windows.water_temperature IS 'Water temperature in Fahrenheit (from NOAA CO-OPS)';

COMMENT ON COLUMN catches.temperature IS 'Air temperature in Fahrenheit at time of catch';
COMMENT ON COLUMN catches.water_temperature IS 'Water temperature in Fahrenheit at time of catch';
