# DuckDB Raster Extension Function Reference

## Function Index
**[Table Functions](#table-functions)**

| Function | Summary |
| --- | --- |
| [`RT_Drivers`](#rt_drivers) | Returns the list of supported GDAL RASTER drivers and file formats. |
| [`RT_Read`](#rt_read) | Reads a raster file and returns a table with the raster data. |

**[Scalar Functions](#scalar-functions)**

| Function | Summary |
| --- | --- |
| [`RT_Blob2Array`](#rt_blob2array) | Transforms the BLOB data of the data band columns into an array of a numeric data type. |

----

## Table Functions

### RT_Drivers

#### Signature

```sql
RT_Drivers ()
```

#### Description

Returns the list of supported GDAL RASTER drivers and file formats.

Note that far from all of these drivers have been tested properly.
Some may require additional options to be passed to work as expected.
If you run into any issues please first consult the [consult the GDAL docs](https://gdal.org/drivers/raster/index.html).

#### Example

```sql
SELECT * FROM RT_Drivers();
```

----

### RT_Read

#### Signature

```sql
RT_Read (file_path VARCHAR,
         open_options VARCHAR[] DEFAULT NULL,
         allowed_drivers VARCHAR[] DEFAULT NULL,
         sibling_files VARCHAR[] DEFAULT NULL,
         compression VARCHAR DEFAULT 'NONE',
         blocksize_x INTEGER DEFAULT NULL,
         blocksize_y INTEGER DEFAULT NULL,
         datacube BOOLEAN DEFAULT false
         )
```

#### Description

The `RT_Read` table function is based on the [GDAL](https://gdal.org/index.html) translator library and enables reading raster data from a variety of geospatial raster file formats as if they were DuckDB tables.

> See [RT_Drivers](#rt_drivers) for a list of supported file formats and drivers.

The table returned by `RT_Read` is a tiled representation of the raster file, where each row corresponds to a tile of the raster. The tile size is determined by the original block size of the raster file, but it can be overridden by the user using the `blocksize_x` and `blocksize_y` parameters. `geometry` column is a `GEOMETRY` type of type `POLYGON` that represents the footprint of each tile and you can use it to create a new geoparquet file adding the option `GEOPARQUET_VERSION`.

The `RT_Read` function accepts parameters, most of them optional:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `path` | VARCHAR | The path to the file to read. The unique mandatory parameter. |
| `open_options` | VARCHAR[] | A list of key-value pairs that are passed to the GDAL driver to control the opening of the file. Read GDAL documentation for available options. |
| `allowed_drivers` | VARCHAR[] | A list of GDAL driver names that are allowed to be used to open the file. If empty, all drivers are allowed. |
| `sibling_files` | VARCHAR[] | A list of sibling files that are required to open the file. |
| `compression` | VARCHAR | The compression method to use when packing the databand column. `NONE` is the unique option now. |
| `blocksize_x` | INTEGER | The block size of the tile in the x direction. You can use this parameter to override the original block size of the raster. |
| `blocksize_y` | INTEGER | The block size of the tile in the y direction. You can use this parameter to override the original block size of the raster. |
| `datacube` | BOOLEAN | `true` means that extension returns one unique N-dimensional databand column with all bands interleaved, otherwise each band is returned as a separate column. `false` is the default. |

This is the list of columns returned by `RT_Read`:

+ `id` is a unique identifier for each tile of the raster.
+ `x` and `y` are the coordinates of the center of each tile. The coordinate reference system is the same as the one of the raster file.
+ `bbox` is the bounding box of each tile, which is a struct with `xmin`, `ymin`, `xmax`, and `ymax` fields.
+ `geometry` is the footprint of each tile as a polygon.
+ `level`, `tile_x`, and `tile_y` are the tile coordinates of each tile. The raster is read in tiles of size `blocksize_x` x `blocksize_y` (or the original block size of the raster if not overridden by the parameters). Each row of the output table corresponds to a tile of the raster, and the `databand_x` columns contain the data of that tile for each band.
+ `cols` and `rows` are the number of columns and rows of each tile, which can be different from the original raster if the `blocksize_x` and `blocksize_y` parameters are used to override the block size.
+ `metadata` is a JSON column that contains the metadata of the raster file, including the list of bands and their properties (data type, no data value, etc), the spatial reference system, the geotransform, and any other metadata provided by the GDAL driver.
+ `databand_x` are BLOB columns that contain the data of the raster bands and a header metadata describing the schema of the data. If the `datacube` option is set to `true`, only a single column called `datacube` will contain all bands interleaved in a single N-dimensional array.

The data band columns are a BLOB with the following internal structure:

+ A Header describes the raster tile data stored in the BLOB.
	+ `magic` (uint16_t): Magic code to identify a BLOB as a raster block (`0x5253`)
	+ `compression` (uint8_t): Compression algorithm code used for the tile data. `0=NONE` is the unique option now, but more can be added in the future.
	+ `data_type` (uint8_t): RasterDataType of the tile data:

		| Code | Data Type | Description |
		|------|-----------|-------------|
		| 0    | UNKNOWN | Unknown or unspecified type |
		| 1    | UINT8 | Eight bit unsigned integer |
		| 2    | INT8 | 8-bit signed integer |
		| 3    | UINT16 | Sixteen bit unsigned integer |
		| 4    | INT16 | Sixteen bit signed integer |
		| 5    | UINT32 | Thirty two bit unsigned integer |
		| 6    | INT32 | Thirty two bit signed integer |
		| 7    | UINT64 | 64 bit unsigned integer |
		| 8    | INT64 | 64 bit signed integer |
		| 9    | FLOAT | Thirty two bit floating point |
		| 10   | DOUBLE | Sixty four bit floating point |

	+ `bands` (int32_t): Number of bands or layers in the data buffer
	+ `cols` (int32_t): Number of columns in the data buffer
	+ `rows` (int32_t): Number of rows in the data buffer
	+ `no_data` (double): NoData value for the tile (To consider when applying algebra operations). `-infinity` if not defined.

+ `data`[] (uint8_t): Interleaved pixel data for all bands, stored in row-major order. The size of this array depends on the data type, number of bands, and tile dimensions.

By using `RT_Read`, the extension also provides “replacement scans” for common raster file formats, allowing you to query files of these formats as if they were tables directly.

----

## Scalar Functions

### RT_Blob2Array

#### Signature

```sql
RT_Blob2ArrayUInt8  (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayInt8   (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayUInt16 (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayInt16  (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayUInt32 (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayInt32  (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayUInt64 (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayInt64  (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayFloat  (blob BLOB, filter_nodata BOOLEAN)
RT_Blob2ArrayDouble (blob BLOB, filter_nodata BOOLEAN)
```

#### Description

Transforms the BLOB data of the data band columns into an array of a numeric data type.

```sql
SELECT
	RT_Blob2ArrayInt32(databand_1, true) AS r,
	RT_Blob2ArrayInt32(databand_2, true) AS g,
	RT_Blob2ArrayInt32(databand_3, true) AS b
FROM
	RT_Read('path/to/raster/file.tif')
;
```

Function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `blob` | BLOB | The BLOB column of the data band to transform. |
| `filter_nodata` | BOOLEAN | Whether to filter out NoData values from the array. If `true`, the function will exclude NoData values from the resulting array. |

Extension provides a different function for each numeric data type:

| Function | Description |
| -------- | ----------- |
| `RT_Blob2ArrayUInt8` | Transforms a BLOB data column into an array of UINT8 values |
| `RT_Blob2ArrayInt8` | Transforms a BLOB data column into an array of INT8 values |
| `RT_Blob2ArrayUInt16` | Transforms a BLOB data column into an array of UINT16 values |
| `RT_Blob2ArrayInt16` | Transforms a BLOB data column into an array of INT16 values |
| `RT_Blob2ArrayUInt32` | Transforms a BLOB data column into an array of UINT32 values |
| `RT_Blob2ArrayInt32` | Transforms a BLOB data column into an array of INT32 values |
| `RT_Blob2ArrayUInt64` | Transforms a BLOB data column into an array of UINT64 values |
| `RT_Blob2ArrayInt64` | Transforms a BLOB data column into an array of INT64 values |
| `RT_Blob2ArrayFloat` | Transforms a BLOB data column into an array of FLOAT values |
| `RT_Blob2ArrayDouble` | Transforms a BLOB data column into an array of DOUBLE values |

Functions return a struct with the following fields:

+ `data_type` (INT): RasterDataType code of the data in the BLOB.
+ `bands` (INT): Number of bands or layers in the data buffer.
+ `cols` (INT): Number of columns in the tile.
+ `rows` (INT): Number of rows in the tile.
+ `no_data` (DOUBLE): NoData value for the tile (To consider when applying algebra operations). `-infinity` if not defined.
+ `values` (ARRAY): An array with the pixel values of the tile for the corresponding band and data type.

This allows you to do algebra operations with the data of the tiles directly in SQL:

```sql
WITH __input AS (
	SELECT
		RT_Blob2ArrayInt32(databand_1, false) AS r
	FROM
		RT_Read('path/to/raster/file.tif', blocksize_x := 512, blocksize_y := 512)
)
SELECT
	list_min(r.values) AS r_min,
	list_stddev_pop(r.values) AS r_avg,
	list_max(r.values) AS r_max
FROM
	__input
;
```

----
