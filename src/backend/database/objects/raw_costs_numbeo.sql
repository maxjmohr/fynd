CREATE TABLE raw_costs_numbeo(
    location_id         INT,
    city                VARCHAR(255),
    country             VARCHAR(255) NOT NULL,
    meal_inexp          NUMERIC(15,5),
    meal_mid            NUMERIC(15,5),
    meal_mcdo           NUMERIC(15,5),
    bread               NUMERIC(15,5),
    eggs                NUMERIC(15,5),
    cheese              NUMERIC(15,5),
    apples              NUMERIC(15,5),
    oranges             NUMERIC(15,5),
    potato              NUMERIC(15,5),
    lettuce             NUMERIC(15,5),
    tomato              NUMERIC(15,5),
    banana              NUMERIC(15,5),
    onion               NUMERIC(15,5),
    beef                NUMERIC(15,5),
    chicken             NUMERIC(15,5),
    rice                NUMERIC(15,5),
    water_small         NUMERIC(15,5),
    water_large         NUMERIC(15,5),
    soda                NUMERIC(15,5),
    milk                NUMERIC(15,5),
    cappuccino          NUMERIC(15,5),
    beer_dom            NUMERIC(15,5),
    beer_imp            NUMERIC(15,5),
    beer_large          NUMERIC(15,5),
    wine                NUMERIC(15,5),
    transport_month     NUMERIC(15,5),
    transport_ticket    NUMERIC(15,5),
    taxi_start          NUMERIC(15,5),
    taxi_km             NUMERIC(15,5),
    taxi_hour           NUMERIC(15,5),
    gas                 NUMERIC(15,5),
    apartment_1room_c   NUMERIC(15,5),
    apartment_1room_o   NUMERIC(15,5),
    apartment_3room_c   NUMERIC(15,5),
    apartment_3room_o   NUMERIC(15,5),
    electricity_water   NUMERIC(15,5),
    internet            NUMERIC(15,5),
    sqm_center          NUMERIC(15,5),
    sqm_suburbs         NUMERIC(15,5),
    mortgage            NUMERIC(15,5),
    phone_plan          NUMERIC(15,5),
    gym                 NUMERIC(15,5),
    tennis              NUMERIC(15,5),
    cinema              NUMERIC(15,5),
    jeans               NUMERIC(15,5),
    dress               NUMERIC(15,5),
    shoes_running       NUMERIC(15,5),
    shoes_business      NUMERIC(15,5),
    cigarettes          NUMERIC(15,5),
    salary              NUMERIC(15,5),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id)
);


COMMENT ON TABLE raw_costs_numbeo IS 'Table stores raw cost data across many categories of all available cities and countries.';

