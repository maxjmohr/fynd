from lxml import etree
import pandas as pd
import requests

class numbeoScraper:
    ''' Scrape data from numbeo.com '''
    def __init__(self) -> None:
        self.url = "https://www.numbeo.com"

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

        return df

if __name__ == "__main__":
    numbeoScraper = numbeoScraper()
    costs_by_country = numbeoScraper.get_costs(by = "country", currency = "EUR")
    costs_by_city = numbeoScraper.get_costs(by = "city", currency = "EUR")
    print(costs_by_country)
    print(costs_by_city)