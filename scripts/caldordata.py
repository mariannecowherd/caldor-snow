#!/opt/anaconda3/envs/snow/bin/ python3
import xarray as xr
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from dirs import projdir, datadir, bgdir, asodatadir
import numpy as np
import glob
from util import make_modis_ds


# plot style#
stylesheet = '/Users/cowherd/Documents/mplstyles/marianne.mplstyle'

# Load shapefiles
caldor = gpd.read_file(f'{datadir}/vector/caldor.shp')
caldor = caldor.to_crs('epsg:4326')
watershed = gpd.read_file(f'{datadir}/vector/eldoradohuc8.shp')
meta = gpd.read_file(f'{datadir}/caldormeta.csv')
nhd3 = gpd.read_file(f'{datadir}/NHD_H_18020129_HU8_GDB.gdb', driver= 'FileGDB', layer = 'NHDFlowline')
usa = gpd.read_file(f'{bgdir}/geoBoundaries-USA-ADM1_simplified.shp') 
tahoe = gpd.read_file(f'{datadir}/lake-tahoe.geojson')

names = pd.DataFrame(nhd3['gnis_name'])
names = names.fillna(value=np.nan)
mask = names.gnis_name.str.contains('South Fork American').fillna(False)
names['geometry'] = nhd3['geometry']
names['mask'] = mask
sfa_stream = gpd.GeoDataFrame(names)[mask]

caldormeta = gpd.read_file(f'{datadir}/caldormeta.csv')
caldormeta['geometry'] = [Point(float(lon), float(lat)) for lon, lat in zip(caldormeta['lon'], caldormeta['lat'])]
caldormeta = gpd.GeoDataFrame(caldormeta, crs = 'EPSG:4326')
caldormeta_gdf = caldormeta


sfa_watershed = watershed[watershed.name == 'South Fork American']

wlabels2 = pd.DataFrame( {
    'name': ['Upper Mokelumne', 'South Fork American', 'Upper Cosumnes', 'Lake\nTahoe'],
    'x': [-120.110087, -120.541590, -120.958073, -120.07],
    'y': [38.532365, 38.851515, 38.530259, 39.020356]
})


## usgs gage info
geometry = [Point(xy) for xy in zip([-120.3275],[38.76361111111111])]
usgs_loc = gpd.GeoDataFrame({'name':['Kyburz'], 'number':[11439500]}, geometry=geometry, crs='EPSG:4326')


data = {
    'Name': ['Lake Audrain', 'Philipps', 'Caples Lake*', 'Tamarack Flat', 'Alpha*', 'Echo Summit', 'Forni Ridge*'],
    'Acronym': ['ABN', 'PHL', 'CAP', 'TMF', 'ALP', 'ECS', 'FRN'],
    'Latitude': [38.81983, 38.81800, 38.71079, 38.80300, 38.80414, 38.82852, 	38.803970],
    'Longitude': [-120.03932, -120.02700, -120.04158, -120.10300, -120.21564, -120.03898, -120.215919],
    'Elevation [ft]': [7300, 6800, 8000, 6550, 7600, 7450, 7600],
    'Year': [1941, 1941, 1939, 1939, 1965, 1940, None],
    'Agency': ['USFS', 'DWR', 'DWR', 'DWR', 'DWR', 'USFS', 'USBR']
}

cdec = pd.DataFrame(data)
geometry = [Point(lon, lat) for lon, lat in zip(cdec['Longitude'], cdec['Latitude'])]
cdec = gpd.GeoDataFrame(cdec, geometry=geometry, crs='EPSG:4326')

srtm = xr.open_dataarray(f'{datadir}/srtm30_sfa.nc')
srtmlocal = srtm.sel(lon=slice(-124.5, -118.5), lat=slice(37.9, 39.5))
cldrstr = 'ca3858612053820210815'
cldrdate= '20210805_20220723'
mtbs_rdnbr = xr.open_dataset(f'{datadir}/{cldrstr}/{cldrstr}_{cldrdate}_rdnbr.tif')
mtbs_rdnbr = mtbs_rdnbr.rio.reproject('EPSG:4326')


asofn = glob.glob(f'{asodatadir}/*American*/*American*swe_50m.tif')[0]
ds_50m = xr.open_rasterio(asofn).rio.reproject('epsg:4326')
srtm = srtm.rio.write_crs('epsg:4326').rename({'lat':'y','lon':'x'})
srtm_50 = srtm.rio.reproject_match(ds_50m)

slope_data = np.arctan(np.sqrt(np.gradient(srtm.values, axis=0)**2 + np.gradient(srtm.values, axis=1)**2))

# Create a new xarray dataset for the slope
slope_da = xr.DataArray(slope_data, coords=srtm.coords, dims=srtm.dims, name='slope')

# Create an xarray dataset for the slope
slope_50 = xr.Dataset({'slope': np.degrees(slope_da)})
grad_x = np.gradient(srtm, axis=0)
grad_y = np.gradient(srtm, axis=1)
aspect_data = np.arctan2(-grad_x, grad_y) * 180 / np.pi  # Convert to degrees

# Create a new xarray dataset for the aspect
aspect_da = xr.DataArray(aspect_data, coords=srtm.coords, dims=srtm.dims)

# Create an xarray dataset for the aspect
aspect_50 = xr.Dataset({'aspect': aspect_da})

# LFCC data
lfcc_area = xr.open_dataset('../data/lfcc_area.nc')
lfcc_area = lfcc_area.rio.write_crs('epsg:4326')
band_data_rp = lfcc_area.band_data.rio.reproject_match(ds_50m)
log_area_rp =  lfcc_area.log_area.rio.reproject_match(ds_50m)


## modis data ## 
modis_SCF = make_modis_ds(f'{datadir}/modis_SCF/')
modis_SDD = make_modis_ds(f'{datadir}/modis_SDD/')

## field data ##
caldormeta = pd.read_csv('../data/caldormeta.csv').drop(columns = ['camera_serial'])
hobo_camera = pd.read_csv('../data/hobo_camera_id.csv').astype(int)
cameraid = pd.read_csv('../data/camera_id.csv').astype(int)
## merge datasets ## 
merged_df = pd.merge(caldormeta, hobo_camera, on='plot_number', how='left')
merged_df = pd.merge(merged_df, cameraid, on='plot_number', how='left')
merged_gdf = gpd.GeoDataFrame(merged_df, geometry=gpd.points_from_xy(merged_df.lon, merged_df.lat))

## CCSS data ## 
fnsp = glob.glob(f'{datadir}/processed/*_processsed.csv')
monthlySD = np.load(f'{datadir}/monthlySD.npy', allow_pickle = True).item()
cap23 = pd.read_csv(f'{datadir}/cap23.csv', parse_dates = True, index_col = 0)


## some light preprocessing to make the fire severity masks ##
categories = ["Regrowth", "Unburned", "Low", "Moderate", "High"]
colors = ["lightgreen", "darkgreen", "yellow", "orange", "red"]
# Define the burn severity categories and their cutoff values
bounds = [-5000, -100, 70, 315, 640, 5000]

# Create an empty dictionary to store masks for each category
category_masks = {}
mtbs_rdnbr_50 = mtbs_rdnbr.rio.reproject_match(ds_50m)

# Create masks for each category
for i in range(len(bounds) - 1):
    lower_bound = bounds[i]
    upper_bound = bounds[i + 1]
    category_label = categories[i]

    # Create a mask for the current category
    mask = (mtbs_rdnbr_50 >= lower_bound) & (mtbs_rdnbr_50 < upper_bound)

    # Add the mask to the dictionary with the category label as the key
    category_masks[category_label] = mask
