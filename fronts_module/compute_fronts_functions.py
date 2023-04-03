from scipy import ndimage
import cv2 as cv
from shapely.geometry import mapping
import numpy as np
import shapely
import xarray as xr
from fronts_module.input_data_functions import get_SST_data_pydap

def compute_fronts_main(data_collection_date,aoi_gdf,coast_buffer):
    """
    This function computes SST fronts 
    
    Parameters
    ----------
    data_collection_date: xarray DataArray
    aoi_gdf: Geodataframe
    coast_buffer: Geodataframe

    Returns
    ----------
    
    sobel_xarray: xarray DataArray

    """
    SST_data = get_SST_data_pydap(aoi_gdf,data_collection_date)

    # Obtains gradient using sobel operator
    sobel_xr = sobel_gradient(SST_data)

    # Mask areas in the coastline and near the coastline
    # This is needed since, the sobel operator returns the edge between data(sea) and no data(land)


    sobel_xr = sobel_xr.rio.clip(coast_buffer.geometry.apply(shapely.geometry.mapping), coast_buffer.crs, drop=True,invert=True)

    #Cut possible edges
    aoi_edges = aoi_gdf.to_crs('EPSG:3035').boundary.buffer(30*1000)

    sobel_xr = sobel_xr.rio.clip(aoi_edges.to_crs('WGS84').geometry.apply(shapely.geometry.mapping), aoi_gdf.crs, drop=True,invert=True)



    # Filter values below 0.2 gradient magnitude

    sobel_xr= sobel_xr.where(sobel_xr>0.2,other=np.nan)
    sobel_xr= sobel_xr.where(sobel_xr.isnull(),other=1)


    return sobel_xr





def sobel_gradient(data_xarray):
    """
    This function calculates the gradient using the Sobel operator.
    First the data from the xarray is converted to a uint8 image, a gaussian
    filter is applied and the sobel gradient is calculated. 
    Finally the resultant data is stored as an xarray.
    
    Parameters
    ----------
    data_xarray: xarray DataArray
    
    Returns
    ----------
    
    sobel_xarray: xarray DataArray

    """

    data_array = data_xarray.values
    img = data_array.astype(np.uint8)
    img_blur = cv.GaussianBlur(img,(3,3),0)
    dx = ndimage.sobel(img_blur, 0)  # horizontal derivative
    dy = ndimage.sobel(img_blur, 1)  # vertical derivative
    dx = (dx/255)
    dx = dx*np.nanmax(dx)
    dy = (dy/255)
    dy = dy*np.nanmax(dy)

    mag = np.hypot(dx, dy)  # magnitude
    
    sobel_xarray = xr.DataArray(
    data=mag,
    dims=["lat", "lon"],
    coords={'lat':data_xarray.lat.values,'lon':data_xarray.lon.values,'time':data_xarray.time.values} )

    sobel_xarray.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    sobel_xarray.rio.write_crs("WGS84", inplace=True)    
    
    return sobel_xarray