COMMENT ON COLUMN raw_costs_numbeo.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN raw_costs_numbeo.city IS 'City name';
COMMENT ON COLUMN raw_costs_numbeo.country IS 'Country name';
COMMENT ON COLUMN raw_costs_numbeo.meal_inexp IS 'Meal, Inexpensive Restaurant';
COMMENT ON COLUMN raw_costs_numbeo.meal_mid IS 'Meal for 2 People, Mid-range Restaurant, Three-course';
COMMENT ON COLUMN raw_costs_numbeo.meal_mcdo IS 'McMeal at McDonalds (or Equivalent Combo Meal)';
COMMENT ON COLUMN raw_costs_numbeo.bread IS 'Loaf of Fresh White Bread (500g)';
COMMENT ON COLUMN raw_costs_numbeo.eggs IS 'Eggs (regular) (12)';
COMMENT ON COLUMN raw_costs_numbeo.cheese IS 'Local Cheese (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.apples IS 'Apples (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.oranges IS 'Oranges (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.potato IS 'Potato (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.lettuce IS 'Lettuce (1 head)';
COMMENT ON COLUMN raw_costs_numbeo.tomato IS 'Tomato (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.banana IS 'Banana (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.onion IS 'Onion (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.beef IS 'Beef Round (1kg) (or Equivalent Back Leg Red Meat)';
COMMENT ON COLUMN raw_costs_numbeo.chicken IS 'Chicken Fillets (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.rice IS 'Rice (white), (1kg)';
COMMENT ON COLUMN raw_costs_numbeo.water_small IS 'Water (0.33 liter bottle)';
COMMENT ON COLUMN raw_costs_numbeo.water_large IS 'Water (1.5 liter bottle)';
COMMENT ON COLUMN raw_costs_numbeo.soda IS 'Coke/Pepsi (0.33 liter bottle)';
COMMENT ON COLUMN raw_costs_numbeo.milk IS 'Milk (regular), (1 liter)';
COMMENT ON COLUMN raw_costs_numbeo.cappuccino IS 'Cappuccino (regular)';
COMMENT ON COLUMN raw_costs_numbeo.beer_dom IS 'Domestic Beer (0.5 liter draught)';
COMMENT ON COLUMN raw_costs_numbeo.beer_imp IS 'Imported Beer (0.33 liter bottle)';
COMMENT ON COLUMN raw_costs_numbeo.beer_large IS 'Domestic Beer (0.5 liter bottle)';
COMMENT ON COLUMN raw_costs_numbeo.wine IS 'Bottle of Wine (Mid-Range)';
COMMENT ON COLUMN raw_costs_numbeo.transport_month IS 'Monthly Pass (Regular Price)';
COMMENT ON COLUMN raw_costs_numbeo.transport_ticket IS 'One-way Ticket (Local Transport)';
COMMENT ON COLUMN raw_costs_numbeo.taxi_start IS 'Taxi Start (Normal Tariff)';
COMMENT ON COLUMN raw_costs_numbeo.taxi_km IS 'Taxi 1km (Normal Tariff)';
COMMENT ON COLUMN raw_costs_numbeo.taxi_hour IS 'Taxi 1hour Waiting (Normal Tariff)';
COMMENT ON COLUMN raw_costs_numbeo.gas IS 'Gasoline (1 liter)';
COMMENT ON COLUMN raw_costs_numbeo.apartment_1room_c IS 'Apartment (1 bedroom) in City Centre';
COMMENT ON COLUMN raw_costs_numbeo.apartment_1room_o IS 'Apartment (1 bedroom) Outside of Centre';
COMMENT ON COLUMN raw_costs_numbeo.apartment_3room_c IS 'Apartment (3 bedrooms) in City Centre';
COMMENT ON COLUMN raw_costs_numbeo.apartment_3room_o IS 'Apartment (3 bedrooms) Outside of Centre';
COMMENT ON COLUMN raw_costs_numbeo.electricity_water IS 'Basic (Electricity, Heating, Cooling, Water, Garbage) for 85m2 Apartment';
COMMENT ON COLUMN raw_costs_numbeo.internet IS 'Internet (60 Mbps or More, Unlimited Data, Cable/ADSL)';
COMMENT ON COLUMN raw_costs_numbeo.sqm_center IS 'Price per Square Meter to Buy Apartment in City Centre';
COMMENT ON COLUMN raw_costs_numbeo.sqm_suburbs IS 'Price per Square Meter to Buy Apartment Outside of Centre';
COMMENT ON COLUMN raw_costs_numbeo.mortgage IS 'Mortgage Interest Rate in Percentages (%), Yearly, for 20 Years Fixed-Rate';
COMMENT ON COLUMN raw_costs_numbeo.phone_plan IS 'Mobile Phone Monthly Plan with Calls and 10GB+ Data';
COMMENT ON COLUMN raw_costs_numbeo.gym IS 'Fitness Club, Monthly Fee for 1 Adult';
COMMENT ON COLUMN raw_costs_numbeo.tennis IS 'Tennis Court Rent (1 Hour on Weekend)';
COMMENT ON COLUMN raw_costs_numbeo.cinema IS 'Cinema, International Release, 1 Seat';
COMMENT ON COLUMN raw_costs_numbeo.jeans IS '1 Pair of Jeans (Levis 501 Or Similar)';
COMMENT ON COLUMN raw_costs_numbeo.dress IS '1 Summer Dress in a Chain Store (Zara, H&M, ...)';
COMMENT ON COLUMN raw_costs_numbeo.shoes_running IS '1 Pair of Nike Running Shoes (Mid-Range)';
COMMENT ON COLUMN raw_costs_numbeo.shoes_business IS '1 Pair of Men Leather Business Shoes';
COMMENT ON COLUMN raw_costs_numbeo.cigarettes IS 'Cigarettes 20 Pack (Marlboro)';
COMMENT ON COLUMN raw_costs_numbeo.salary IS 'Average Monthly Net Salary (After Tax)';
COMMENT ON COLUMN raw_costs_numbeo.updated_at IS 'Timestamp of the last update of the record';