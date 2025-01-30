import xarray as xr
import numpy as np
from scipy.signal import savgol_filter
import rasterio
import os

def smooth_data(data, window_length, polyorder):
    return savgol_filter(data, window_length=window_length, polyorder=polyorder)


def get_elev(ds, srtm, band_size = 200, STATIC = False):
    # Extract elevation values from 'srtm_50' dataset
    elevation_values = srtm.values
    elevation_values_ft = elevation_values * 3.28084
    # Extract values from 'ds_50m' dataset
    ds_values = ds.values # may need to change this depending on dataset vs data array

    # Calculate the elevation bands
    elevation_bands = np.arange(1500, np.nanmax(elevation_values_ft), band_size)
    if STATIC:
        elevation_bands = np.arange(1500, 9000, band_size)

    # Initialize lists to store the means and percentiles
    band_means = []
    percentiles_25 = []
    percentiles_75 = []
    stds = []

    # Loop through elevation bands and calculate statistics for each band
    for band in elevation_bands:
        mask = (elevation_values_ft >= band) & (elevation_values_ft < band + band_size)
        values_in_band = ds_values[mask]
        if len(values_in_band) > 0:
            band_means.append(np.nanmedian(values_in_band))
            percentiles_25.append(np.nanpercentile(values_in_band, 25))
            percentiles_75.append(np.nanpercentile(values_in_band, 75))
            stds.append(np.nanstd(values_in_band))
        else:
            band_means.append(0)
            percentiles_25.append(0)
            percentiles_75.append(0)
            stds.append(0)

    return elevation_bands, band_means, percentiles_25, percentiles_75, stds



def make_modis_ds(directory):
    tiff_files = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith('.tif')]

    tiff_files.sort()
    data_arrays = []
    years = []
    for tiff_file in tiff_files:
        with rasterio.open(tiff_file) as src:
            # Read the data and metadata
            data = src.read(1)  # Assuming the data is in the first band
            transform = src.transform
            crs = src.crs
            data_arrays.append(xr.DataArray(data, dims=('y', 'x'), coords={'y': range(src.height), 'x': range(src.width)}))
            years.append(int(tiff_file.split('_')[-1].split('.')[0]))

    # Concatenate the DataArrays along the time dimension
    combined_data = xr.concat(data_arrays, dim='time')

    # Assign coordinates for the time dimension
    combined_data['time'] = range(len(tiff_files))

    # Assign CRS and transform
    combined_data.attrs['crs'] = crs
    combined_data.attrs['transform'] = transform

    data = xr.open_dataset(tiff_files[0])
    combined_data['x'] = data['x']
    combined_data['y'] = data['y']
    combined_data['time'] = years
    return combined_data
