# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 16:08:31 2022

@author: micr
"""
import geopandas as gpd
import xarray as xr
from shapely.geometry import mapping, Polygon
from pydap.client import open_url
from pydap.cas.get_cookies import setup_session
from datetime import timedelta

def opendap_data(start_date,end_date):
    """
    This function establish a openDap connection with Copernicus GLO-SST-L4-NRT-OBS-SST-V2 collection

    Parameters
    ----------
    start_date: datetime
    end_date: datetime

    Returns
    ----------
    data_collection: Xarray

    """ 
    
    url = 'https://nrt.cmems-du.eu/thredds/dodsC/METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2'
    username = 'mchapelarivas'
    password = 'Micr1234!'

    cas_url = 'https://cmems-cas.cls.fr/cas/login'
    session = setup_session(cas_url, username, password)
    
    session.cookies.set("CASTGC", session.cookies.get_dict()['CASTGC'])
    ## OPeNDAP connection
    data_store = xr.backends.PydapDataStore(open_url(url, session=session))
    data_collection  = xr.open_dataset(data_store).sel(time=slice(start_date,end_date+timedelta(days=1)))
    return data_collection 

def get_coastline(aoi,coastline_directory):
    
    """
    This function get the coastline from vector amd clip it to the aoi 
    
    Parameters
    ----------
    data: xarray DataArray
    
    Returns
    ----------
    coastline_aoi: GeoDataFrame

    """ 
    
    coastline_shp = gpd.read_file(coastline_directory)
    
    # Convert it to geodataframe and set coordinate reference system
    polygon_gdf = gpd.GeoDataFrame(gpd.GeoSeries(aoi), columns=['geometry'])
    polygon_gdf = polygon_gdf.set_crs('WGS84')
    
    # Clip coastline shapefile to bounding box extent
    coastline_aoi = gpd.overlay(coastline_shp, polygon_gdf, how='intersection')
    coastline_aoi.to_crs('EPSG:3035', inplace= True)
    
    return coastline_aoi


def polygon_to_gdf(aoi):
    
    """
    Creates the buffer area of 2 km from the coastline
    
    Parameters
    ----------
    coastline: GeoDataFrame
    
    Returns
    ----------
    coastline_buffer: GeoDataFrame

    """ 
    
    polygon_gdf = gpd.GeoDataFrame(gpd.GeoSeries(aoi), columns=['geometry'])    
    polygon_gdf.set_crs('WGS84',inplace=True)

    return polygon_gdf


def get_SST_data(file_path,aoi_gdf):
    
    """
    Reads SST and clips it to the buffer area
    
    Parameters
    ----------
    file_path:str
    aoi_gdf: GeoDataFrame
    
    Returns
    ----------
    data_SST: xarray DataArray

    """ 
               
        
    ds = xr.open_dataset(file_path)
  
    # Extract SST or CHL from file using latitudes and longitudes index
    data_SST = ds['analysed_sst'][0,:,:]
    #Convert from kelving to degree celsius
    data_SST = data_SST - 273.15
    
    # Add latitude and longitude 
    data_SST.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    data_SST.rio.write_crs("WGS84", inplace=True)
                
    # Clip to buffer
    data_SST = data_SST.rio.clip(aoi_gdf.geometry.apply(mapping), aoi_gdf.crs, drop=True)
            
    return data_SST        
            
def get_SST_data_pydap(aoi_gdf,ds):
    
    """
    Reads SST and clips it to the buffer area
    
    Parameters
    ----------
    file_path:str
    aoi_gdf: GeoDataFrame
    
    Returns
    ----------
    data_SST: xarray DataArray

    """ 
    # Extract SST or CHL from file using latitudes and longitudes index
    data_SST = ds['analysed_sst'][0,:,:]
    #Convert from kelving to degree celsius
    data_SST = data_SST - 273.15
    
    # Add latitude and longitude 
    data_SST.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    data_SST.rio.write_crs("WGS84", inplace=True)
                
    # Clip to buffer
    data_SST = data_SST.rio.clip(aoi_gdf.geometry.apply(mapping), aoi_gdf.crs, drop=True)
            
    return data_SST 

def get_CHL_data(file_path,aoi_gdf):
    """
    Reads CHL and clips it to the buffer area
    
    Parameters
    ----------
    file_path:str
    buffer_gdf: GeoDataFrame
    
    Returns
    ----------
    data_CHL: xarray DataArray

    """ 
           
   
    #Read data for CHL
    ds_CHL = xr.open_dataset(file_path)
 
    data_CHL = ds_CHL['CHL'][0,:,:]
    data_CHL = data_CHL.rio.write_crs('WGS84')
    # Clip to buffer
    data_CHL = data_CHL.rio.clip(aoi_gdf.geometry.apply(mapping), aoi_gdf.crs, drop=True)
    #data_CHL = data_CHL.where(data_CHL<0.3,other=np.nan)
            
    
    return data_CHL        


def get_coast_buffer(coastline,buffer_size):
    
    """
    Creates a buffer area around the coastline vector of the size given by
    the user. buffer_size is in km
    
    Parameters
    ----------
    coastline: GeoDataFrame
    buffer_size: float
    Returns
    ----------
    coastline_buffer: GeoDataFrame

    """ 
    
    coastline.to_crs('EPSG:3035', inplace= True)
    coastline['buffer'] = coastline.buffer(buffer_size*1000)
    coastline_buffer = coastline.set_geometry('buffer')
    coastline_buffer.to_crs('WGS84', inplace= True)

    return coastline_buffer