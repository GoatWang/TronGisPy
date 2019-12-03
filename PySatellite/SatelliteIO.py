import os
import numpy as np
import ogr, osr
import gdal
import geopandas as gpd
from PySatellite.CRS import transfer_npidx_to_coord_polygon

# bands compositions
def get_geo_info(fp):
    """cols, rows, bands, geo_transform, projection, dtype_gdal, no_data_value = get_geo_info(fp)"""
    ds = gdal.Open(fp)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bands = ds.RasterCount 
    geo_transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    dtype_gdal = ds.GetRasterBand(1).DataType
    no_data_value = ds.GetRasterBand(1).GetNoDataValue()
    ds = None 
    return cols, rows, bands, geo_transform, projection, dtype_gdal, no_data_value

def get_nparray(fp, opencv_shape=True):
    """if opencv_shape the shape will be (cols, rows, bnads), else (bnads, cols, rows)"""
    ds = gdal.Open(fp)
    X = ds.ReadAsArray()
    ds = None 
    if not opencv_shape:
        return X
    else:
        if len(X.shape) == 2:
            X = X.reshape(-1, *X.shape)
        return np.transpose(X, axes=[1,2,0])

def get_extend(fp):
    """get the extend(boundry) coordnate"""
    ds = gdal.Open(fp)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    gt = ds.GetGeoTransform()
    extend=[]
    xarr=[0,cols]
    yarr=[0,rows]
    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            extend.append([x,y])
        yarr.reverse()
    return extend


def write_output_tif(X, dst_tif_path, bands, cols, rows, geo_transform, projection, data_type=gdal.GDT_Int32, no_data_value=None):
    assert len(X.shape) == 3, "please reshape it to (n_rows, n_cols, n_bands)"
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst_tif_path, cols, rows, bands, data_type) # dst_filename, xsize=512, ysize=512, bands=1, eType=gdal.GDT_Byte
    dst_ds.SetGeoTransform(geo_transform)
    dst_ds.SetProjection(projection)

    for b in range(bands):
        band = dst_ds.GetRasterBand(b+1)
        band.WriteArray(X[:, :, b], 0, 0)
        if no_data_value:
            band.SetNoDataValue(no_data_value)
        band.FlushCache()
        
    dst_ds = None

def clip_tif_by_shp(src_tif_path, src_shp_path, dst_tif_path):
    result = gdal.Warp(dst_tif_path,
                       src_tif_path,
                       cutlineDSName=src_shp_path,
                       cropToCutline=True)
    result = None

def tif_composition(ref_tif_path, src_tif_paths, dst_tif_path, dst_tif_dtype_gdal=None):
    """
    ref_tif_path: should be used to create the canvas with final coordinate system, geo_transform and projection, 
    src_tif_paths: should be in list type with elements with full path of tif images.
    dst_tif_path: output file path
    """
    # get geo info
    cols, rows, bands, geo_transform, projection, dtype_gdal, no_data_value = get_geo_info(ref_tif_path)
    if dst_tif_dtype_gdal:
        dtype_gdal = dst_tif_dtype_gdal
        
    # cal bands count
    bands_for_each_tif = [get_geo_info(tif_path)[2] for tif_path in src_tif_paths]
    bands = sum(bands_for_each_tif)

    # bands compositions: create new tif
    dst_ds = gdal.GetDriverByName('GTiff').Create(dst_tif_path, cols, rows, bands, dtype_gdal)
    dst_ds.SetGeoTransform(geo_transform)
    dst_ds.SetProjection(projection)
    
    # bands compositions: write bands
    band_num = 1
    for tif_path, bands_for_the_tif in zip(src_tif_paths, bands_for_each_tif):
        nparr = get_nparray(tif_path)
        for band_num_for_the_tif in range(bands_for_the_tif):
            band = dst_ds.GetRasterBand(band_num)
            band.WriteArray(nparr[:, :, band_num_for_the_tif], 0, 0)
            band.FlushCache()
            if no_data_value:
                band.SetNoDataValue(no_data_value)
            band_num += 1
    dst_ds = None

def refine_resolution(src_tif_path, dst_tif_path, dst_resolution):
    result = gdal.Warp(dst_tif_path, src_tif_path, xRes=dst_resolution, yRes=dst_resolution)
    result = None

