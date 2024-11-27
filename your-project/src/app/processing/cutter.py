# https://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
# https://gis.stackexchange.com/questions/57710/determining-coordinates-of-corners-of-raster-layer-using-pyqgis/57711#57711
import abc
import io
import json
import os

from osgeo import gdal, ogr, osr

import numpy as np
from pyproj import Transformer

from app.processing.exceptions import ImageNotFound
from app.processing.models import Bbox


class Crop:
    def __init__(self, ds_path):
        self.ds_path = ds_path

    def open(self):
        if os.path.exists(self.ds_path):
            ds = gdal.Open(self.ds_path)
            return ds
        raise ImageNotFound(f"Cannot open: {self.ds_path}")


    @abc.abstractmethod
    def crop(self, geom):
        pass

    @staticmethod
    def round_to_nearest_10(num):
        return round(num/10)*10


class CropJson(Crop):

    no_data = 0

    def crop(self, geom):
        geojson_str = json.dumps(geom)
        driver = ogr.GetDriverByName('GeoJSON')
        datasource = driver.CreateDataSource('/vsimem/my.json')
        datasource.CreateLayer('layer')

        ogr_ds = ogr.Open(f'GeoJSON:{geojson_str}')
        layer = ogr_ds.GetLayer()

        ds = self.open()
        # Get raster properties
        geotransform = ds.GetGeoTransform()
        projection = ds.GetProjection()
        cols = ds.RasterXSize
        rows = ds.RasterYSize

        # Reproject GeoJSON to raster CRS if necessary
        source_srs = layer.GetSpatialRef()
        target_srs = osr.SpatialReference(wkt=projection)
        if not source_srs.IsSame(target_srs):
            coord_transform = osr.CoordinateTransformation(source_srs, target_srs)
            for feature in layer:
                geom = feature.GetGeometryRef()
                geom.Transform(coord_transform)
        else:
            geom = layer.GetNextFeature().GetGeometryRef()

        # Create a mask raster with the same dimensions as the input raster
        driver = gdal.GetDriverByName('MEM')
        mask_ds = driver.Create('', cols, rows, 1, gdal.GDT_Byte)
        mask_ds.SetGeoTransform(geotransform)
        mask_ds.SetProjection(projection)

        # Rasterize the geometry onto the mask
        gdal.RasterizeLayer(mask_ds, [1], layer, burn_values=[1])
        mask_band = mask_ds.GetRasterBand(1)
        mask = mask_band.ReadAsArray()

        # Apply the mask to the raster data
        data = ds.ReadAsArray()
        masked_data = np.where(mask == 1, data, np.nan)

        # Save the cropped raster
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create('/vsimem/my.tif', cols, rows, ds.RasterCount)
        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)

        for i in range(ds.RasterCount):
            out_band = out_ds.GetRasterBand(i + 1)
            out_band.Fill(self.no_data)
            out_band.WriteArray(masked_data[i] if ds.RasterCount > 1 else masked_data)
            out_band.SetNoDataValue(self.no_data)

        out_ds.FlushCache()

        tiff_driver = gdal.GetDriverByName('GTiff')  # GeoTIFF driver
        tiff_dataset = tiff_driver.CreateCopy('/vsimem/temp.tif', out_ds)  # Save in virtual filesystem
        tiff_dataset.FlushCache()
        # Calculate col row for geojson
        extent = layer.GetExtent()  # (min_x, max_x, min_y, max_y)
        layer.GetSpatialRef()
        min_x, max_x, min_y, max_y = extent

        proj = osr.SpatialReference(wkt=tiff_dataset.GetProjection())
        xmin, xres, _, ymax, _, yres = tiff_dataset.GetGeoTransform()

        transformer = Transformer.from_crs("EPSG:4326", proj.ExportToProj4(), always_xy=True)
        bbox_t = transformer.transform(
            [min_x, max_x],  # x-coordinates
            [min_y, max_y]  # y-coordinates
        )
        xmin_t, xmax_t = bbox_t[0]
        ymin_t, ymax_t = bbox_t[1]

        # Calculate pixel indices for the transformed bbox
        xoff = int((xmin_t - xmin) / xres)  # Column start
        yoff = int((ymax - ymax_t) / abs(yres))  # Row start
        xsize = int((xmax_t - xmin_t) / xres)  # Number of columns
        ysize = int((ymax_t - ymin_t) / abs(yres))  # Number of rows

        subset = tiff_dataset.ReadAsArray(xoff, yoff, xsize, ysize)
        bbox_driver = gdal.GetDriverByName('GTiff')
        bbox_ds = bbox_driver.Create('/vsimem/bbox.tif', xsize, ysize, tiff_dataset.RasterCount, gdal.GDT_Byte)
        new_geotransform = (
            self.round_to_nearest_10(xmin_t),  # xmin of cropped area
            xres,  # pixel width
            0,  # rotation (usually 0)
            self.round_to_nearest_10(ymax_t),  # ymax of cropped area
            0,  # rotation (usually 0)
            yres  # pixel height (negative)
        )
        bbox_ds.SetGeoTransform(new_geotransform)
        bbox_ds.SetProjection(tiff_dataset.GetProjection())

        # Write data band by band
        for i in range(1, tiff_dataset.RasterCount + 1):
            bbox_band = bbox_ds.GetRasterBand(i)
            bbox_band.Fill(self.no_data)
            bbox_band.WriteArray(subset[i - 1])
            bbox_band.SetNoDataValue(self.no_data)

        bbox_ds.FlushCache()



        buffer = io.BytesIO()
        vsi_file = gdal.VSIFOpenL('/vsimem/bbox.tif', 'rb')
        vsi_file_size = gdal.VSIStatL('/vsimem/bbox.tif').size

        buffer.write(gdal.VSIFReadL(1, vsi_file_size, vsi_file))
        buffer.seek(0)  # Reset the pointer in the buffer for reading

        gdal.Unlink('/vsimem/temp.tif')
        gdal.Unlink('/vsimem/my.tif')
        gdal.Unlink('/vsimem/bbox.tif')

        # Close datasets
        tiff_dataset = None
        ds = None
        geojson_ds = None
        mask_ds = None
        out_ds = None
        bbox_ds = None

        return buffer


