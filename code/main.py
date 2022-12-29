
#importing data
from data import *
from map_styles import *
from location import *

from random import randint
from datetime import datetime
from time import sleep
from typing import List
from dataclasses import dataclass
import json
import os

import pandas as pd
import geopandas as gpd
import folium
from pyodide.http import open_url
import js
import asyncio
from requests import request

#ignore warnings
import warnings
warnings.filterwarnings('ignore')

#constants
print('INFO: Loading Bondaries')
FSAS_GPD = gpd.read_file('boundaries.geojson').rename(columns={'POSTCODE': 'FSA'})
FSAS_GPD['centroid'] = FSAS_GPD.centroid

print('INFO: Creating Paths')
#create a directory to store the scraped data
os.mkdir(os.getcwd()+'/jsons/')
JSONS_PATH = os.getcwd()+'/jsons/'

print('INFO: Loading Locations')
#Initiate all the locations
LOCATIONS = []
for loc in LOCATIONS_DICT.values():
    LOCATIONS.append(Location(loc['retailerSiteId'], loc['retailOutletLocationSk'], loc['name'], loc['acronym'], loc['region'], loc['business'], loc['kind'], loc['address'], loc['geo_coordinates']))

class FSA: 
    '''
    A class to represent canadian forward sortation areas i.e. FSA.
    ...
    Attributes
    ----------
    Methods
    ----------
    '''
    def __init__(self, fsa_name: str) -> None:
        self.fsa_name: str = fsa_name
        self.geometry = FSAS_GPD[FSAS_GPD['FSA'] == fsa_name].geometry.values
        self.centroid = FSAS_GPD[FSAS_GPD['FSA'] == fsa_name]['centroid'].values

    def __repr__(self) -> str:
        return self.fsa_name

class Zone: 
    '''
    A class to represent OSP Zone areas, derived from the csv file that can be exported from OSP's website.
    link: https://delivery-area.voila.osp.tech/delivery-zones
    ...
    Attributes
    ----------
    Methods
    ----------
    '''
    def __init__(self, serviced_by_location: Location, zone_name: str, zone_business: str, zone_fsas: List) -> None:
        self.serviced_by: Location = serviced_by_location
        self.name: str = zone_name
        self.business: str = zone_business
        self.fsas: List[FSA] = []

        for fsa in zone_fsas:
            self.fsas.append(FSA(fsa))
        
    def __repr__(self) -> str:
        return f"Zone: {self.name} | Serviced by: {self.serviced_by.acronym}"
    
    @property
    def geometry(self):
        geometries = []
        for fsa in self.fsas:
            #work around to ignore empty geometries
            if len(fsa.geometry) > 0:
                geometries.append(fsa.geometry[0])
        return gpd.GeoSeries(geometries).unary_union

    @property
    def centroid(self):
        return self.geometry.centroid

