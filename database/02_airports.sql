-- ------------------------------------------------------------
-- AIRPORTS
-- Top 30 US airports + CDG (Paris)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS airports (
    airport_id      INT AUTO_INCREMENT PRIMARY KEY,
    iata_code       VARCHAR(3)   NOT NULL UNIQUE,
    name            VARCHAR(60)  NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    state           VARCHAR(2),
    country         VARCHAR(40)  NOT NULL DEFAULT 'USA',
    latitude        DECIMAL(9,6) NOT NULL,
    longitude       DECIMAL(9,6) NOT NULL,
    metro_pop_M     DECIMAL(5,2) NOT NULL COMMENT 'Metro population in millions',
    is_hub          BOOLEAN      NOT NULL DEFAULT FALSE,
    num_gates       INT          NOT NULL DEFAULT 1,
    open_time       TIME         NOT NULL DEFAULT '05:00:00',
    close_time      TIME         NOT NULL DEFAULT '01:00:00',
    timezone        VARCHAR(32)  NOT NULL DEFAULT 'America/New_York'
);

-- ------------------------------------------------------------
-- SEED: Airports (Top 30 US + CDG)
-- Data based on Wikipedia busiest US airports list
-- ------------------------------------------------------------
INSERT INTO airports (iata_code, name, city, state, country, latitude, longitude, metro_pop_M, is_hub, num_gates, timezone) VALUES
('ATL','Hartsfield-Jackson Atlanta Intl','Atlanta','GA','USA',33.6407,-84.4277,6.14,TRUE,11,'America/New_York'),
('LAX','Los Angeles Intl','Los Angeles','CA','USA',33.9425,-118.4081,13.20,TRUE,11,'America/Los_Angeles'),
('ORD','O\'Hare Intl','Chicago','IL','USA',41.9742,-87.9073,9.46,TRUE,11,'America/Chicago'),
('DFW','Dallas/Fort Worth Intl','Dallas','TX','USA',32.8998,-97.0403,7.76,TRUE,11,'America/Chicago'),
('DEN','Denver Intl','Denver','CO','USA',39.8561,-104.6737,2.93,FALSE,3,'America/Denver'),
('JFK','John F. Kennedy Intl','New York','NY','USA',40.6413,-73.7781,20.14,FALSE,5,'America/New_York'),
('SFO','San Francisco Intl','San Francisco','CA','USA',37.6213,-122.3790,4.75,FALSE,5,'America/Los_Angeles'),
('SEA','Seattle-Tacoma Intl','Seattle','WA','USA',47.4502,-122.3088,4.02,FALSE,4,'America/Los_Angeles'),
('LAS','Harry Reid Intl','Las Vegas','NV','USA',36.0840,-115.1537,2.23,FALSE,2,'America/Los_Angeles'),
('MCO','Orlando Intl','Orlando','FL','USA',28.4294,-81.3090,2.67,FALSE,3,'America/New_York'),
('MIA','Miami Intl','Miami','FL','USA',25.7959,-80.2870,6.17,FALSE,5,'America/New_York'),
('CLT','Charlotte Douglas Intl','Charlotte','NC','USA',35.2140,-80.9431,2.67,FALSE,3,'America/New_York'),
('PHX','Phoenix Sky Harbor Intl','Phoenix','AZ','USA',33.4373,-112.0078,4.95,FALSE,5,'America/Phoenix'),
('IAH','George Bush Intercontinental','Houston','TX','USA',29.9902,-95.3368,7.34,FALSE,5,'America/Chicago'),
('BOS','Logan Intl','Boston','MA','USA',42.3656,-71.0096,4.87,FALSE,5,'America/New_York'),
('MSP','Minneapolis-Saint Paul Intl','Minneapolis','MN','USA',44.8848,-93.2223,3.65,FALSE,4,'America/Chicago'),
('FLL','Fort Lauderdale-Hollywood Intl','Fort Lauderdale','FL','USA',26.0726,-80.1527,1.95,FALSE,2,'America/New_York'),
('DTW','Detroit Metropolitan','Detroit','MI','USA',42.2162,-83.3554,4.37,FALSE,4,'America/New_York'),
('PHL','Philadelphia Intl','Philadelphia','PA','USA',39.8719,-75.2411,6.23,FALSE,5,'America/New_York'),
('LGA','LaGuardia','New York','NY','USA',40.7769,-73.8740,20.14,FALSE,5,'America/New_York'),
('MDW','Chicago Midway','Chicago','IL','USA',41.7868,-87.7522,9.46,FALSE,5,'America/Chicago'),
('BWI','Baltimore/Washington Intl','Baltimore','MD','USA',39.1754,-76.6683,9.97,FALSE,5,'America/New_York'),
('SLC','Salt Lake City Intl','Salt Lake City','UT','USA',40.7884,-111.9778,1.26,FALSE,1,'America/Denver'),
('DCA','Ronald Reagan Washington Natl','Washington','DC','USA',38.8512,-77.0402,9.97,FALSE,5,'America/New_York'),
('SAN','San Diego Intl','San Diego','CA','USA',32.7338,-117.1933,3.34,FALSE,3,'America/Los_Angeles'),
('MCI','Kansas City Intl','Kansas City','MO','USA',39.2976,-94.7139,2.22,FALSE,2,'America/Chicago'),
('STL','St. Louis Lambert Intl','St. Louis','MO','USA',38.7487,-90.3700,2.81,FALSE,3,'America/Chicago'),
('HNL','Daniel K. Inouye Intl','Honolulu','HI','USA',21.3187,-157.9224,0.98,FALSE,1,'Pacific/Honolulu'),
('PDX','Portland Intl','Portland','OR','USA',45.5898,-122.5951,2.51,FALSE,3,'America/Los_Angeles'),
('BNA','Nashville Intl','Nashville','TN','USA',36.1263,-86.6774,2.01,FALSE,2,'America/Chicago'),
('CDG','Charles de Gaulle Intl','Paris',NULL,'France',49.0097,2.5479,12.20,FALSE,5,'Europe/Paris');