def rasterize_layer(src_shp_path, dst_tif_path, ref_tif_path, use_attribute=None):
    """
    src_shp_path: rasterize which shp.
    dst_tif_path: rasterize output, should be in tiff type.
    ref_tif_path: the geo information reference raster.
    use_attribute: use thich attribute of the shp as raster value.
    """
    # Open your shapefile
    df_shp = gpd.read_file(src_shp_path)
    if not use_attribute:
        use_attribute = 'positive'
        df_shp['positive'] = 1
    else:
        assert use_attribute in df_shp.columns, "attribute not exists!"
    src_shp_ds = ogr.Open(df_shp.to_json())
    src_shp_layer = src_shp_ds.GetLayer()

    # Create the destination raster data source
    # pixelWidth = pixelHeight = 2 # depending how fine you want your raster
    # x_min, x_max, y_min, y_max = source_layer.GetExtent()
    # cols = int((x_max - x_min) / pixelHeight)
    # rows = int((y_max - y_min) / pixelWidth)
    # geoTransform = (x_min, pixelWidth, 0, y_min, 0, pixelHeight)
    ref_tif_ds = gdal.Open(ref_tif_path)
    ref_tif_cols, ref_tif_rows = ref_tif_ds.RasterXSize, ref_tif_ds.RasterYSize
    
    dst_tif_ds = gdal.GetDriverByName('GTiff').Create(dst_tif_path, ref_tif_cols, ref_tif_rows, 1, gdal.GDT_Byte) # dst_filename, xsize=512, ysize=512, bands=1, eType=gdal.GDT_Byte
    dst_tif_ds.SetGeoTransform(ref_tif_ds.GetGeoTransform())

    band = dst_tif_ds.GetRasterBand(1)
    band.SetNoDataValue(0)
    band.FlushCache()

    # set it to the attribute that contains the relevant unique
    gdal.RasterizeLayer(dst_tif_ds, [1], src_shp_layer, options = ["ATTRIBUTE="+use_attribute]) # target_ds, band_list, source_layer, options = options

    # Add a spatial reference
    dst_tif_ds.SetProjection(ref_tif_ds.GetProjection())
#     dst_tif_dsSRS = osr.SpatialReference()
#     dst_tif_dsSRS.ImportFromEPSG(3826)
#     dst_tif_ds.SetProjection(dst_tif_dsSRS.ExportToWkt())

    ref_tif_ds = None
    dst_ds = None


def polygonize_layer(src_tif_path, dst_shp_path, remove_boundry=True):
    src_ds = gdal.Open(src_tif_path)
    srcband = src_ds.GetRasterBand(1)
    src_srs=osr.SpatialReference(wkt=src_ds.GetProjection())

    if os.path.isfile(dst_shp_path):
        os.remove(dst_shp_path)
    drv = ogr.GetDriverByName("ESRI Shapefile")
    dst_ds = drv.CreateDataSource(dst_shp_path)
    layer_name = os.path.split(dst_shp_path)[-1].replace(".shp", "")
    dst_layer = dst_ds.CreateLayer(layer_name, srs=src_srs)
    dst_field = -1 #the attribute field index indicating the feature attribute into which the pixel value of the polygon should be written.

    gdal.Polygonize(srcband, None, dst_layer, dst_field, [], callback=None)

    src_ds = None
    dst_ds = None

    if remove_boundry:
        df_shp = gpd.read_file(dst_shp_path)
        df_shp.drop(np.argmax(df_shp['geometry'].apply(lambda x:x.area).values), inplace=True)
        df_shp.to_file(dst_shp_path)

def raster_pixel_to_polygon(src_tif_path, dst_shp_path, all_bands_as_feature=False, crs=None, return_gdf=False):
    """
    crs should be dict type {'init' :'epsg:<epsg_code>'}, e.g. {'init' :'epsg:4326>'}
    """
    cols, rows, bands, geo_transform, projection, dtype_gdal, no_data_value = get_geo_info(src_tif_path)
    X = get_nparray(src_tif_path)
    idxs = np.where(np.ones_like(X[:,:,0], dtype=np.bool))
    rows = []
    for row_idx, col_idx in zip(*idxs):
        row = {}
        npidx = (row_idx, col_idx)
        row['geometry'] = transfer_npidx_to_coord_polygon(npidx, geo_transform)
        if all_bands_as_feature:
            for i in range(X.shape[2]):
                row['band'+str(i+1)] = X[row_idx, col_idx, i]
        rows.append(row)
    df_shp = gpd.GeoDataFrame(rows, geometry='geometry')
    if crs:
        df_shp.crs = crs
    if return_gdf:
       return df_shp
    else:
        df_shp.to_file(dst_shp_path)


#==================================
def get_testing_fp():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    satellite_tif_path = os.path.join(base_dir, 'data', 'P0015913_SP5_006_001_002_021_002_005.tif')
    return os.path.abspath(satellite_tif_path)