class CropBBox(Crop):
    def crop(self, geom: Bbox):
        ds =self.open()
        proj = osr.SpatialReference(wkt=ds.GetProjection())
        geotransform = ds.GetGeoTransform()
        xmin, xres, _, ymax, _, yres = geotransform
        transformer = Transformer.from_crs("EPSG:4326", proj.ExportToProj4(), always_xy=True)
        bbox_t = transformer.transform(
            [geom.min_x, geom.max_x],  # x-coordinates
            [geom.min_y, geom.max_y]  # y-coordinates
        )
        xmin_t, xmax_t = bbox_t[0]
        ymin_t, ymax_t = bbox_t[1]

        # Calculate pixel indices for the transformed bbox
        xoff = int((xmin_t - xmin) / xres)  # Column start
        yoff = int((ymax - ymax_t) / abs(yres))  # Row start
        xsize = int((xmax_t - xmin_t) / xres)  # Number of columns
        ysize = int((ymax_t - ymin_t) / abs(yres))  # Number of rows

        subset = ds.ReadAsArray(xoff, yoff, xsize, ysize)

        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create('/vsimem/my.tif', xsize, ysize, ds.RasterCount, gdal.GDT_Byte)

        # Update geotransform for the new dataset
        new_geotransform = (
            self.round_to_nearest_10(xmin_t),  # xmin of cropped area
            xres,  # pixel width
            0,  # rotation (usually 0)
            self.round_to_nearest_10(ymax_t),  # ymax of cropped area
            0,  # rotation (usually 0)
            yres  # pixel height (negative)
        )
        out_ds.SetGeoTransform(new_geotransform)
        out_ds.SetProjection(ds.GetProjection())

        # Write data band by band
        for i in range(1, ds.RasterCount + 1):
            out_ds.GetRasterBand(i).WriteArray(subset[i - 1])

        out_ds.FlushCache()

        tiff_driver = gdal.GetDriverByName('GTiff')  # GeoTIFF driver
        tiff_dataset = tiff_driver.CreateCopy('/vsimem/temp.tif', out_ds)
        tiff_dataset.FlushCache()
        vsi_file = gdal.VSIFOpenL('/vsimem/temp.tif', 'rb')
        vsi_file_size = gdal.VSIStatL('/vsimem/temp.tif').size
        buffer = io.BytesIO()
        buffer.write(gdal.VSIFReadL(1, vsi_file_size, vsi_file))
        buffer.seek(0)  # Reset the pointer in the buffer for reading

        gdal.Unlink('/vsimem/temp.tif')
        gdal.Unlink('/vsimem/my.tif')

        ds = None
        out_ds = None
        tiff_dataset = None

        return buffer
