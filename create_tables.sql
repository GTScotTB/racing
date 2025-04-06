-- Add car_number_round to FormulaFordEventEntry
ALTER TABLE formula_ford_event_entry ADD COLUMN car_number_round INTEGER;

-- Create CompetitorWeightHeight table
CREATE TABLE competitor_weight_height (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    competitor_id INTEGER NOT NULL,
    qual_weight FLOAT,
    qual_height VARCHAR(10),
    r1_weight FLOAT,
    r1_height VARCHAR(10),
    r2_weight FLOAT,
    r2_height VARCHAR(10),
    r3_weight FLOAT,
    r3_height VARCHAR(10),
    notes TEXT,
    FOREIGN KEY (competitor_id) REFERENCES formula_ford_competitor(id),
    FOREIGN KEY (event_id) REFERENCES formula_ford_event(id)
);

-- Create CompetitorECU table
CREATE TABLE competitor_ecu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    competitor_id INTEGER NOT NULL,
    ecu_number VARCHAR(50),
    inspector_name VARCHAR(100),
    check_date DATE,
    notes TEXT,
    FOREIGN KEY (competitor_id) REFERENCES formula_ford_competitor(id),
    FOREIGN KEY (event_id) REFERENCES formula_ford_event(id)
);

-- Create CompetitorEngine table
CREATE TABLE competitor_engine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    competitor_id INTEGER NOT NULL,
    engine_number VARCHAR(50),
    inspector_name VARCHAR(100),
    check_date DATE,
    notes TEXT,
    FOREIGN KEY (competitor_id) REFERENCES formula_ford_competitor(id),
    FOREIGN KEY (event_id) REFERENCES formula_ford_event(id)
);

-- Create TechnicalCheck table
CREATE TABLE technical_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    competitor_id INTEGER NOT NULL,
    check_type VARCHAR(50),
    result VARCHAR(255),
    inspector_name VARCHAR(100),
    check_date DATE,
    notes TEXT,
    FOREIGN KEY (competitor_id) REFERENCES formula_ford_competitor(id),
    FOREIGN KEY (event_id) REFERENCES formula_ford_event(id)
); 