-- Step 1: Create the database
CREATE DATABASE RealEstate;
GO

-- Step 2: Use it
USE RealEstate;
GO

-- Step 3: Create pricing table
IF OBJECT_ID('pricing', 'U') IS NULL
CREATE TABLE pricing (
    id INT IDENTITY(1,1) PRIMARY KEY,
    price BIGINT,
    area INT,
    bedrooms INT,
    bathrooms INT,
    stories INT,
    mainroad BIT,
    guestroom BIT,
    basement BIT,
    hotwaterheating BIT,
    airconditioning BIT,
    parking INT,
    prefarea BIT,
    furnishingstatus VARCHAR(50),
    price_per_sqft FLOAT,
    has_aircon_and_heat BIT
);
GO

-- Step 4: Create event_log table
IF OBJECT_ID('event_log', 'U') IS NULL
CREATE TABLE event_log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    table_name VARCHAR(50),
    type VARCHAR(50),
    timestamp DATETIME,
    description TEXT,
    source_script VARCHAR(100)
);
GO

-- Step 5: Add indexes (hypothetical FK/index candidates)
CREATE NONCLUSTERED INDEX idx_furnishingstatus ON pricing (furnishingstatus);
CREATE NONCLUSTERED INDEX idx_mainroad_guestroom ON pricing (mainroad, guestroom);
CREATE NONCLUSTERED INDEX idx_prefarea_parking ON pricing (prefarea, parking);

