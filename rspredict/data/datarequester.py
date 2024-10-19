# %% [markdown]
# # **About**
# 
# |Section|Details|
# |---|---|
# |Script|rs-data-requester|
# |Description|rs-data-requester is used to retrieve historical price data for items in Runescape 3. This data will be transformed to predict future item prices.|
# |Author|Andrew Yang|

# %% [markdown]
# # **Setup**

# %%
import requests # use to retrieve data from API
import math
import pandas as pd
import datetime
from enum import Enum
from scipy.signal.windows import exponential

# %% [markdown]
# # **Classes**

# %%
class RSGameBase(Enum):
    """
    A enum class to force conformity to either Runescape or Old School Runescape when retrieving data.

    This is based on the Weird Gloop API that provides Grand Exchange data, which can have two options: 

    rs (Runescape 3)
    osrs (Old School Runescape)
    """
    rs = "rs"
    osrs = "osrs"

# %%
class RSDataFilter(Enum):
    """
    A enum class that is used to modify the extend of item price data retrieved.

    This is based on the Weird Gloop API that provides Grand Exchange data, which has three options: 

    all (all price data)
    last90d (last 90 days)
    sample
    """

    all = "all"
    last90d = "last90d"
    sample = "sample"

# %%
class RSDataRequester:
    """
    A object class used to retrieve Runescape Grand Exchange item price data.
    ...

    Attributes
    ---
    show_debug : bool
        Used to show information useful for debugging.
    integrate_social : bool
        Boolean setting for integrating social media information into the final dataset.
    diff_data : bool
        Boolean setting for including differenced features in the final dataset.
    ma_data : bool
        Boolean setting for including moving average features in the final dataset.
    game_base : RSGameBase
        Enum used to represent the target game the API will get price data for: RS or OSRS.
    data_filter : RSDataFilter 
        Enum used to represent the extent of price data the API will get: all, the last 90 days, or a sample.

    Methods
    ---
    set_game_base(str setting):
        Sets the object's game base to either OSRS or RS for API calls.
    set_data_filter(str setting):
        Sets the object's data filter to the last 90 days, a sample, or all historical data for API calls.

    
    """

    show_debug = False # Object setting for debugging.
    integrate_social = False # Object setting for integrating social media information into the model.
    # diff_data = False # Object setting for getting differented data for each record.
    # ma_data = False # Object setting for getting moving average data for each record.
    game_base = RSGameBase.rs # API can have two options: rs (Runescape 3) or osrs (Old School Runescape).
    data_filter = RSDataFilter.all # API has three options: all (all price data), last90d (last 90 days), and sample. 
    
    
    def __init__(self): 
        self.show_debug = False
        self.integrate_social = False
        # self.diff_data = False
        # self.ma_data = False
        self.game_base = RSGameBase.rs
        self.data_filter = RSDataFilter.all

    def set_game_base(self, setting):
        """
        Sets the object's game base to either OSRS or RS for API calls.

        Parameters
        ---
        setting : string
            String representing the game base setting.
        """

        if setting.lower() == "osrs":
            self.game_base = RSGameBase.osrs
            return
        
        self.game_base = RSGameBase.rs
        if setting.lower() != "rs":
            print(f"RSDataRequester: {setting} is an invalid game base; defaulting to the 'rs' game base.")  

    def set_data_filter(self, setting):
        """
        Sets the object's data filter to the last 90 days, a sample, or all historical data for API calls.
        
        Parameters
        ---
        setting : string
            String representing the data filter setting.
        """

        if setting.lower() == "last90d":
            self.data_filter = RSDataFilter.last90d
        elif setting.lower() == "sample":
            self.data_filter = RSDataFilter.sample
        
        self.data_filter = RSDataFilter.all
        if setting.lower() != "all":
                print(f"RSDataRequester: {setting} is an invalid data filter; defaulting to the 'all' data filter.")
    
    def get_item_historical_prices(self, item_id):
        """
        Uses an item id to return the relevant price info of an item over time.).

        Parameters
        ---
        item_id : int
            The Runescape item id.

        Returns
        ---
        dict (str id, int price, int volume, int timestamp):
            Returns the item's id, price, and volume (if available) on a particular day as determined by the unix timestamp.
        """
        
        # The RS3 Wiki uses Weird Gloop for their API, and includes support for retrieving their stored Grand Exchange data.
        # We can avoid request limitations with Jagex's own Grand Exchange API, and get all historical data.
        request_prices_base = f"https://api.weirdgloop.org/exchange/history/{self.game_base.value}/{self.data_filter.value}"
        #print(f"Historical GE prices request endpoint: {request_prices_base}")

        # Call the API to get the item's price info.
        r_prices = requests.get(request_prices_base, params = {"id": item_id})
        if self.show_debug:
            print(f"Status of item {item_id}: {r_prices.status_code}")    
        
        return r_prices.json()[f"{item_id}"] 

    def confirm_item_category(self, item_category):
        """
        Verifies the inputed item category is included.

        See the following link for all item categories (https://runescape.wiki/w/Application_programming_interface#category).

        Parameters
        ---
        item_category : int
            The Runescape item category.

        Raises
        ---
        ValueError
            If the item_category parameter is not within the existing list of item category ids.
        """
        category_ids = range(0, 44, 1) # ONLY RS: RS item categories are just ints internally
        if self.show_debug: 
            print(f"All item category ids: {list(category_ids)}")

        if item_category not in category_ids:
            raise ValueError(f"RSDataRequester: The requested category id is not supported; Item categories must be between {category_ids.start} and {category_ids.stop}, inclusive.")
    
    def get_category_alpha(self, item_category):
        """
        Retrieves an alpha (first letter) keyed dictionary of all the items in an item category. This is used to iterate through the category.

        See the following link for all item categories (https://runescape.wiki/w/Application_programming_interface#category).

        Parameters
        ---
        item_category : int
            The Runescape item category.

        Returns
        ---
        list (dict (str letter, int items)):
            Returns a list of dictionaries, which are made up of an alpha and number of items under said alpha.
        """

        # Grabs a list of dictionaries that show how many items are under each "alpha" (character)
        request_category_base = "https://services.runescape.com/m=itemdb_rs/api/catalogue/category.json?"
        r_category = requests.get(request_category_base, params = {"category": item_category})
        if self.show_debug: 
            print(r_category.status_code)

        # Retrieve alpha count, and show if debug setting is enabled.
        category_alpha_dict = r_category.json()["alpha"]
        if self.show_debug: 
            print(f"Item alpha dict: ")
            display(category_alpha_dict)

        return category_alpha_dict

    def get_category_alpha_item_ids(self, req_category, req_alpha, req_page):
        """
        Returns a list of item ids for a given category id, alpha letter, and page number.

        See the following link for all item categories (https://runescape.wiki/w/Application_programming_interface#category).

        Parameters
        ---
        req_category : int
            The Runescape item category.
        req_alpha : string
            The alpha (first letter of the item name).
        req_page : int
            The page to refer to in the alpha dict.    

        Returns
        ---
        list (dict (str letter, int items)):
            Returns a list of dictionaries, which are made up of an alpha and number of items under said alpha.
        """

        # Define API endpoint for getting item info.
        request_items_base = "https://services.runescape.com/m=itemdb_rs/api/catalogue/items.json?"
        r_items = requests.get(request_items_base, params = {"category": req_category, "alpha": req_alpha, "page": req_page})
        if self.show_debug:
            print(f"Status of item category|alpha|page ({req_category}|{req_alpha}|{req_page}): {r_items.status_code}")
        return [i["id"] for i in r_items.json()["items"]]
    
    def get_category_item_ids(self, item_category):
        """
        Returns a list of item ids for a given category id.

        See the following link for all item categories (https://runescape.wiki/w/Application_programming_interface#category).

        Parameters
        ---
        item_category : int
            The Runescape item category.

        Returns
        ---
        list (int item_ids):
            Returns a list of ints, which are item ids.
        """

        # Confirm that the inputed item_category is acceptable.
        self.confirm_item_category(item_category) 

        # Get the item category alpha dict (dictionary with all items organized by first letter).
        category_alpha_dict = self.get_category_alpha(item_category) 

        # For each alpha (starting letter).
        category_item_ids = []
        for a in category_alpha_dict:
            if a["items"] <= 0: # If there is no items in this alpha, skip it.
                continue
            
            # Otherwise:
            req_requests =  math.ceil(a["items"] / 12) # Determine the # of times to request the API for all items.
            for page in range(1, req_requests + 1, 1):
                category_item_ids.extend(self.get_category_alpha_item_ids(item_category, a["letter"], page))
        
        return category_item_ids

    def get_all_categories_item_ids(self, categories = []):
        """
        Returns a list of item ids for a given list of category ids.

        See the following link for all item categories (https://runescape.wiki/w/Application_programming_interface#category).

        Parameters
        ---
        categories : list(ints)
            The Runescape item category.

        Returns
        ---
        list (int):
            Returns a list of ints, which are item ids.
        """
        all_item_ids = []
        for c in categories:
            all_item_ids.extend(self.get_category_item_ids(c))

        return all_item_ids
    
    def get_raw_historical_prices(self, indiv_item_ids = [], categories = []):
        """
        Returns a Pandas dataframe including item prices and potentially volume at a specific time point.

        See the following link for all item categories (https://runescape.wiki/w/Application_programming_interface#category).

        Parameters
        ---
        indiv_item_ids : list(ints)
            A list of item ids.
        categories : list(ints)
            A list of targeted item category ids.

        Returns
        ---
        Pandas dataframe(string id, int price, float volume, int timestamp):
            Returns a dataframe that includes item id, item price and volume at a unix timestamp.
        """
        
        all_set = set(self.get_all_categories_item_ids(categories)).union(set(indiv_item_ids))

        all_prices = []
        for id in all_set:
            all_prices.extend(self.get_item_historical_prices(id))

        return pd.DataFrame(all_prices)
    
    # Convert unix timestamp to date.
    def unix_to_date_string(self, ts):
        return datetime.datetime.fromtimestamp(ts/1000, datetime.UTC).strftime('%Y-%m-%d')
    
    # Convert unix timestamp to date.
    def unix_to_datetime(self, ts):
        return datetime.datetime.fromtimestamp(ts/1000, datetime.UTC)
    
    # Determine if a unix timestamp represents a weekend or weekday.
    def unix_is_weekday(self, ts):
        return 1 if datetime.datetime.fromtimestamp(ts/1000, datetime.UTC).weekday() < 5 else 0
    
    def get_social_media_data(self, ref_df = None):
        """
        Returns a dataframe containing info on recent Runescape 3 updates.

        Returns
        ---
        Pandas dataframe():
            Returns social media update info.
        """
        
        # The RS3 Wiki uses Weird Gloop for their API; this endpoint gets all social media information.
        request_socials_base = f"https://api.weirdgloop.org/runescape/social"
        halt = False # Used in while loop - API response includes if there are additional pages left.
        max_iter = 100 # Failsafe.

        page = 1
        social_dict_list = []

        while halt != True and page <= max_iter: # As long as we haven't halted the process and page less than the max allowed
            r_social = requests.get(request_socials_base, params = {"page": page}) # Request social media info from API.
            
            if self.show_debug:
                print(f"Status of page {page}: {r_social.status_code}")
            page += 1

            if r_social.json()["pagination"]["has_more"] != True: # If the response tells use there's no more pages, halt the loop.
                halt = True

            social_dict_list.extend(r_social.json()["data"]) # Add dictionaries to our list.

        # Get social media list of dicts into a dataframe.
        social_df = pd.DataFrame(social_dict_list)

        # Create string version of date to link social media info to specific dates.
        social_df["date_string"] = social_df["dateAdded"].apply(lambda x: str(x)[:10]) #.map(datetime_to_string)

        # Enrich social media history dataframe based on title of media item:
        #   Launch usually indicates a new release.
        #   Bosses are big drop sources of items, and may affect our items of interest.
        #   Quests show info about an upcoming Runescape quest. These quests may unlock new things which require our items of interest.
        #   Event usually indicates a new upcoming events.
        #   Double XP tells players when the next Double XP is coming up, and is a known market mover.
        #   Update is more general, but can include information on changes for any of the above info... or something irrelevant.
        social_df["launch_update"] = social_df["title"].apply(lambda x: "Launch" in x if x is not None else False)
        social_df["boss_update"] = social_df["title"].apply(lambda x: "Boss" in x if x is not None else False)
        social_df["quest_update"] = social_df["title"].apply(lambda x: "Quest" in x if x is not None else False)
        social_df["event_update"] = social_df["title"].apply(lambda x: "Event" in x if x is not None else False)
        social_df["dxp_update"] = social_df["title"].apply(lambda x: "Double XP" in x if x is not None else False)
        social_df["general_update"] = social_df["title"].apply(lambda x: "Update" in x if x is not None else False)

        # Prepare date bounds with socials and the price dataset.
        earliest_update_date = social_df.date_string.min()
        recent_update_date = social_df.date_string.max()
        earliest_price_date = ref_df.date_string.min() if ref_df is not None else social_df.date_string.min()
        recent_price_date = ref_df.date_string.max() if ref_df is not None else social_df.date_string.max()
        print(f"Earliest update: {earliest_update_date}; Most recent update: {recent_update_date}.")
        print(f"Earliest price: {earliest_price_date}; Most recent price: {recent_price_date}.")   
        
        # Use date bounds to expand socials/update info for all dates of the price dataset
        sim_min_date = datetime.datetime.strptime(min(earliest_update_date, earliest_price_date), '%Y-%m-%d')
        sim_max_date = datetime.datetime.strptime(max(recent_update_date, recent_price_date), '%Y-%m-%d')

        # Sets iteration range.
        range_days = pd.date_range(sim_min_date, sim_max_date).to_list()
        print(f"Iterate over {len(range_days)} days.")

        update_concat_list = []
        for d in range_days:
            update_concat_list.append([d.strftime('%Y-%m-%d'), False, False, False, False, False, False])

        # Prepare social media data df
        social_temp_df = social_df[['date_string', 'launch_update', 'quest_update', 'event_update', 'dxp_update', 
                            'general_update', 'boss_update']]
        social_append_df = pd.DataFrame(update_concat_list, columns = social_temp_df.columns)
        social_enriched_df = pd.concat([social_temp_df, social_append_df], axis = 0)

        # Get aggregate update info by date.
        social_agg_df = social_enriched_df.groupby(["date_string"], as_index=False).any()

        # Calculate moving averages for 7, 14, and 30 days and put into dataframes.
        # FUTURE UPDATE - experiment with different window weight methods (like exponential or gaussian), to represent decaying influence of update.
        social_agg_df_7_ma = social_agg_df[social_agg_df.columns[social_agg_df.columns!='date_string']].rolling(7, 1, False, "exponential").mean()
        social_agg_df_14_ma = social_agg_df[social_agg_df.columns[social_agg_df.columns!='date_string']].rolling(14, 1, False, "exponential").mean()
        social_agg_df_30_ma = social_agg_df[social_agg_df.columns[social_agg_df.columns!='date_string']].rolling(30, 1, False, "exponential").mean()

        # Rename columns for clarity.
        social_agg_df_7_ma.columns = [f"{c}_7_ma" for c in social_agg_df_7_ma.columns.to_list()]
        social_agg_df_14_ma.columns = [f"{c}_14_ma" for c in social_agg_df_14_ma.columns.to_list()]
        social_agg_df_30_ma.columns = [f"{c}_30_ma" for c in social_agg_df_30_ma.columns.to_list()]

        # Creates final aggregate information.
        social_agg_final_df = pd.concat([social_agg_df, social_agg_df_7_ma, social_agg_df_14_ma, social_agg_df_30_ma], axis=1)

        return social_agg_final_df
    
    def get_historical_prices(self, indiv_item_ids = [], categories = []):
        """
        Returns a Pandas dataframe with additional features, including differenced/moving averages.

        Parameters
        ---
        indiv_item_ids : list(ints)
            A list of item ids.
        categories : list(ints)
            The Runescape item category.

        Returns
        ---
        Pandas dataframe(string id, int price, float volume, int timestamp...):
            Returns a dataframe that includes item id, item price and volume at a unix timestamp, as well as differenced/moving averaged prices.
        """
        
        # get base historical prices
        ge_df = self.get_raw_historical_prices(indiv_item_ids, categories)

        # add in weekday/weekend info, adjust timestamp to date
        ge_df["date"] = ge_df['timestamp'].map(self.unix_to_datetime)
        ge_df["date_string"] = ge_df['timestamp'].map(self.unix_to_date_string)
        ge_df["weekday"] = ge_df['timestamp'].map(self.unix_is_weekday)

        # Get differenced data by 1 day, 1 week, 2 weeks, and ~ 1 month (comparing price for each item by their id). Great for time series.
        ge_df["diff_1_day"] = ge_df.groupby("id")["price"].diff(1)
        ge_df["diff_7_day"] = ge_df.groupby("id")["price"].diff(7)
        ge_df["diff_14_day"] = ge_df.groupby("id")["price"].diff(14)
        ge_df["diff_30_day"] = ge_df.groupby("id")["price"].diff(30)

        # Get 1 week, 2 week, and ~1 month moving average (comparing price for each item by their id).
        ge_df["ma_7_day"] = ge_df.groupby("id")["price"].rolling(7, 1).mean().reset_index(drop=True)
        ge_df["ma_14_day"] = ge_df.groupby("id")["price"].rolling(14, 1).mean().reset_index(drop=True)
        ge_df["ma_30_day"] = ge_df.groupby("id")["price"].rolling(30, 1).mean().reset_index(drop=True)

        # Get the difference between 1 week, 2 week, and ~1 month moving average for each day.
        ge_df["diff_ma_7_day"] = ge_df.groupby("id")["ma_7_day"].diff(1)
        ge_df["diff_ma_14_day"] = ge_df.groupby("id")["ma_14_day"].diff(1)
        ge_df["diff_ma_30_day"] = ge_df.groupby("id")["ma_30_day"].diff(1)

        # Create the following conditions to filter ge_df:
        # cond1 - If the difference in moving average at a dat for 1 week, 2 weeks, and 1 month are = 0, the date's price is likely the initial Jagex-set price.
        # cond2 - Similarly, remove rows with null values in difference in moving average.
        # cond3 - Finally, as a precaution, remove null rows for price differences at 1 day, 1 week, 2 weeks, and 1 month.

        cond1 = (ge_df["diff_ma_7_day"] != 0) & (ge_df["diff_ma_14_day"] != 0) & (ge_df["diff_ma_30_day"] != 0)
        cond2 = (ge_df["diff_ma_7_day"].notnull()) & (ge_df["diff_ma_14_day"].notnull()) & (ge_df["diff_ma_30_day"].notnull())
        cond3 = (ge_df["diff_1_day"].notnull()) & (ge_df["diff_7_day"].notnull()) & (ge_df["diff_14_day"].notnull())& (ge_df["diff_30_day"].notnull())

        # Filter original ge prices dataframe based on the above conditions to get clean values.
        ge_enriched_df = ge_df[cond1 & cond2 & cond3].copy().reset_index()

        ge_final_df = ge_enriched_df
        if self.integrate_social:
            social_df = self.get_social_media_data(ge_final_df)
            ge_final_df = ge_enriched_df.merge(social_df, left_on='date_string', right_on='date_string', how = "left")

        return ge_final_df
    
    def get_time_series_historical_prices(self, indiv_item_ids = [], categories = []):
        """
        Returns a Pandas dataframe stripped down to its base time series.

        Parameters
        ---
        indiv_item_ids : list(ints)
            A list of item ids.
        categories : list(ints)
            The Runescape item category.

        Returns
        ---
        Pandas dataframe(string id, int price, string date):
            Returns a dataframe that includes item id, item price, and the date.
        """
        
        # get base historical prices
        ge_df = self.get_raw_historical_prices(indiv_item_ids, categories)

        # get datetimes
        ge_df["date"] = ge_df['timestamp'].map(self.unix_to_datetime)

        # Filter original ge prices dataframe based on the above conditions to get clean values.
        ge_ts_df = ge_df[["id", "price", "date"]]
        return ge_ts_df
    
    def export_data(self, df, folder_path):
        # Create file based on date.
        today = datetime.date.today().strftime('%Y-%m-%d')
        print(f"Current date: {today}")

        filename = f"ge-prices-{today}.csv"
        print(f"Final filename: {filename}")

        # Export file.
        df.to_csv(f"{folder_path}{filename}", index=False)  



