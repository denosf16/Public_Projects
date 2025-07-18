-- 1. Widen POSITION to allow hybrid roles like 'Guard-Forward', 'Forward-Center', etc.
ALTER TABLE player_info
ALTER COLUMN POSITION VARCHAR(30);

-- 2. Ensure DRAFT_YEAR accepts NULL and is stored as an INT
ALTER TABLE player_info
ALTER COLUMN DRAFT_YEAR INT NULL;

-- 3. Ensure DRAFT_ROUND accepts NULL and is stored as an INT
ALTER TABLE player_info
ALTER COLUMN DRAFT_ROUND INT NULL;

-- 4. Ensure DRAFT_NUMBER accepts NULL and is stored as an INT
ALTER TABLE player_info
ALTER COLUMN DRAFT_NUMBER INT NULL;

-- 5. Ensure HEIGHT_INCHES can accept decimal precision (for cases like 79.5 in future flexibility)
ALTER TABLE player_info
ALTER COLUMN HEIGHT_INCHES FLOAT NULL;

-- 6. Ensure TEAM_ID can be NULL (for free agents or unassigned players)
ALTER TABLE player_info
ALTER COLUMN TEAM_ID INT NULL;

-- 7. Ensure BIRTHDATE is correctly typed as DATE and accepts NULL
ALTER TABLE player_info
ALTER COLUMN BIRTHDATE DATE NULL;


