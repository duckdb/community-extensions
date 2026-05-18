# DuckDB Raster Extension Function Reference

## Function Index

**[Table Functions](#table-functions)**

| Function | Summary |
| --- | --- |
| [`RT_Drivers`](#rt_drivers) | Returns the list of supported GDAL RASTER drivers and file formats. |
| [`RT_Read`](#rt_read) | Reads a raster file (or a mosaic of raster files) and returns a table with the raster data. |
| [`RT_Write`](#rt_write) | (`COPY TO`) Exports the data table to a new raster file. |

**[Scalar Functions](#scalar-functions)**

| Function | Summary |
| --- | --- |
| [`RT_Cube2Array`](#rt_cube2array) | Transforms the data of the datacube columns into an array of a numeric data type. |
| [`RT_Cube2Type`](#rt_cube2type) | Transforms a datacube column to another data type. |
| [`RT_Array2Cube`](#rt_array2cube) | Transforms an array of numeric values into a datacube column. |
| [`RT_Cube<UnaryOp>`](#rt_cubeunaryop) | Applies an unary operation to the values in the datacube element-wise. |
| [`RT_Cube<BinaryOp>`](#rt_cubebinaryop) | Applies a binary operation to the values in the datacube element-wise. |
| [`RT_CubeStats`](#rt_cubestats) | Calculates statistics for a specific band of a datacube. |
| [`RT_GdalConfig`](#rt_gdalconfig) | Sets a GDAL configuration option (equivalent to CPLSetConfigOption). |

**[Spatial Functions](#spatial-functions)**

| Function | Summary |
| --- | --- |
| [`RT_Envelope`](#rt_envelope) | Computes the bounding box of the valid (non-no-data) cells in the input datacube and returns it as a geometry. |
| [`RT_Polygon`](#rt_polygon) | Creates a polygon geometry for each contiguous region of non-no-data values in the datacube. |
| [`RT_CubeClip`](#rt_cubeclip) | Returns a datacube where cells outside the given geometry are replaced by the specified value. |
| [`RT_CubeBurn`](#rt_cubeburn) | Returns a datacube where cells inside the given geometry are replaced by the specified value. |

----

## Table Functions

### RT_Drivers

Returns the list of supported GDAL RASTER drivers and file formats.

Note that not all of these drivers have been thoroughly tested.
Some may require additional options to be passed to work as expected.
If you run into any issues, please consult the [GDAL docs](https://gdal.org/drivers/raster/index.html).

#### Signature

```sql
RT_Drivers ()
```

#### Examples

```sql
SELECT * FROM RT_Drivers();
```

----

### RT_Read

Open a raster file (or a mosaic of raster files) and return a table with the raster data.

The function accepts a string or a list of strings as input. In case of a list of strings, the function creates a virtual raster (VRT) mosaic of the input files, which allows you to read multiple raster files as if they were one. This is especially useful when working with large rasters that are split into multiple files.

The `RT_Read` table function is based on the [GDAL](https://gdal.org/index.html) translator library and enables reading raster data from a variety of geospatial raster file formats as if they were DuckDB tables.

> See [RT_Drivers](#rt_drivers) for a list of supported file formats and drivers.

The table returned by `RT_Read` is a tiled representation of the raster file[s], where each row corresponds to a tile of the raster. The tile size is determined by the original block size of the raster file[s], but it can be overridden by the user using the `blocksize_x` and `blocksize_y` parameters. The `geometry` column is a `GEOMETRY` of type `POLYGON` that represents the footprint of each tile, and you can use it to create a new geoparquet file by adding the option `GEOPARQUET_VERSION`.

Both `databand` and `datacube` columns share the same underlying type: a BLOB encoding an N-dimensional array of pixel values. The terms are interchangeable in the context of this extension — they only differ in how `RT_Read` names the output columns. By default, `RT_Read` produces one column per raster band, named `databand_1`, `databand_2`, etc. When the `datacube` option is `true`, all bands are merged into a single column named `datacube`. In either case the BLOB layout is identical.

The `RT_Read` function accepts parameters, most of them optional:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `path` | VARCHAR | The path to the file to read. The only mandatory parameter. |
| `open_options` | VARCHAR[] | A list of key-value pairs that are passed to the GDAL driver to control the opening of the file. Refer to the GDAL documentation for available options. Only for single-file version of the function. |
| `allowed_drivers` | VARCHAR[] | A list of GDAL driver names that are allowed to be used to open the file. If empty, all drivers are allowed. Only for single-file version of the function. |
| `sibling_files` | VARCHAR[] | A list of sibling files that are required to open the file. Only for single-file version of the function. |
| `separate_bands` | BOOLEAN | `true` means that each input goes into a separate band in the VRT dataset. Otherwise, the files are considered as source rasters of a larger mosaic and the VRT file has the same number of bands as the input files. Only for multi-file version of the function. `false` is the default. |
| `data_format` | VARCHAR | Compression format used when packing the pixel data into the BLOB. See the data format table in the BLOB structure section below. `RAW` (uncompressed) is the default. |
| `blocksize_x` | INTEGER | The block size of the tile in the x direction. You can use this parameter to override the original block size of the raster. |
| `blocksize_y` | INTEGER | The block size of the tile in the y direction. You can use this parameter to override the original block size of the raster. |
| `skip_empty_tiles` | BOOLEAN | When `true`, tiles that contain no data are omitted from the output (checks the `GDAL_DATA_COVERAGE_STATUS_DATA` flag when supported). `true` is the default. |
| `datacube` | BOOLEAN | When `true`, all bands are merged into a single `datacube` column; otherwise each band is returned as a separate `databand_N` column. `false` is the default. |

This is the list of columns returned by `RT_Read`:

+ `id` is a unique identifier for each tile of the raster.
+ `x` and `y` are the coordinates of the center of each tile. The coordinate reference system is the same as the one of the raster file.
+ `bbox` is the bounding box of each tile, which is a struct with `xmin`, `ymin`, `xmax`, and `ymax` fields.
+ `geometry` is the footprint of each tile as a polygon.
+ `level`, `tile_x`, and `tile_y` are the tile grid coordinates. The raster is partitioned into tiles of `blocksize_x` × `blocksize_y` pixels (or the file's native block size when not overridden).
+ `cols` and `rows` are the actual pixel dimensions of the tile, which may differ from the requested block size at the edges of the raster.
+ `metadata` is a JSON column with the raster file metadata: band properties (data type, nodata value, etc.), spatial reference system, geotransform, and any driver-specific metadata.
+ `databand_1`, `databand_2`, … are BLOB columns, each holding the pixel data for one raster band together with a small binary header that describes the tile layout. When the `datacube` option is `true`, a single `datacube` column is returned instead, containing all bands in the same BLOB format.

The data band columns are a BLOB with the following internal structure:

+ A Header describes the raster tile data stored in the BLOB.
	+ `magic` (uint16_t): Magic code to identify a BLOB as a raster block (`0x5253`)
	+ `data_format` (uint8_t): Data format code used for packing tile data:

		| Code | Key | Description |
		|------|-----------|-------------|
		| 0    | RAW | Uncompressed raw data, interleaved by pixel and band |
		| 1    | SNAPPY | Snappy compressed data |
		| 2    | GZIP | GZIP compressed data |
		| 3    | ZSTD | Zstandard compressed data |
		| 4    | LZ4 | LZ4 compressed data |

	+ `data_type` (uint8_t): Data type of the values of the tile data:

		| Code | Key | Description |
		|------|-----------|-------------|
		| 0    | UINT8 | Eight bit unsigned integer |
		| 1    | INT8 | 8-bit signed integer |
		| 2    | UINT16 | Sixteen bit unsigned integer |
		| 3    | INT16 | Sixteen bit signed integer |
		| 4    | UINT32 | Thirty two bit unsigned integer |
		| 5    | INT32 | Thirty two bit signed integer |
		| 6    | UINT64 | 64 bit unsigned integer |
		| 7    | INT64 | 64 bit signed integer |
		| 8    | FLOAT | Thirty two bit floating point |
		| 9    | DOUBLE | Sixty four bit floating point |

	+ `bands` (int32_t): Number of bands or layers in the data buffer.
	+ `cols` (int32_t): Number of columns in the data buffer.
	+ `rows` (int32_t): Number of rows in the data buffer.
	+ `no_data` (double): NoData value for the tile (to be considered when applying algebraic operations). `-infinity` if not defined.

+ `data`[] (uint8_t): Interleaved pixel data for all bands, stored in row-major order. The size of this array depends on the data type, number of bands, and tile dimensions.

The default `data_format` is `RAW` (uncompressed). Choosing a compressed format reduces BLOB size and memory usage at the cost of additional CPU overhead. Any arithmetic operation on a datacube automatically decompresses and promotes values to double precision internally, so if you intend to perform calculations it is more efficient not to use compression at read time. Use `RT_Cube2Type<TYPE>` to convert the result back to the desired data type before writing to a new file.

`RT_Read` supports filter pushdown on all non-BLOB columns. Use the `bbox` struct or the `geometry` column to spatially filter tiles before the pixel data is loaded, which avoids reading unnecessary data from disk.

By using `RT_Read`, the extension also provides “replacement scans” for common raster file formats (`.tif`, `.img`, `.vrt`), allowing you to query files of these formats as if they were tables directly.

#### Signature

```sql
RT_Read (file_path [VARCHAR, VARCHAR[]],
         open_options VARCHAR[] DEFAULT NULL,
         allowed_drivers VARCHAR[] DEFAULT NULL,
         sibling_files VARCHAR[] DEFAULT NULL,
         separate_bands BOOLEAN DEFAULT false,
         data_format VARCHAR DEFAULT 'RAW',
         blocksize_x INTEGER DEFAULT NULL,
         blocksize_y INTEGER DEFAULT NULL,
         skip_empty_tiles BOOLEAN DEFAULT true,
         datacube BOOLEAN DEFAULT false
         )
```

#### Examples

```sql
SELECT * FROM RT_Read('path/to/raster/file.tif');

SELECT
    geometry, databand_1
FROM
    RT_Read([
        'path/to/mosaic/raster-clip00.tif',
        'path/to/mosaic/raster-clip01.tif',
        'path/to/mosaic/raster-clip10.tif',
        'path/to/mosaic/raster-clip11.tif'
    ])
;
```

----

### RT_Write

You can write new raster files in DuckDB using the `COPY` command and `FORMAT RASTER`.

The extension reads the `geometry` column to derive the spatial extent and pixel resolution of the output raster, and the specified datacube columns to populate its pixel values.

The extension provides the format `RASTER` and a set of options to control the writing process:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `FORMAT` | VARCHAR | Must be set to 'RASTER' to use the raster writing functionality. |
| `DRIVER` | VARCHAR | The GDAL driver to use to write the raster file. You can check available drivers using `RT_Drivers` function. |
| `CREATION_OPTIONS` | VARCHAR[] | A list of key-value pairs that are passed to the GDAL driver to control the creation of the file. Read GDAL documentation for available options. |
| `RESAMPLING` | VARCHAR | The resampling method to use when the tile size of the input data does not match the block size of the output raster. Available options are `nearest`, `bilinear`, `cubic`, `cubicspline`, `lanczos`, `average`, `mode`.... `nearest` is the default. |
| `ENVELOPE` | DOUBLE[] | The spatial extent of the output raster in the format [xmin, ymin, xmax, ymax]. If not provided, the extent will be calculated from the input tiles. |
| `COMPUTE_VALID_ENVELOPE` | BOOLEAN | Whether to compute the spatial extent of the output raster based on the valid (non-no-data) cells of the input tiles. If `true`, the extension will calculate the bounding box that encompasses all valid cells in the input tiles and use it as the spatial extent of the output raster. This option is useful when the input tiles have a lot of no-data cells and you want to avoid creating a raster with a large extent but mostly empty. `false` is the default, which means that the spatial extent of the output raster will be calculated based on the geometries of the input tiles, regardless of their data values. |
| `SRS` | VARCHAR | The spatial reference system of the output raster in WKT or EPSG code format. |
| `GEOMETRY_COLUMN` | VARCHAR | The name of the column that contains the geometry of the tiles. This column will be used to calculate the spatial extent and resolution of the output raster. It must be a column of type `GEOMETRY`. `geometry` is the default name. |
| `DATABAND_COLUMNS` | VARCHAR[] | Ordered list of datacube columns to write as raster bands. Each column must be a BLOB with the internal structure produced by `RT_Read` or `RT_Array2Cube`. |

Raster rotation is not supported, so the input `geometry` column must contain axis-aligned polygons that represent the footprint of each tile.

#### Signature

```sql
COPY (
	SELECT geometry, databand_1, ...
)
TO 'path/to/output/file.tif'
WITH (
	FORMAT RASTER,
	...
);
```

#### Examples

You can write a new raster file from an existing one by running:

```sql
COPY (
   	SELECT
		geometry,
		databand_1, databand_2, databand_3
	FROM
		RT_Read('path/to/raster/file.tif')
)
TO 'path/to/output/file.tif'
WITH (
	FORMAT RASTER,
	DRIVER 'COG',
	CREATION_OPTIONS ('COMPRESS=LZW'),
	RESAMPLING 'nearest',
	ENVELOPE [545539.750, 4724420.250, 545699.750, 4724510.250],
	--COMPUTE_VALID_ENVELOPE true,
	SRS 'EPSG:25830',
	GEOMETRY_COLUMN 'geometry',
	DATABAND_COLUMNS ['databand_3', 'databand_2', 'databand_1']
);
```

Because every row includes a `geometry` column, you can also export tile footprints to any vector format supported by the `spatial` extension:

```sql
COPY (
   	SELECT
		* EXCLUDE(databand_1,databand_2,databand_3)
   	FROM
		RT_Read('path/to/raster/file.tif')
)
TO 'path/to/output/file.parquet'
WITH (
	FORMAT PARQUET, GEOPARQUET_VERSION 'V1'
);

-- Or using the spatial extension, for example, writing a GeoPackage file:

LOAD spatial;

COPY (
	SELECT
		* EXCLUDE(databand_1,databand_2,databand_3)
	FROM
		RT_Read('path/to/raster/file.tif')
)
TO 'path/to/output/file.gpkg'
WITH (
	FORMAT GDAL, DRIVER 'GPKG', SRS 'EPSG:4326'
);
```

----

## Scalar Functions

### RT_Cube2Array

Extracts the pixel values of a datacube column into a plain SQL array of a chosen numeric type.

Function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `datacube` | DATACUBE | The datacube column to extract values from. |
| `filter_nodata` | BOOLEAN | When `true`, nodata cells are excluded from the output array. |

Extension provides a different function for each numeric data type:

| Function | Description |
| -------- | ----------- |
| `RT_Cube2ArrayUInt8` | Transforms a datacube column into an array of UINT8 values |
| `RT_Cube2ArrayInt8` | Transforms a datacube column into an array of INT8 values |
| `RT_Cube2ArrayUInt16` | Transforms a datacube column into an array of UINT16 values |
| `RT_Cube2ArrayInt16` | Transforms a datacube column into an array of INT16 values |
| `RT_Cube2ArrayUInt32` | Transforms a datacube column into an array of UINT32 values |
| `RT_Cube2ArrayInt32` | Transforms a datacube column into an array of INT32 values |
| `RT_Cube2ArrayUInt64` | Transforms a datacube column into an array of UINT64 values |
| `RT_Cube2ArrayInt64` | Transforms a datacube column into an array of INT64 values |
| `RT_Cube2ArrayFloat` | Transforms a datacube column into an array of FLOAT values |
| `RT_Cube2ArrayDouble` | Transforms a datacube column into an array of DOUBLE values |

Functions return a struct with the following fields:

+ `data_type` (INT): Numeric data type code of the source datacube.
+ `bands` (INT): Number of bands in the tile.
+ `cols` (INT): Number of pixel columns in the tile.
+ `rows` (INT): Number of pixel rows in the tile.
+ `no_data` (DOUBLE): Nodata sentinel value (`-infinity` when not defined).
+ `values` (ARRAY): Flat array of pixel values in row-major order.

A direct SQL cast (`::DOUBLE[]`, etc.) is also supported as a shorthand, but nodata values are not filtered in that case.

#### Signature

```sql
RT_Cube2Array<data_type> (datacube DATACUBE, filter_nodata BOOLEAN)
```

#### Examples

```sql
SELECT
	RT_Cube2ArrayInt32(databand_1, true) AS r,
	RT_Cube2ArrayInt32(databand_2, true) AS g,
	RT_Cube2ArrayInt32(databand_3, true) AS b
FROM
	RT_Read('path/to/raster/file.tif')
;
```

This function set allows you to perform operations on the tile data directly in SQL:

```sql
WITH __input AS (
	SELECT
		RT_Cube2ArrayInt32(databand_1, false) AS r
	FROM
		RT_Read('path/to/raster/file.tif', blocksize_x := 512, blocksize_y := 512)
)
SELECT
	list_min(r.values)        AS r_min,
	list_max(r.values)        AS r_max,
	list_stddev_pop(r.values) AS r_stddev
FROM
	__input
;
```

> **Performance tip:** Choose the `RT_Cube2Array<TYPE>` variant whose type matches the datacube's native type. A type mismatch requires value conversion on every pixel. The native data type of each band is available in the `metadata` column returned by `RT_Read`.

Using a direct SQL cast is equivalent but does **not** filter nodata values:

```sql
SELECT
	databand_1::DOUBLE[] AS r_array,
FROM
	RT_Read('path/to/raster/file.tif')
;
```

----

### RT_Cube2Type

Changes the pixel data type of a datacube in-place, returning a new datacube of the same dimensions.

All arithmetic operations produce `DOUBLE` values internally. Use this function to convert the result to the desired storage type before writing to a raster file, or to reinterpret the data type of an existing band (e.g. from `INT16` to `FLOAT`).

Function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `datacube` | DATACUBE | The datacube column whose pixel type will be converted. |

Extension provides a different function for each numeric data type:

| Function | Description |
| -------- | ----------- |
| `RT_Cube2TypeUInt8` | Transforms a datacube column into a datacube with UINT8 values |
| `RT_Cube2TypeInt8` | Transforms a datacube column into a datacube with INT8 values |
| `RT_Cube2TypeUInt16` | Transforms a datacube column into a datacube with UINT16 values |
| `RT_Cube2TypeInt16` | Transforms a datacube column into a datacube with INT16 values |
| `RT_Cube2TypeUInt32` | Transforms a datacube column into a datacube with UINT32 values |
| `RT_Cube2TypeInt32` | Transforms a datacube column into a datacube with INT32 values |
| `RT_Cube2TypeUInt64` | Transforms a datacube column into a datacube with UINT64 values |
| `RT_Cube2TypeInt64` | Transforms a datacube column into a datacube with INT64 values |
| `RT_Cube2TypeFloat` | Transforms a datacube column into a datacube with FLOAT values |
| `RT_Cube2TypeDouble` | Transforms a datacube column into a datacube with DOUBLE values |

#### Signature

```sql
RT_Cube2Type<data_type> (datacube DATACUBE)
```

#### Examples

```sql
SELECT
	RT_Cube2TypeFloat(databand_1 / 1000) AS r_float,
	RT_Cube2TypeFloat(databand_2 / 1000) AS g_float,
	RT_Cube2TypeFloat(databand_3 / 1000) AS b_float
FROM
	RT_Read('path/to/raster/file.tif')
;
```

----

### RT_Array2Cube

Packages a plain SQL array of numeric values back into a datacube BLOB, the inverse of `RT_Cube2Array`.

Use this function to convert the output of array-level operations (e.g. `list_transform`, custom UDFs) back into a datacube that can be written to a raster file with `COPY … FORMAT RASTER`.

Function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `array` | ARRAY | The array of numeric values to transform into a BLOB column. |
| `data_format` | VARCHAR | The data format to use for packing the data into the BLOB. |
| `bands` | INT | Number of bands or layers in the data buffer. |
| `cols` | INT | Number of columns in the tile. |
| `rows` | INT | Number of rows in the tile. |
| `no_data` | DOUBLE | NoData value for the tile (to be considered when applying algebraic operations). |

#### Signature

```sql
RT_Array2Cube (array ARRAY, data_format VARCHAR, bands INT, cols INT, rows INT, no_data DOUBLE)
```

#### Examples

```sql
WITH __input AS (
	SELECT
		RT_Cube2ArrayInt32(databand_1, false) AS r
	FROM
		RT_Read('path/to/raster/file.tif', blocksize_x := 512, blocksize_y := 512)
)
SELECT
	RT_Array2Cube(r.values, 'RAW', r.bands, r.cols, r.rows, r.no_data) AS r_array
FROM
	__input
;
```

----

### RT_CubeUnaryOp

Applies a unary operation element-wise to every pixel of the input datacube. Returns a new datacube of the same dimensions and data type. Nodata cells are preserved unchanged.

| Function | Description |
| -------- | ----------- |
| `RT_CubeNeg` | Returns a datacube with each cell negated (multiplied by -1). |
| `RT_CubeAbs` | Returns a datacube with the absolute value of each cell. |
| `RT_CubeSqrt` | Returns a datacube with the square root of each cell. |
| `RT_CubeLog` | Returns a datacube with the natural logarithm of each cell. |
| `RT_CubeExp` | Returns a datacube with the exponential (e^x) of each cell. |

#### Signature

```sql
RT_Cube<funcname> (datacube DATACUBE)
```

#### Examples

```sql
SELECT
	RT_CubeNeg(databand_1) AS neg
FROM
	RT_Read('path/to/raster/file.tif')
;
```

----

### RT_CubeBinaryOp

Applies a binary operation cell-by-cell between two datacubes or a datacube and a scalar. Returns a new datacube of the same dimensions. No-data cells are preserved unless otherwise noted.

**Arithmetic**

| Function | Description |
| -------- | ----------- |
| `RT_CubeAdd` (`+`) | Returns a datacube with each cell equal to the sum of the two inputs. |
| `RT_CubeSubtract` (`-`) | Returns a datacube with each cell equal to the left-hand cell minus the right-hand cell. |
| `RT_CubeMultiply` (`*`) | Returns a datacube with each cell equal to the product of the two inputs. |
| `RT_CubeDivide` (`/`) | Returns a datacube with each cell equal to the left-hand cell divided by the right-hand cell. |
| `RT_CubePow` (`^`) | Returns a datacube with each cell raised to the power of the right-hand value. |
| `RT_CubeMod` (`%`) | Returns a datacube with each cell equal to the remainder of dividing the left-hand cell by the right-hand value. |

**Comparison** (result cells are 1 if true, 0 if false)

| Function | Description |
| -------- | ----------- |
| `RT_CubeEqual` | Returns a datacube where each cell is 1 if left == right, 0 otherwise. |
| `RT_CubeNotEqual` | Returns a datacube where each cell is 1 if left != right, 0 otherwise. |
| `RT_CubeLess` | Returns a datacube where each cell is 1 if left < right, 0 otherwise. |
| `RT_CubeLessEqual` | Returns a datacube where each cell is 1 if left <= right, 0 otherwise. |
| `RT_CubeGreater` | Returns a datacube where each cell is 1 if left > right, 0 otherwise. |
| `RT_CubeGreaterEqual` | Returns a datacube where each cell is 1 if left >= right, 0 otherwise. |

**Assignment / Utility**

| Function | Description |
| -------- | ----------- |
| `RT_CubeSet` | Returns a datacube where valid cells are replaced by the right-hand value. No-data cells in the source are preserved. |
| `RT_CubeSetNoData` | Returns a datacube where nodata cells are replaced by the specified value, and sets this value as the new nodata sentinel. |
| `RT_CubeFill` | Returns a datacube where all cells (including no-data) are unconditionally replaced by the right-hand value. |
| `RT_CubeMin` | Returns a datacube with each cell equal to the minimum of the two inputs. |
| `RT_CubeMax` | Returns a datacube with each cell equal to the maximum of the two inputs. |
| `RT_CubeNullOrEmpty` | Returns true if the datacube is null or empty, false otherwise. |

The math operators (`+`, `-`, `*`, `/`, `^`, `%`) are also supported as aliases of the corresponding arithmetic functions.

#### Signature

```sql
RT_Cube<funcname> (databand_a DATACUBE, value_b [DATACUBE, double])
```

#### Examples

```sql
SELECT
	RT_CubeAdd(databand_1, 10) AS v1,
	RT_CubeAdd(databand_1, databand_2) AS v2,
	(v1 + v2) AS v3
FROM
	RT_Read('path/to/raster/file.tif')
;
```

----

### RT_CubeStats

Calculates statistics for a specific band (0-based index) of a datacube.

The returned value is a `STRUCT` with the following fields:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `minimum` | DOUBLE | Minimum pixel value among valid (non-nodata) cells. |
| `maximum` | DOUBLE | Maximum pixel value among valid (non-nodata) cells. |
| `mean` | DOUBLE | Mean (average) of all valid pixel values. |
| `stddev` | DOUBLE | Population standard deviation of all valid pixel values. |
| `valid_count` | BIGINT | Number of valid (non-nodata) cells. |
| `nodata_count` | BIGINT | Number of nodata cells. |

Function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `databand` | DATACUBE | The datacube column to compute statistics for. |
| `band_index` | INTEGER | The 0-based index of the band to compute statistics for. |

#### Signature

```sql
RT_CubeStats (datacube DATACUBE, band_index INTEGER)
```

#### Examples

```sql
SELECT
    RT_CubeStats(databand_1, 0) AS stats
FROM
    RT_Read('path/to/raster/file.tif')
;

-- Access individual fields:
SELECT
    stats.minimum,
    stats.maximum,
    stats.mean,
    stats.stddev,
    stats.valid_count,
    stats.nodata_count
FROM (
    SELECT RT_CubeStats(databand_1, 0) AS stats
    FROM RT_Read('path/to/raster/file.tif')
);
```

----

### RT_GdalConfig

Sets a GDAL configuration option (equivalent to CPLSetConfigOption).

This is useful, for example, to allow unauthenticated access to public S3 buckets
when using GDAL-native VSI paths.

Function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `key` | VARCHAR | The GDAL configuration option key. |
| `value` | VARCHAR | The value to set for the configuration option. Pass NULL when no value is needed. |

#### Signature

```sql
RT_GdalConfig (key VARCHAR, value VARCHAR)
```

#### Examples

```sql
SELECT RT_GdalConfig('AWS_NO_SIGN_REQUEST', 'YES');
```

----

## Spatial Functions

### RT_Envelope

Computes the bounding box of the valid (non-no-data) cells in the input datacube and returns it as a geometry.

The function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `databand` | DATACUBE | The datacube column to polygonize. |
| `tile_x` | INTEGER | The tile x coordinate of the tile. |
| `tile_y` | INTEGER | The tile y coordinate of the tile. |
| `blocksize_x` | INTEGER | The block size of the tile in the x direction. |
| `blocksize_y` | INTEGER | The block size of the tile in the y direction. |
| `geo_transform` | DOUBLE[] | The Geo Transform matrix of the tile. This is an array of 6 values representing the affine transformation coefficients. |

`blocksize_x`, `blocksize_y` and `geo_transform` parameters can be extracted from the datacube `metadata` column.

#### Signature

```sql
RT_Envelope (datacube DATACUBE,
             tile_x INTEGER,
             tile_y INTEGER,
             blocksize_x INTEGER,
             blocksize_y INTEGER,
             geo_transform DOUBLE[])
```

#### Examples

```sql
LOAD json;

SELECT
    RT_Envelope(databand_1,
                tile_x,
                tile_y,
               (metadata->'blocksize_x')::INTEGER,
               (metadata->'blocksize_y')::INTEGER,
               (metadata->'transform')::DOUBLE[]) AS geometry
FROM
    RT_Read('path/to/raster/file.tif')
;
```

----

### RT_Polygon

Creates a polygon geometry for each contiguous region of non-no-data values in the datacube.

This function takes a datacube column as input and returns polygon geometry representing the contiguous regions of non-no-data values in the datacube. The function needs the tile coordinates, Geo Transform matrix, and blocksize of the datacube to calculate the geometry of the output polygons.

The function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `databand` | DATACUBE | The datacube column to polygonize. |
| `tile_x` | INTEGER | The tile x coordinate of the tile. |
| `tile_y` | INTEGER | The tile y coordinate of the tile. |
| `blocksize_x` | INTEGER | The block size of the tile in the x direction. |
| `blocksize_y` | INTEGER | The block size of the tile in the y direction. |
| `geo_transform` | DOUBLE[] | The Geo Transform matrix of the tile. This is an array of 6 values representing the affine transformation coefficients. |

`blocksize_x`, `blocksize_y` and `geo_transform` parameters can be extracted from the datacube `metadata` column.

#### Signature

```sql
RT_Polygon (datacube DATACUBE,
            tile_x INTEGER,
            tile_y INTEGER,
            blocksize_x INTEGER,
            blocksize_y INTEGER,
            geo_transform DOUBLE[])
```

#### Examples

```sql
LOAD json;

SELECT
    RT_Polygon(databand_1,
               tile_x,
               tile_y,
              (metadata->'blocksize_x')::INTEGER,
              (metadata->'blocksize_y')::INTEGER,
              (metadata->'transform')::DOUBLE[]) AS geometry
FROM
    RT_Read('path/to/raster/file.tif')
;
```

----

### RT_CubeClip

Returns a datacube where cells outside the given geometry are replaced by the specified value. Cells inside the geometry are preserved. No-data cells are preserved.

The function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `databand` | DATACUBE | The input datacube column. |
| `tile_x` | INTEGER | The tile x coordinate of the tile. |
| `tile_y` | INTEGER | The tile y coordinate of the tile. |
| `blocksize_x` | INTEGER | The block size of the tile in the x direction. |
| `blocksize_y` | INTEGER | The block size of the tile in the y direction. |
| `geo_transform` | DOUBLE[] | The Geo Transform matrix of the tile. This is an array of 6 values representing the affine transformation coefficients. |
| `geometry` | GEOMETRY | The clip geometry. Cells outside this geometry will be replaced by `value`. |
| `value` | DOUBLE | The value to use for cells outside the geometry. |

#### Signature

```sql
RT_CubeClip (datacube DATACUBE,
             tile_x INTEGER,
             tile_y INTEGER,
             blocksize_x INTEGER,
             blocksize_y INTEGER,
             geo_transform DOUBLE[],
             geometry GEOMETRY,
             value DOUBLE)
```

#### Examples

```sql
LOAD json;
LOAD spatial;

SELECT
    RT_CubeClip(databand_1,
                tile_x,
                tile_y,
               (metadata->'blocksize_x')::INTEGER,
               (metadata->'blocksize_y')::INTEGER,
               (metadata->'transform')::DOUBLE[],
                ST_GeomFromText('POLYGON((...))'),
               (metadata->'bands'->0->'nodata')::DOUBLE) AS clipped
FROM
    RT_Read('path/to/raster/file.tif')
;
```

----

### RT_CubeBurn

Returns a datacube where cells inside the given geometry are replaced by the specified value. Cells outside the geometry are preserved. No-data cells are preserved.

The function accepts the following parameters:

| Parameter | Type | Description |
| --------- | -----| ----------- |
| `databand` | DATACUBE | The input datacube column. |
| `tile_x` | INTEGER | The tile x coordinate of the tile. |
| `tile_y` | INTEGER | The tile y coordinate of the tile. |
| `blocksize_x` | INTEGER | The block size of the tile in the x direction. |
| `blocksize_y` | INTEGER | The block size of the tile in the y direction. |
| `geo_transform` | DOUBLE[] | The Geo Transform matrix of the tile. This is an array of 6 values representing the affine transformation coefficients. |
| `geometry` | GEOMETRY | The burn geometry. Cells inside this geometry will be replaced by `value`. |
| `value` | DOUBLE | The value to burn into cells inside the geometry. |

#### Signature

```sql
RT_CubeBurn (datacube DATACUBE,
             tile_x INTEGER,
             tile_y INTEGER,
             blocksize_x INTEGER,
             blocksize_y INTEGER,
             geo_transform DOUBLE[],
             geometry GEOMETRY,
             value DOUBLE)
```

#### Examples

```sql
LOAD json;
LOAD spatial;

SELECT
    RT_CubeBurn(databand_1,
                tile_x,
                tile_y,
               (metadata->'blocksize_x')::INTEGER,
               (metadata->'blocksize_y')::INTEGER,
               (metadata->'transform')::DOUBLE[],
                ST_GeomFromText('POLYGON((...))'),
                1.0) AS burned
FROM
    RT_Read('path/to/raster/file.tif')
;
```

----