def process_json_reponse(city, data_json):
    filtered_data = []
    for obs in data_json['sevendays']['periods']:
        filtered_data.append({ 
                "scrape_date" : datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "placecode" : city['placecode'],
                
                "city_prov" : city['prov'],
                "city_name" : city['city'],
                "city_lat" : city['lat'],
                "city_lon" : city['lon'],
                "city_zone" : city['zone'],
                
                "date_complete" : obs['cdate'],
                "Date" : obs['super_short_dayanddate'],
                "weekday" : obs['super_short_day'],
                "month_day" : obs['super_short_date'],

                "Period" : "AM",

                "Wind Direction" : obs['wd'],
                "Wind Speed" : int(obs['metric_windSpeed']),
                "Wind Speed Unit" : obs['metric_windSpeed_unit'],
                "Wind Gust" : int(obs['windGust']),
                "Wind Gust Unit" : obs['gust_unit'],
                "Feels Like" : int(obs['metric_feelsLike']),
                "Feels Like Unit" : obs['metric_feelsLike_unit'],
                "Temperature" : int(obs['tmac']),
                "Temperature Unit" : obs['metric_temperatureMax_unit'],
                "Rain" : obs['r'],
                "Rain Unit" : obs['ru'],
                "Snow" : obs['s'],
                "Snow Unit" : obs['su'],
                "POP" : int(obs['pdp']),
                "Description" : obs['itd'],
                })
        
        filtered_data.append({ 
                "scrape_date" : datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "placecode" : city['placecode'],
                
                "city_prov" : city['prov'],
                "city_name" : city['city'],
                "city_lat" : city['lat'],
                "city_lon" : city['lon'],
                "city_zone" : city['zone'],
                
                "date_complete" : obs['cdate'],
                "Date" : obs['super_short_dayanddate'],
                "weekday" : obs['super_short_day'],
                "month_day" : obs['super_short_date'],

                "Period" : "PM",

                "Wind Direction" : obs['windDirectionNight'],
                "Wind Speed" : int(obs['windSpeedNight_kmh']),
                "Wind Speed Unit" : obs['windSpeedNight_unit'],
                "Wind Gust" : int(obs['windGustNight']),
                "Wind Gust Unit" : obs['gustNight_unit'],
                "Feels Like" : int(obs['feelsLikeNight']),
                "Feels Like Unit" : obs['feelsLikeNight_unit'],
                "Temperature" : int(obs['tmic']),
                "Temperature Unit" : obs['metric_temperatureMin_unit'],
                "Rain" : obs['rr'],
                "Rain Unit" : obs['ru'],
                "Snow" : obs['sr'],
                "Snow Unit" : obs['su'],
                "POP" : int(obs['pnp']),
                "Description" : obs['itn']})
                
    return filtered_data

def get_html_sandwich(city, df_weather):
    ##filter weather_df to get only that town's data
    data_df = df_weather[df_weather['placecode'] == city['placecode']]
    html_top_bun = f'''
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    </head>
    <body>
    <h3> {city['city']} </h3>
    <i> Data Source: The Weather Network. Last Update: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} </i>
    <br>
    </body>
    </html>
    '''

    html_table = f'''
    <html>
    <head><title></title>
    <style>
    #summary {{
    font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
    font-size: 12px;
    border-collapse: collapse;
    width: 100%;
    text-align:center;
    vertical-align:middle;
    }}

    #summary td, #summary th {{
    border-collapse:collapse;
    border: 1px solid #9ABAD9;
    border-spacing: 2px;
    padding: 2px;
    text-align:center;
    vertical-align:middle;
    }}

    #summary tr:nth-child(even){{background-color: #f2f2f2;}}

    #summary th {{
    padding-top: 12px;
    padding-bottom: 12px;
    text-align: left;
    background-color: #409cff;
    color: white;
    border-color: #9abad9;
    text-align:center;
    vertical-align:middle;
    }}
    </style>
    </head>
    <body>
        {data_df[['Date', 'Period', 'Description', 'Feels Like', 'Temperature', 'Rain', 'Snow', 'POP', 'Wind Direction', 'Wind Speed', 'Wind Gust']].head(14).to_html(table_id="summary", index=False)}
    </body>
    </html>.
    '''
    return ''.join([html_top_bun, html_table])

def clear_folder(path):
    for i in os.listdir(path):
        os.remove(i)

async def scrape_data(cities, path):
    total_cities = len(cities)
    for i, city in enumerate(cities): 
        #TODO error handling in case data can't get fetched
        #data = await json.load(open_url(f"https://www.theweathernetwork.com/api/data/{city['placecode']}/"))
        response = request(f"https://www.theweathernetwork.com/api/data/{city['placecode']}/")
        data = response.json()
        with open(f"{path+city['placecode']}.json", "w") as file:
            await json.dump(data, file)
        js.document.getElementById("refresh_progress").style.width = str((len(os.listdir(path))/total_cities)*100)+'%'

def refresh_data(cities, path):
    clear_folder(path)
    asyncio.ensure_future(scrape_data(cities, path))

def main():    
    print(os.listdir(JSONS_PATH))
        #jsons.extend(process_json_reponse(city, data))
        #print(city['city'])
    #
        #df_weather = pd.DataFrame(jsons)

    #all_fsas = []
    #col_zones: List[Zone] = []
    #for key, value in ZONES.items():
    #    zone_location = "CFC"
    #    zone_fsas = value
    #    zone_business = "CFC"
    #    col_zones.append(Zone(zone_location, key, zone_business, zone_fsas))
    #    all_fsas.extend(value)

