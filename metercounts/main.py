import requests
import logging
import http.client as http_client
from datetime import datetime, time
import pandas as pd
import pytz
import os

from functools import partial
from geopy.geocoders import Nominatim

import pygeohash as pgh


http_client.HTTPConnection.debuglevel = 1
logger = logging.getLogger(__name__)

class McData:
    def __init__(self):
        #self.fac = main_factory()
        pass

    def get_meter_counts(self, now: datetime = None):
        # Note I'm hardcoding the start date to 2019 because thats the
        # latest data available.. we could start at 2010 or something and 
        # watch the data change through time but I think I'd have to do something
        # extra in Grafana... maybe TBD
        payload = {
        'api_key': os.environ['API_KEY'],
        "frequency": "annual",
        'start': '2019', 
        'facets[technology][]': "Advanced Meter Infrastructure",
        'facets[sector][]': "TOT",
        'data[]': 'meters',
        "offset": 0,
        "length": 5000,
        }

        response = requests.get('https://api.eia.gov/v2/electricity/state-electricity-profiles/meters/data/', 
            params=payload)

        json_data = response.json()
        logger.info(f"Retrieved State Electricity rec count {json_data['response']['total']}")
        return json_data

    def create_dataframe_from_response(self, json_data):
        # put that nasty json response into a pretty dataframe
        assert json_data and 'response' in json_data
        df = pd.DataFrame.from_records(json_data['response']['data'])
        df.rename(columns={'meters-units': 'unit', 'meters': 'metercount'}, inplace=True)
        logger.info(f"Dataframe head\n {df.head()}")
        return df

class GeoTool:
    # this is using the free Nominatim service 
    # which is rate limited to 1 request a second so this will take a while 
    # we could stand up our own service but depending on how much of the world
    # you want to be able to geocode it can require a LOT of memory
    geolocator = Nominatim
    geocode = partial
    def __init__(self):
        self.geolocator = Nominatim(user_agent="metercounts")
        self.geocode = partial(self.geolocator.geocode, language="en")

    def gcode_lat(self, location):
        location = f'{location}, US' # Only lookup US state names
        return self.geocode(location).latitude
    
    def gcode_long(self, location):
        # note that I don't know how to make this give me Washington State
        # by default rather than Washington DC.  I could figure it out but for now
        # I just fix the one record in the DB after it generates the data
        location = f'{location}, US' # Only lookup US state names
        return self.geocode(location).longitude
    
    def gcode_geohash(self, latitude, longitude):
        # gimme one of those pretty geohashes
        return pgh.encode(latitude=latitude, longitude=longitude)

class DbHandler:
    def __init__(self):
        now = datetime.utcnow()
        now = datetime.combine(now.date(), time(hour=now.hour), tzinfo=pytz.UTC)
        self.now = now
    
    def insert_df(df):
        from sqlalchemy import create_engine
        engine = create_engine(os.environ['METERCOUNT_DB_URL'])
        df.to_sql(name='metercount', con=engine, index_label='id', if_exists='replace')
        logger.info(f"Upserted {df.shape[0]} rows")


        
if __name__ == "__main__":
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    
    # Go get the data
    json_data = McData().get_meter_counts()
    df = McData().create_dataframe_from_response(json_data)
    # Remove the US row - it is NOT a State and I don't know why they include it
    df = df[df.state != 'US']

    # Prep to geocode the states so Grafana's tool can map them
    geoTool = GeoTool()
    df['latitude'] = df.apply(lambda row: geoTool.gcode_lat(row.stateName), axis=1)
    df['longitude'] = df.apply(lambda row: geoTool.gcode_long(row.stateName), axis=1)
    df['geohash'] = df.apply(lambda row: geoTool.gcode_geohash(row.latitude, row.longitude), axis=1)

    # put it in the db so Grafana sees it
    DbHandler.insert_df(df)