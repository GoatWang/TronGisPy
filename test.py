import unittest

# basic
import os
import shutil
import numpy as np
from collections import Counter

# data
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

# gis
from shapely.geometry import Polygon
import gdal

# main
from PySatellite.SplittedImage import SplittedImage
from PySatellite.SatelliteIO import get_geo_info, get_nparray, get_extend, write_output_tif, clip_image_by_shp, tif_composition
from PySatellite.Algorithm import kmeans
data_dir = os.path.join('PySatellite', 'data')
satellite_tif_dir = data_dir
satellite_tif_path = os.path.join(satellite_tif_dir, 'P0015913_SP5_006_001_002_021_002_005.tif')
satellite_tif_clipper_path = os.path.join(satellite_tif_dir, 'P0015913_SP5_006_001_002_021_002_005_clipper.shp')
satellite_tif_kmeans_path = os.path.join(satellite_tif_dir, 'P0015913_SP5_006_001_002_021_002_005_kmeans.tif')

show_image = False


class TestSplittedImage(unittest.TestCase):
    def setUp(self):
        self.output_dir = os.path.join('test_output')
        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

        # window_size_h = window_size_w = step_size_h = step_size_w = 256
        self.box_size = 128
        
        cols, rows, bands, geo_transform, projection, dtype_gdal, no_data_value = get_geo_info(satellite_tif_path)
        self.geo_transform = geo_transform
        self.projection = projection
        self.dtype_gdal = dtype_gdal
        self.X = get_nparray(satellite_tif_path)

        self.splitted_image = SplittedImage(self.X, self.box_size, self.geo_transform, self.projection)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test___getitem__(self):
        slice_test1 = Counter(pd.cut(self.splitted_image[1].flatten(), bins=3, labels=range(3))) == Counter({1: 137343, 0: 122742, 2: 2059})
        slice_test2 = Counter(pd.cut(self.splitted_image[:2].flatten(), bins=3, labels=range(3))) == Counter({1: 412579, 0: 366496, 2: 7357})
        slice_test3 = Counter(pd.cut(self.splitted_image[:2, 2].flatten(), bins=3, labels=range(3))) == Counter({0: 97945, 1: 95721, 2: 2942})
        slice_test4 = Counter(pd.cut(self.splitted_image[:2, :2].flatten(), bins=3, labels=range(3))) == Counter({1: 333569, 0: 250291, 2: 5964})

        self.assertTrue(slice_test1)
        self.assertTrue(slice_test2)
        self.assertTrue(slice_test3)
        self.assertTrue(slice_test4)

    def test_get_padded_image(self):
        shape_test = self.splitted_image.padded_image.shape == (512, 512, 4)
        self.assertTrue(shape_test)

    def test_get_splitted_images(self):
        shape_test = self.splitted_image.get_splitted_images().shape == (16, 128, 128, 4)
        self.assertTrue(shape_test)

    def test_get_geo_attribute(self):
        df_attribute = self.splitted_image.get_geo_attribute()
        pol = df_attribute.loc[0, 'geometry']
        area_test = pol.area == 1638400.0
        self.assertTrue(area_test)

    def test_write_splitted_images(self):
        self.splitted_image.write_splitted_images(self.output_dir, 'P0015913_SP5_006_001_002_021_002_005')

    def test_write_combined_tif(self):
        box_size = 101
        splitted_image = SplittedImage(self.X, box_size, self.geo_transform, self.projection)
        X_pred = splitted_image.get_splitted_images()
        dst_tif_path = os.path.join(self.output_dir, "combined.tif")
        splitted_image.write_combined_tif(X_pred, dst_tif_path, self.dtype_gdal)

class TestSatelliteIO(unittest.TestCase):
    def setUp(self):
        self.output_dir = os.path.join('test_output')
        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_clip_image_by_shp(self):
        dst_image_path = os.path.join(self.output_dir, 'clipped_image.tif')
        clip_image_by_shp(satellite_tif_path, satellite_tif_clipper_path, dst_image_path)
        clip_image_arr = get_nparray(dst_image_path)
        if show_image:
            plt.imshow(clip_image_arr)
            plt.title("TestSatelliteIO" + ": " + "test_clip_image_by_shp")
            plt.show()
        self.assertTrue(clip_image_arr.shape == (138, 225, 4))

    def test_tif_composition(self):
        crs_tif_image = satellite_tif_path
        src_tif_paths = [satellite_tif_path, satellite_tif_kmeans_path]
        dst_image_path = os.path.join(self.output_dir, 'composited_image.tif')
        tif_composition(crs_tif_image, src_tif_paths, dst_image_path)

        composited_image_arr = get_nparray(dst_image_path)
        if show_image:
            plt.imshow(composited_image_arr[:, :, 4], cmap='gray')
            plt.title("TestSatelliteIO" + ": " + "test_clip_image_by_shp")
            plt.show()

        self.assertTrue(composited_image_arr.shape == (512, 512, 5))

class TestAlgorithm(unittest.TestCase):
    def setUp(self):
        self.output_dir = os.path.join('test_output')
        if not os.path.isdir(self.output_dir):
            os.mkdir(self.output_dir)

        # window_size_h = window_size_w = step_size_h = step_size_w = 256
        self.box_size = 128
        self.cols, self.rows, self.bands, self.geo_transform, self.projection, self.dtype_gdal, self.no_data_value = get_geo_info(satellite_tif_path)
        self.X = get_nparray(satellite_tif_path)

    # def tearDown(self):
    #     shutil.rmtree(self.output_dir)

    def test_kmeans(self):
        X_kmeans = kmeans(self.X, n_clusters=5, no_data_value=0)
        dst_tif_path = os.path.join(self.output_dir, "X_kmeans.tif")
        bands = 1
        write_output_tif(X_kmeans.reshape(*X_kmeans.shape, -1), dst_tif_path, bands, self.cols, self.rows, self.geo_transform, self.projection)

        kmeans_image_arr = get_nparray(dst_tif_path)
        if show_image:
            plt.imshow(kmeans_image_arr[:, :, 0], cmap='gray')
            plt.title("TestAlgorithm" + ": " + "test_kmeans")
            plt.show()
        self.assertTrue(Counter(list(np.hstack(kmeans_image_arr[:, :, 0])))[4] == 9511)

if __name__ == "__main__":
    unittest.main()
#  python -m unittest -v test.py