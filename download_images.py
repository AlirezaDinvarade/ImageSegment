# -*- coding: utf-8 -*-
"""Untitled42.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ujWGpD428t2j3gJhYub-mUym9bVQ8OZd
"""

import ee
service_account = 'geo-test@geotest-317218.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, 'geotest-privkey.json')
ee.Initialize(credentials)

# !apt install gdal-bin python-gdal python3-gdal 
# !pip install rasterio
# !apt install python3-rtree 
# !pip install git+git://github.com/geopandas/geopandas.git
# !pip install descartes

import os
import numpy as np
import rasterio as rio
from rasterio.plot import show
import io
import requests

# library for unzip tiff image that downloaded from google earth engine 
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
import requests

class Processor:
    def __init__(self,start,end,north, south ,East,West, pixles):
      self.start = start
      self.end = end

      self.north = north 
      self.south = south 
      self.East = East 
      self.West = West 
      self.pixles = pixles
      self.polygon = []
     
######################################################################
    def geojson(self): 
      vertical_coords = np.linspace(self.south, self.north, self.pixles + 1)
      horizontal_coords = np.linspace(self.West, self.East, self.pixles + 1)

      North_coords = vertical_coords[1:]
      South_coords = vertical_coords[:-1]
      West_coords = horizontal_coords[:-1]
      East_coords = horizontal_coords[1:]

      coords_list = []
      for i in range(pixles):
        for j in range(pixles):
          coords_list.append([
                [South_coords[i],West_coords[j]],
                [North_coords[i],West_coords[j]],
                [North_coords[i],East_coords[j]],
                [South_coords[i],East_coords[j]],
                [South_coords[i],West_coords[j]],
              ])
          
      for coordinates in coords_list:
        geoJSON = {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "properties": {},
              "geometry": {
                "type": "Polygon",
                "coordinates": [
                      coordinates
                ]
              }
            }
          ]
        }
        coords = geoJSON['features'][0]['geometry']['coordinates']
        self.polygon.append(ee.Geometry.Polygon(coords))
######################################################################
    def get_images_sentinel2(self, coordinates):
      image = (ee.ImageCollection("COPERNICUS/S2")
          .filterDate(self.start, self.end)
          .filterBounds(coordinates)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',10))
          .mean()
          .clip(coordinates))
      return image
######################################################################
    def get_images_Land_use(self, coordinates):
      image = ee.ImageCollection("ESA/WorldCover/v100").first().clip(coordinates) 
      return image
######################################################################
    def get_image_sentinel1(self, coordinates):
      image = (ee.ImageCollection("COPERNICUS/S1_GRD")
          .filterDate(self.start, self.end)
          .filterBounds(coordinates)
          .mean()
          .clip(coordinates))
      return image
######################################################################
    def turn_image_to_raster(self,image, title, coordinate, folder ):
          # download image from google earth engine
          url = image.getDownloadURL(
              params={'name': title, 'scale': 10, 'region': coordinate,
                      'crs': 'EPSG:4326', 'filePerBand': False,
                          'format': 'GEO_TIFF'})
          
          response = requests.get(url)
          with open(folder+title+'.tif', 'wb') as fd:
            fd.write(response.content)

          print('turn_image_to_raster called')
##################################################################################################
    def main(self):

      if not os.path.isdir('lable'):
        os.mkdir('lable')
      if not os.path.isdir('sentinel1'):
        os.mkdir('sentinel1')
      if not os.path.isdir('sentinel2'):
        os.mkdir('sentinel2')

      lable_index = open("lable_index.txt","w+")
      image_index = open("image_index.txt","w+")

      self.geojson()
      k=0
      for polygon in self.polygon:
        lable = self.get_images_Land_use(coordinates = polygon)
        self.turn_image_to_raster(image = lable, title = 'lable'+str(k), coordinate = polygon, folder = './lable/')
        lable_index.write("lable-"+str(k))

        sentinel1 = self.get_image_sentinel1(coordinates = polygon)
        self.turn_image_to_raster(image = sentinel1, title = 'sentinel1-'+str(k), coordinate = polygon, folder = './sentinel1/')
        image_index.write("sentinel1-"+str(k))

        sentinel2 = self.get_images_sentinel2(coordinates = polygon)
        self.turn_image_to_raster(image = sentinel2, title = 'sentinel2-'+str(k), coordinate = polygon, folder = './sentinel2/')
        image_index.write("sentinel2-"+str(k))

        k = k+1
      lable_index.close()
      image_index.close()

start_time = '2020-01-01'
end_time = '2021-01-01'
north = 51.17204187399198
south = 50.42497156149198
East = 36.128738474565694
West = 35.469352596568484
pixles = 20

p1 = Processor(start_time ,end_time,north = north, south = south, East = East, West = West, pixles = pixles)

raster_images = p1.main()

raster = rio.open('/content/lable/Land_use0.tif')
print(raster.count)
raster.shape

type(raster.read())

