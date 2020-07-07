# Introduction
The repo aims to build a geographic information system (GIS) library for Python interface. The library includes the following modules.

# Instlall
## Windows
1. Install preinstall thinktron pypi server
```
pip install -U --index-url http://rd.thinktronltd.com:28181/simple --trusted-host rd.thinktronltd.com GDAL==3.0.4 Fiona==1.8.13 Shapely==1.6.4.post2 geopandas==0.7.0 Rtree==0.9.4
```

2. Install TronGisPy from thinktron pypi server (Windows)
```
pip install -U --extra-index-url http://rd.thinktronltd.com:28181/simple --trusted-host rd.thinktronltd.com TronGisPy
```

## Linux
1. Build GDAL==3.0.4 by yourself
2. install preinstall from public pypi server
```
pip install GDAL==3.0.4 Fiona==1.8.13 Shapely==1.6.4.post2 geopandas==0.7.0 Rtree==0.9.4
```

3. Install TronGisPy from thinktron pypi server (Windows)
```
pip install -U --extra-index-url http://rd.thinktronltd.com:28181/simple --trusted-host rd.thinktronltd.com TronGisPy
```

## TronGisPy Main Modules
1. Raster: This module is Main class in this library. A Raster object contains all required information for a gis raster file such as `.tif` file including digital number for each pixel, number of rows, number of cols, number of bands, geo_transform, projection, no_data_value and metadata. 

2. CRS: Converion the indexing system e.g. coordinate & numpy index and wkt & epsg. 

3. TypeCast: Mapping the nearest data type betyween gdal and numpy, and convert the gdal data type from integer to readable string. 

4. ShapeGrid: Interaction between raster and vector data. 

5. Normalizer: Normalize the Image data for model training or plotting.

6. AeroTriangulation: Do the aero-triangulation calculation.

7. Interpolation: Interpolation for raster data on specific cells which are usually nan cells.

8. SplittedImage: Split remote sensing images for machine learning model training.

9. DEMProcessor: General dem processing functions e.g. shadow, slope, TRI, TPI and roughness.

10. GisIO: Some file-based gis functions.

# Quick Start
```python
import TronGisPy as tgp
raster = tgp.read_raster(tgp.get_testing_fp('satellite_tif'))
print("raster.data.shape:", raster.data.shape)
print("raster.geo_transform:", raster.geo_transform)
print("raster.projection:", raster.projection)
print("raster.no_data_value:", raster.no_data_value)
raster.plot()
```

<!-- ## Linux
1. install gdal 2.3.1 on the linux system (recommend get from the [url](http://download.osgeo.org/gdal/2.3.1/gdal-2.3.1.tar.gz))
    ```
    cd ~/Downloads
    wget http://download.osgeo.org/gdal/2.3.1/gdal-2.3.1.tar.gz
    tar xzf gdal-2.3.1.tar.gz
    mv ./gdal-2.3.1 ~/gdal-2.3.1
    cd ~/gdal-2.3.1
    ./configure
    make
    sudo make install
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH
    echo "export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH" >> ~/.profile
    ```

2. install gdal python sdk
    ```
    apt-get install -y python3.6-dev
    pip3 install numpy
    pip3 install GDAL==2.3.1 # must specify the version
    ```

3. install shapely & fiona & Rtree & geopandas
    ```
    pip install shapely fiona Rtree geopandas
    ``` -->



<!-- # Usage
Please see [Tutorial.ipynb](http://rd.thinktronltd.com/jeremywang/TronGisPyTutorial/blob/master/Tutorial.ipynb) & [the Tutorial repo](http://rd.thinktronltd.com/jeremywang/TronGisPyTutorial/) -->

# Build (For Developer)
```bash
python setup.py sdist bdist_wheel
```