#
    ##instantiate map
    #m = folium.Map(location=[45.4769531, -73.7979043], zoom_start=8, tiles='cartodb positron')
#
    #folium.raster_layers.WmsTileLayer(
    #    url = 'https://geo.weather.gc.ca/geomet?',
    #    layers = 'RADAR_1KM_RSNO',
    #    transparent = True, 
    #    control = True,
    #    fmt="image/png",
    #    name = 'Canada Weather Radar Snow',
    #    overlay = True,
    #    show = False,
    #    opacity = 0.5
    #).add_to(m)
#
    #legend_html = '''
    #{% macro html(this, kwargs) %}
    #<div style="
    #    position: fixed; 
    #    bottom: 50px;
    #    left: 50px;
    #    width: 250px;
    #    height: auto;
    #    z-index:9999;
    #    font-size:14px;
    #    ">
    #<img src="https://geo.weather.gc.ca/geomet?version=1.3.0&service=WMS&request=GetLegendGraphic&sld_version=1.1.0&layer=RADAR_1KM_RSNO&format=image/png&STYLE=RADARURPPRECIPS14-LINEAR">
    #</div>
    #{% endmacro %}
    #'''
    #legend = folium.branca.element.MacroElement()
    #legend._template = folium.branca.element.Template(legend_html)
#
    #folium.raster_layers.WmsTileLayer(
    #    url = 'https://geo.weather.gc.ca/geomet?',
    #    layers = 'RADAR_1KM_RRAI',
    #    transparent = True, 
    #    control = True,
    #    fmt="image/png",
    #    name = 'Canada Weather Radar Rain',
    #    overlay = True,
    #    show = False,
    #    opacity = 0.65
    #).add_to(m)
#
    ##change map tile
    #folium.TileLayer('stamentoner').add_to(m)
    #folium.TileLayer('OpenStreetMap').add_to(m)
#
    #zones_group = folium.FeatureGroup(name='OSP Zones').add_to(m)
    ##add the existing zones geometries
    #for zone in col_zones:
    #    fillColor = STYLES[zone.name]['fillColor']
    #    color = STYLES[zone.name]['color']
    #    tooltip = [zone.name]
    #    zones_group.add_child(folium.GeoJson(
    #        data=zone.geometry, 
    #        style_function=lambda x, fillColor=fillColor, color=color: {
    #            "fillColor": fillColor,
    #            "color": color,
    #        },
    #        tooltip=tooltip))
#
    ##add location markers
    #markers_group = folium.FeatureGroup(name="Location Markers").add_to(m)
    #markers_group.add_child(folium.Marker(location=[43.70300, -79.38900], popup='VAUGHAN CFC'))
    #markers_group.add_child(folium.Marker(location=[43.616401, -79.538833], popup='ETB SPOKE'))
    #markers_group.add_child(folium.Marker(location=[45.4769531, -73.7979043], popup='POINTE-CLAIRE CFC'))
    #markers_group.add_child(folium.Marker(location=[46.8400925, -71.2760664], popup='QBC SPOKE'))
    #markers_group.add_child(folium.Marker(location=[45.378810, -75.631818], popup='OTTAWA SPOKE'))
#
    ##add circles for the 
    #weather_observations_group = folium.FeatureGroup(name="Weather Observations").add_to(m)
#
    #for city in CITIES:
    #    pop = get_html_sandwich(city, df_weather)
    #    weather_observations_group.add_child(folium.CircleMarker(location=[city['lat'], city['lon']], popup=pop, radius=10, color='#69b3a2', fill=True, fill_color='#69b3a2'))
#
    #folium.LayerControl().add_to(m)
#
    #m.get_root().add_child(legend)
#
    #fig = folium.branca.element.Figure(height="100%")
    #fig.add_to(m)
#
    #df_summary = df_weather[df_weather['Period']=='AM'].pivot(index=['city_prov', 'city_zone', 'city_name'], columns=['month_day'], values=['Snow'])
#
    #display(HTML(m._repr_html_()), target="folium")

main()