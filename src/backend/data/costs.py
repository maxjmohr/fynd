from lxml import etree
import pandas as pd
import numpy as np
import os
import requests
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import xgboost as xgb

class numbeoScraper:
    ''' Scrape data from numbeo.com '''
    def __init__(self) -> None:
        "Initialize the class"
        self.url = "https://www.numbeo.com"

    
    def train_xgb(self, features:pd.DataFrame, targets:pd.DataFrame) -> xgb.XGBRegressor:
        ''' Train an XGBoost model to predict missing values
        Input:  - features: pd.DataFrame, features to train the model on
                - targets: pd.DataFrame, targets to train the model on
        Output: model: trained XGBoost model
        '''

        # Split the data into training and test sets
        X_train, _, y_train, _ = train_test_split(features, targets, test_size=0.2, random_state=42)

        X_train = X_train.fillna(0)  # Replace NaN with 0 or any other appropriate value
        # y_train = y_train.fillna(0)  # Replace NaN with 0 or any other appropriate value

        model = xgb.XGBRegressor(objective="reg:squarederror", random_state=666)
        model.fit(X_train, y_train)

        return model
    

    def predict_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        ''' Predict missing values of feature columns in the DataFrame
        Input:  - df: pd.DataFrame, DataFrame to predict missing values in
                - model: xgb.XGBRegressor, trained XGBoost model
        Output: pd.DataFrame, DataFrame with predicted missing values
        '''
        # Get the feature columns
        feature_columns = df.columns[df.isna().any()].tolist()
        # Delete city and country columns
        if "city" in feature_columns:
            feature_columns.remove("city")
        if "country" in feature_columns:
            feature_columns.remove("country")

        # Create xgb DataFrame
        df_xgb = df.copy()

        # Drop city and country columns
        if "city" in df_xgb.columns:
            df_xgb.drop(["city"], axis=1, inplace=True)
        if "country" in df_xgb.columns:
            df_xgb.drop(["country"], axis=1, inplace=True)

        # Turn all columns into float except city and country
        for column in df_xgb.columns:
            df_xgb[column] = pd.to_numeric(df_xgb[column], errors='coerce')

        # Predict missing values
        for column in feature_columns:
            # Train the model for the current feature if it has not been trained yet
            current_script_directory = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(current_script_directory, f"../../../res/models/costs_numbeo_{column}.model")
            if os.path.exists(path):
                model = xgb.XGBRegressor()
                model.load_model(path)
            else:
                model = self.train_xgb(features=df_xgb.loc[df_xgb[column].notna(), df_xgb.columns != column],
                                       targets=df_xgb.loc[df_xgb[column].notna(), column])

            # Get the indices of the missing values
            indices = df[df[column].isna()].index.tolist()

            # Predict the missing values
            predictions = model.predict(df_xgb.loc[indices, df_xgb.columns != column])

            # Replace the missing values with the predictions
            df.loc[indices, column] = predictions

            # Save model
            model.save_model(path)

        return df


    def get_costs(self, by: str = "country", currency: str = "EUR") -> pd.DataFrame:
        ''' Scrape the costs by city or country from numbeo.com
        Input:  - self.url
                - by: str, either "city" or "country"
                - currency: str, currency to display the costs in
        Output: pd.DataFrame
        '''
        # Check if currency is ISO 4217 compliant
        if len(currency) != 3:
            raise ValueError("Currency must be ISO 4217 compliant")
        
        # Get the HTML code
        if by == "city":
            url = self.url + f"/cost-of-living/prices_by_city.jsp?displayCurrency={currency}&itemId=101&itemId=100&itemId=228&itemId=224&itemId=60&itemId=66&itemId=64&itemId=62&itemId=110&itemId=118&itemId=121&itemId=14&itemId=19&itemId=17&itemId=15&itemId=11&itemId=16&itemId=113&itemId=9&itemId=12&itemId=8&itemId=119&itemId=111&itemId=112&itemId=115&itemId=116&itemId=13&itemId=27&itemId=26&itemId=29&itemId=28&itemId=114&itemId=6&itemId=4&itemId=5&itemId=3&itemId=2&itemId=1&itemId=7&itemId=105&itemId=106&itemId=44&itemId=40&itemId=42&itemId=24&itemId=20&itemId=18&itemId=109&itemId=108&itemId=107&itemId=206&itemId=25&itemId=30&itemId=33&itemId=34"
        elif by == "country":
            url = self.url + f"/cost-of-living/prices_by_country.jsp?displayCurrency={currency}&itemId=101&itemId=100&itemId=228&itemId=224&itemId=60&itemId=66&itemId=64&itemId=62&itemId=110&itemId=118&itemId=121&itemId=14&itemId=19&itemId=17&itemId=15&itemId=11&itemId=16&itemId=113&itemId=9&itemId=12&itemId=8&itemId=119&itemId=111&itemId=112&itemId=115&itemId=116&itemId=13&itemId=27&itemId=26&itemId=29&itemId=28&itemId=114&itemId=6&itemId=4&itemId=5&itemId=3&itemId=2&itemId=1&itemId=7&itemId=105&itemId=106&itemId=44&itemId=40&itemId=42&itemId=24&itemId=20&itemId=18&itemId=109&itemId=108&itemId=107&itemId=206&itemId=25&itemId=30&itemId=33&itemId=34"
        else: raise ValueError("costs_by must be either 'city' or 'country'")
        page = requests.get(url).content
        tree = etree.HTML(page)

        # Find table and get cokumn names along with data
        table = tree.find('.//table[@id="t2"]')
        column_names = ["".join(node.find('.//div').itertext()) for node in table.findall('.//th')]
        data = [[node.text for node in row.findall('.//td')] for row in table.findall('.//tr')]

        # Create DataFrame
        df = pd.DataFrame(data, columns=column_names)

        # Find the city or country names and add them to the DataFrame
        elements = tree.findall('.//td/a')
        names = [element.text for element in elements]

        if by == "city":
            df["City"] = names[1:] # First two values are irrelevant, one will be deleted later anyways, so delete only one here
        elif by == "country":
            df["Country"] = names

        # Drop Rank column and first value row (empty)
        df.drop("Rank", axis=1, inplace=True)
        df.drop(df.index[0], inplace=True)
        df = df.loc[:,~df.columns.duplicated()].copy()
        df = df.replace('-',np.NaN)
        
        # Rename columns
        column_dict = {
            'Meal, Inexpensive Restaurant':'meal_inexp',
            'Meal for 2 People, Mid-range Restaurant, Three-course':'meal_mid',
            'McMeal at McDonalds (or Equivalent Combo Meal)':'meal_mcdo',
            'Domestic Beer (0.5 liter draught)':'beer_dom',
            'Imported Beer (0.33 liter bottle)':'beer_imp', 
            'Coke/Pepsi (0.33 liter bottle)':'soda',
            'Water (0.33 liter bottle) ':'water_small', 
            'Milk (regular), (1 liter)':'milk',
            'Loaf of Fresh White Bread (500g)':'bread', 
            'Eggs (regular) (12)':'eggs',
            'Local Cheese (1kg)':'cheese', 
            'Water (1.5 liter bottle)':'water_large',
            'Bottle of Wine (Mid-Range)':'wine', 
            'Domestic Beer (0.5 liter bottle)':'beer_large',
            'Cigarettes 20 Pack (Marlboro)':'cigarettes',
            'One-way Ticket (Local Transport)':'transport_ticket', 
            'Chicken Fillets (1kg)':'chicken',
            'Monthly Pass (Regular Price)':'transport_month', 
            'Gasoline (1 liter)':'gas',
            'Volkswagen Golf 1.4 90 KW Trendline (Or Equivalent New Car)':'car_vw',
            'Apartment (1 bedroom) in City Centre':'apartment_1room_c',
            'Apartment (1 bedroom) Outside of Centre':'apartment_1room_o',
            'Apartment (3 bedrooms) in City Centre':'apartment_3room_c',
            'Apartment (3 bedrooms) Outside of Centre':'apartment_3room_o',
            'Basic (Electricity, Heating, Cooling, Water, Garbage) for 85m2 Apartment':'electricity_water',
            'Internet (60 Mbps or More, Unlimited Data, Cable/ADSL)':'internet',
            'Mobile Phone Monthly Plan with Calls and 10GB+ Data':'phone_plan',
            'Fitness Club, Monthly Fee for 1 Adult':'gym',
            'Tennis Court Rent (1 Hour on Weekend)':'tennis',
            'Cinema, International Release, 1 Seat':'cinema',
            '1 Pair of Jeans (Levis 501 Or Similar)':'jeans',
            '1 Summer Dress in a Chain Store (Zara, H&M, ...)':'dress',
            '1 Pair of Nike Running Shoes (Mid-Range)':'shoes_running',
            '1 Pair of Men Leather Business Shoes':'shoes_business',
            'Price per Square Meter to Buy Apartment in City Centre':'sqm_center',
            'Price per Square Meter to Buy Apartment Outside of Centre':'sqm_suburbs',
            'Average Monthly Net Salary (After Tax)':'salary',
            'Mortgage Interest Rate in Percentages (%), Yearly, for 20 Years Fixed-Rate':'mortgage',
            'Taxi Start (Normal Tariff)':'taxi_start', 
            'Taxi 1km (Normal Tariff)':'taxi_km',
            'Taxi 1hour Waiting (Normal Tariff)':'taxi_hour', 
            'Apples (1kg)':'apples', 
            'Oranges (1kg)':'oranges',
            'Potato (1kg)':'potato', 
            'Lettuce (1 head)':'lettuce', 
            'Cappuccino (regular)':'cappuccino',
            'Rice (white), (1kg)':'rice', 
            'Tomato (1kg)':'tomato', 
            'Banana (1kg)':'banana', 
            'Onion (1kg)':'onion',
            'Beef Round (1kg) (or Equivalent Back Leg Red Meat)':'beef',
            'Toyota Corolla Sedan 1.6l 97kW Comfort (Or Equivalent New Car)':'car_toyota',
            'Preschool (or Kindergarten), Full Day, Private, Monthly for 1 Child':'kindergarten',
            'International Primary School, Yearly for 1 Child':'primary_school'
            }
        
        if by=="country":
            column_dict["Country"]="country"
        elif by=="city":
            column_dict["City"]="city"
        
        df.rename(columns=column_dict, inplace=True)

        # Predict missing values
        df = self.predict_missing_values(df)

        return df

"""
numbeoScraper = numbeoScraper()
costs_by_country = numbeoScraper.get_costs(by = "country", currency = "EUR")
costs_by_city = numbeoScraper.get_costs(by = "city", currency = "EUR")
print(costs_by_country)
print(costs_by_city)
"""