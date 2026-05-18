# DuckDB Raster Extension — Practical Guide

This guide walks through the most common use cases of the DuckDB Raster Extension, from opening a single file to running a complete Earth Observation analysis pipeline. For the full function reference, see the [functions](functions.md) page.

The examples use sample data from the [`test/data`](../test/data/) folder. You can substitute any raster file supported by GDAL, including remote files accessed over HTTP or S3.

**Contents:**

1. [Reading Raster Files](#1-reading-raster-files)
2. [Writing Raster Files](#2-writing-raster-files)
3. [Band Algebra](#3-band-algebra)
4. [Spatial Queries](#4-spatial-queries)
5. [End-to-End Earth Observation Analysis](#5-end-to-end-earth-observation-analysis)

---

## 1. Reading Raster Files

### From a local file

The simplest way to read a raster file is to pass its path to `RT_Read`. The result is a table where each row represents one tile and each band is exposed as a separate `BLOB` column:

```sql
SELECT * FROM RT_Read('./test/data/overlay-sample.tiff');
```

> **Tip:** `RT_Read` also supports a `datacube` option that merges all band columns into a single N-dimensional array `BLOB` column instead of one column per band.

### Controlling the tile size

The `blocksize_x` and `blocksize_y` parameters let you override the block size stored in the file. This is useful for controlling how much data is loaded per row. The following query reads the file in 512×512 pixel tiles regardless of the block size defined in the file:

```sql
SELECT * FROM RT_Read('./test/data/overlay-sample.tiff', blocksize_x := 512, blocksize_y := 512);
```

### From a remote S3 bucket

Use the `/vsis3/` prefix to instruct GDAL's virtual file system to read directly from S3. For public buckets, disable signature checking first:

```sql
SELECT RT_GdalConfig('AWS_NO_SIGN_REQUEST', 'YES');

SELECT
    *
FROM
    RT_Read('/vsis3/sentinel-cogs/sentinel-s2-l2a-cogs/30/T/WN/2021/9/S2B_30TWN_20210930_0_L2A/B02.tif')
LIMIT 5
;
```

Alternatively, use the native DuckDB S3 path format (see the `httpfs` extension documentation for authentication options):

```sql
SELECT
    *
FROM
    RT_Read('s3://sentinel-cogs/sentinel-s2-l2a-cogs/30/T/WN/2021/9/S2B_30TWN_20210930_0_L2A/B02.tif')
LIMIT 5
;
```

### Multiple files as a mosaic

Pass an array of paths to `RT_Read` to open several files as a single virtual mosaic. The files are stitched together automatically:

```sql
SELECT
    x, y, bbox, geometry, level, tile_x, tile_y, cols, rows, metadata
FROM
    RT_Read([
        './test/data/mosaic/SCL.tif-land-clip00.tiff',
        './test/data/mosaic/SCL.tif-land-clip01.tiff',
        './test/data/mosaic/SCL.tif-land-clip10.tiff',
        './test/data/mosaic/SCL.tif-land-clip11.tiff'
    ])
;
```

<img src="images/read_multiple.png" alt="read_multiple.png" width="800"/>

> **Note on `separate_bands`:** By default (`separate_bands := false`), the input files are treated as tiles of a larger mosaic and the result has the same number of bands as each individual file. Setting `separate_bands := true` places each file into its own band of the VRT dataset, which is useful when reading spectrally different bands stored in separate files (see the NDVI example in [Section 5](#5-end-to-end-earth-observation-analysis)).

---

## 2. Writing Raster Files

### Exporting to a raster format

Use the `COPY … TO` statement with `FORMAT RASTER` to write query results to a raster file. The `DRIVER` option specifies the output format (any GDAL-supported driver). Use `DATABAND_COLUMNS` to control which columns are written as bands and in what order:

```sql
COPY (
    SELECT * FROM RT_Read('./test/data/overlay-sample.tiff')
)
TO './test/data/copy_to_raster.png'
WITH (
    FORMAT RASTER,
    DRIVER 'PNG',
    CREATION_OPTIONS ('WORLDFILE=YES'),
    RESAMPLING 'nearest',
    ENVELOPE [545539.750, 4724420.250, 545699.750, 4724510.250],
    SRS 'EPSG:25830',
    GEOMETRY_COLUMN 'geometry',
    DATABAND_COLUMNS ['databand_3', 'databand_2', 'databand_1']
);
```

<img src="images/copy_to_raster.png" alt="copy_to_raster.png" width="800"/>

For the full list of creation options refer to the [function reference](functions.md#rt_write) and to the [GDAL driver documentation](https://gdal.org/drivers/raster/index.html).

### Exporting a mosaic to Cloud-Optimized GeoTIFF

The same `COPY … TO` syntax works when writing a mosaic assembled from multiple input files:

```sql
COPY (
    SELECT
        *
    FROM
        RT_Read([
            './test/data/mosaic/SCL.tif-land-clip00.tiff',
            './test/data/mosaic/SCL.tif-land-clip01.tiff',
            './test/data/mosaic/SCL.tif-land-clip10.tiff',
            './test/data/mosaic/SCL.tif-land-clip11.tiff'
        ])
)
TO './test/data/copy_to_cog.tiff'
WITH (
    FORMAT RASTER,
    DRIVER 'COG',
    CREATION_OPTIONS ('COMPRESS=LZW'),
    RESAMPLING 'nearest',
    SRS 'EPSG:25830',
    GEOMETRY_COLUMN 'geometry',
    DATABAND_COLUMNS ['databand_1']
);
```

<img src="images/copy_to_cog.png" alt="copy_to_cog.png" width="800"/>

### Exporting tile footprints to vector formats

Because every row in `RT_Read`'s output includes a `geometry` column, you can use the `spatial` extension to write tile footprints directly to vector formats such as GeoParquet or GeoPackage:

```sql
-- Export tile footprints to GeoParquet
COPY (
    SELECT
        id, x, y, tile_x, tile_y, cols, rows, geometry, metadata
    FROM
        RT_Read([
            './test/data/mosaic/SCL.tif-land-clip00.tiff',
            './test/data/mosaic/SCL.tif-land-clip01.tiff',
            './test/data/mosaic/SCL.tif-land-clip10.tiff',
            './test/data/mosaic/SCL.tif-land-clip11.tiff'
        ])
    WHERE
        NOT RT_CubeNullOrEmpty(databand_1)
)
TO './test/data/copy_to_geoparquet.parquet'
WITH (
    FORMAT PARQUET, GEOPARQUET_VERSION 'V1'
);

LOAD spatial;

-- Export tile footprints to GeoPackage
COPY (
    SELECT
        id, x, y, tile_x, tile_y, cols, rows, geometry, metadata
    FROM
        RT_Read([
            './test/data/mosaic/SCL.tif-land-clip00.tiff',
            './test/data/mosaic/SCL.tif-land-clip01.tiff',
            './test/data/mosaic/SCL.tif-land-clip10.tiff',
            './test/data/mosaic/SCL.tif-land-clip11.tiff'
        ])
    WHERE
        NOT RT_CubeNullOrEmpty(databand_1)
)
TO './test/data/copy_to_geopackage.gpkg'
WITH (
    FORMAT GDAL, DRIVER 'GPKG', SRS 'EPSG:32630'
);
```

<img src="images/copy_to_geopackage.png" alt="copy_to_geopackage.png" width="800"/>

---

## 3. Band Algebra

Databands support standard arithmetic operators (`+`, `-`, `*`, `/`) as well as a set of built-in [functions](functions.md#rt_cubebinaryop) for common operations. Operations apply element-wise across the pixels of each tile:

```sql
SELECT
    databand_1 + databand_2 AS sum_bands,
    RT_CubeAdd(databand_1, databand_2) - 1.8 AS sum_func_offset,
    databand_1 * 2 AS scaled_band
FROM
    RT_Read('./test/data/overlay-sample.tiff')
;
```

---

## 4. Spatial Queries

### Filtering by geometry intersection

Every tile row exposes a `geometry` column that you can use with any spatial function from the `spatial` extension. The following example selects only the tiles that intersect a reference polygon:

```sql
WITH __clip_layer AS (
    SELECT geom FROM ST_Read('./test/data/CATAST_Pol_Township-PNA.geojson')
),
__dataset AS (
    SELECT
        id, x, y, tile_x, tile_y, cols, rows, geometry, databand_1, metadata
    FROM
        __clip_layer,
        RT_Read([
            './test/data/mosaic/SCL.tif-land-clip00.tiff',
            './test/data/mosaic/SCL.tif-land-clip01.tiff',
            './test/data/mosaic/SCL.tif-land-clip10.tiff',
            './test/data/mosaic/SCL.tif-land-clip11.tiff'
        ])
    WHERE
        ST_Intersects(__clip_layer.geom, geometry)
)
SELECT * FROM __dataset;
```

### Fast bounding-box filtering

For larger datasets, filtering on the `bbox` column (a struct with fields `xmin`, `ymin`, `xmax`, `ymax`) is faster than computing full geometry intersections because it avoids deserializing the `geometry` column:

```sql
SELECT
    *
FROM
    RT_Read('./test/data/overlay-sample.tiff')
WHERE
    bbox.xmin >  545500.0 AND bbox.xmax <  545800.0
    AND
    bbox.ymin > 4724400.0 AND bbox.ymax < 4724600.0
;
```

---

## 5. End-to-End Earth Observation Analysis

This section builds a complete pipeline that queries a [STAC API](https://stacspec.org/) catalog to discover Sentinel-2 imagery, reads the relevant spectral bands, and computes the **Normalized Difference Vegetation Index (NDVI)**:

$$NDVI = \frac{NIR - RED}{NIR + RED}$$

The pipeline is introduced step by step — from a basic catalog search to a full multi-tile AOI workflow — before presenting the complete solution.

> **Prerequisites:** The examples below require the `json`, `spatial`, and `http_client` extensions. Run the following once per session:
> ```sql
> LOAD json;
> LOAD spatial;
> INSTALL http_client FROM community;
> LOAD http_client;
> ```

### Step 1 — Discover products with a basic STAC search

The simplest way to explore a STAC catalog is to send a GET request to its `/search` endpoint and parse the JSON response:

```sql
WITH __input AS (
    -- Issue an HTTP GET to the STAC search endpoint.
    SELECT
        http_get('https://earth-search.aws.element84.com/v0/search') AS res
),
__features AS (
    -- Unnest the 'features' array from the response body.
    SELECT
        unnest( from_json(((res->>'body')::JSON)->'features', '["json"]') ) AS features
    FROM
        __input
)
SELECT
    features->>'id' AS id,
    features->'properties'->>'sentinel:product_id' AS product_id,
    concat(
        'T',
        features->'properties'->>'sentinel:utm_zone',
        features->'properties'->>'sentinel:latitude_band',
        features->'properties'->>'sentinel:grid_square'
    ) AS grid_id,
    ST_GeomFromGeoJSON(features->'geometry') AS geom
FROM
    __features
;
```

> To search a different collection, replace `sentinel-s2-l2a-cogs` with the desired collection identifier and update the band names in the subsequent steps.

### Step 2 — Filter by area of interest and date range

A POST request allows you to supply a GeoJSON geometry as an intersects filter and restrict results to a specific date range:

```sql
WITH __aoi AS (
    -- Load the area of interest from a GeoJSON file.
    SELECT
        geom
    FROM
        ST_Read('./test/data/CATAST_Pol_Township-PNA.geojson')
),
__geojson AS (
    -- Reproject to WGS84 (EPSG:4326) and serialize as GeoJSON, as required by the STAC API.
    SELECT
        ST_AsGeoJSON( ST_Transform(geom, 'EPSG:32630', 'EPSG:4326', always_xy := true) ) AS g
    FROM
        __aoi
    LIMIT 1
),
__input AS (
    -- POST the search request with AOI and date filters.
    SELECT
        http_post('https://earth-search.aws.element84.com/v0/search',
            headers => MAP {
                'Content-Type': 'application/json',
                'Accept-Encoding': 'gzip',
                'Accept': 'application/geo+json'
            },
            params => {
                'collections': ['sentinel-s2-l2a-cogs'],
                'datetime': '2021-09-30/2021-09-30',
                'intersects': (SELECT g FROM __geojson),
                'limit': 16
            }
        ) AS data
),
__features AS (
    SELECT
        unnest( from_json( (data->>'body')->'features', '["json"]') ) AS features
    FROM
        __input
)
SELECT
    features->>'id' AS id,
    features->'properties'->>'sentinel:product_id' AS product_id,
    concat(
        'T',
        features->'properties'->>'sentinel:utm_zone',
        features->'properties'->>'sentinel:latitude_band',
        features->'properties'->>'sentinel:grid_square'
    ) AS grid_id,
    [
        features->'assets'->'B02'->>'href',
        features->'assets'->'B03'->>'href',
        features->'assets'->'B04'->>'href'
    ] AS bands,
    ST_GeomFromGeoJSON(features->'geometry') AS geom
FROM
    __features
;
```

### Step 3 — Compute NDVI from a known product

When the asset URLs are already known, you can compute NDVI directly. Pass both the NIR band (`B08`) and the RED band (`B04`) to `RT_Read` with `separate_bands := true` so each file becomes its own databand:

```sql
COPY (
    WITH __input AS (
        -- Read NIR (B08) as databand_1 and RED (B04) as databand_2.
        SELECT
            geometry,
            databand_1 AS nir,
            databand_2 AS red
        FROM
            RT_Read(
                [
                    '/vsis3/sentinel-cogs/sentinel-s2-l2a-cogs/30/T/WN/2021/9/S2B_30TWN_20210930_0_L2A/B08.tif',
                    '/vsis3/sentinel-cogs/sentinel-s2-l2a-cogs/30/T/WN/2021/9/S2B_30TWN_20210930_0_L2A/B04.tif'
                ],
                separate_bands := true,
                blocksize_x := 1024,
                blocksize_y := 1024
            )
    )
    -- Apply the NDVI formula and convert the result to floating-point.
    SELECT
        geometry,
        RT_Cube2TypeFloat( (nir - red) / (nir + red) ) AS ndvi
    FROM
        __input
)
TO './test/data/ndvi.tiff'
WITH (
    FORMAT RASTER,
    DRIVER 'COG',
    CREATION_OPTIONS ('COMPRESS=LZW'),
    RESAMPLING 'nearest',
    SRS 'EPSG:32630',
    GEOMETRY_COLUMN 'geometry',
    DATABAND_COLUMNS ['ndvi']
);
```

### Step 4 — Complete AOI workflow with dynamic STAC discovery

The previous examples used hard-coded asset URLs. This final workflow discovers products dynamically and processes all matching tiles — potentially spanning several Sentinel-2 granules.

**Important constraint:** `RT_Read` and `ST_Read` only accept **literal** path values at bind time; column references and subqueries are not allowed as arguments. The solution is to use `SET VARIABLE` / `getvariable()`: DuckDB resolves variables to constants before invoking the table function.

#### Part A — Search the catalog and store results

Run the STAC search once, persist the results in a temporary table, and then build array variables from it. This avoids repeating the HTTP request and correctly handles multi-granule results:

```sql
LOAD json;
LOAD spatial;
INSTALL http_client FROM community;
LOAD http_client;

-- Enable public S3 access via GDAL.
SELECT RT_GdalConfig('AWS_NO_SIGN_REQUEST', 'YES');

-- Search the STAC catalog and store all matching features.
CREATE OR REPLACE TEMP TABLE __search_results AS
    WITH __aoi AS (
        SELECT geom FROM ST_Read('./test/data/CATAST_Pol_Township-PNA.geojson')
    ),
    __geojson AS (
        SELECT
            ST_AsGeoJSON( ST_Transform(geom, 'EPSG:32630', 'EPSG:4326', always_xy := true) ) AS g
        FROM
            __aoi
        LIMIT 1
    ),
    __input AS (
        SELECT http_post('https://earth-search.aws.element84.com/v0/search',
            headers => MAP {
                'Content-Type': 'application/json',
                'Accept-Encoding': 'gzip',
                'Accept': 'application/geo+json'
            },
            params => {
                'collections': ['sentinel-s2-l2a-cogs'],
                'datetime': '2021-09-30/2021-09-30',
                'intersects': (SELECT g FROM __geojson),
                'limit': 16
            }
        ) AS data
    ),
    __features AS (
        SELECT
            unnest(from_json((data->>'body')->'features', '["json"]')) AS features
        FROM
            __input
    )
    SELECT
        replace(
            features->'assets'->'B08'->>'href',
            'https://sentinel-cogs.s3.us-west-2.amazonaws.com',
            '/vsis3/sentinel-cogs'
        ) AS nir_url,
        replace(
            features->'assets'->'B04'->>'href',
            'https://sentinel-cogs.s3.us-west-2.amazonaws.com',
            '/vsis3/sentinel-cogs'
        ) AS red_url
    FROM
        __features
;

-- Build one array variable per band — one URL per matching granule.
SET VARIABLE nir_urls = (SELECT list(nir_url) FROM __search_results);
SET VARIABLE red_urls = (SELECT list(red_url) FROM __search_results);

-- Verify the variables (optional):
-- SELECT getvariable('nir_urls');
-- SELECT getvariable('red_urls');
```

#### Part B — Read, clip, and compute NDVI

With the URL variables in place, read NIR and RED as two separate mosaics, join the tiles by their grid coordinates, clip each tile to the AOI, and write the NDVI result as a Cloud-Optimized GeoTIFF:

```sql
COPY (
    WITH __aoi AS (
        SELECT geom FROM ST_Read('./test/data/CATAST_Pol_Township-PNA.geojson')
    ),
    __nir AS (
        -- Read all NIR (B08) tiles as a single mosaic.
        SELECT
            tile_x, tile_y, geometry, metadata, databand_1 AS nir
        FROM
            RT_Read(getvariable('nir_urls'), blocksize_x := 1024, blocksize_y := 1024)
        WHERE
            ST_Intersects(geometry, (SELECT geom FROM __aoi))
    ),
    __red AS (
        -- Read all RED (B04) tiles as a single mosaic; the tile grid matches NIR.
        SELECT
            tile_x, tile_y, geometry, metadata, databand_1 AS red
        FROM
            RT_Read(getvariable('red_urls'), blocksize_x := 1024, blocksize_y := 1024)
        WHERE
            ST_Intersects(geometry, (SELECT geom FROM __aoi))
    ),
    __data AS (
        -- Join tiles by grid position, clip each to the AOI, and compute NDVI.
        SELECT
            n.tile_x,
            n.tile_y,
            n.geometry,
            n.metadata,
            RT_CubeClip(
                n.nir,
                n.tile_x,
                n.tile_y,
               (n.metadata->'blocksize_x')::INTEGER,
               (n.metadata->'blocksize_y')::INTEGER,
               (n.metadata->'transform')::DOUBLE[],
               (SELECT geom FROM __aoi),
               (n.metadata->'bands'->0->'nodata')::DOUBLE
            ) AS nir,
            RT_CubeClip(
                r.red,
                r.tile_x,
                r.tile_y,
               (r.metadata->'blocksize_x')::INTEGER,
               (r.metadata->'blocksize_y')::INTEGER,
               (r.metadata->'transform')::DOUBLE[],
               (SELECT geom FROM __aoi),
               (r.metadata->'bands'->0->'nodata')::DOUBLE
            ) AS red
        FROM
            __nir n
        JOIN
            __red r ON n.tile_x = r.tile_x AND n.tile_y = r.tile_y
    )
    SELECT
        geometry,
        RT_Cube2TypeFloat( (nir - red) / (nir + red) ) AS ndvi
    FROM
        __data
)
TO './test/data/sentinel2_to_ndvi.tiff'
WITH (
    FORMAT RASTER,
    DRIVER 'COG',
    CREATION_OPTIONS ('COMPRESS=LZW'),
    RESAMPLING 'nearest',
    SRS 'EPSG:32630',
    COMPUTE_VALID_ENVELOPE true,
    GEOMETRY_COLUMN 'geometry',
    DATABAND_COLUMNS ['ndvi']
);
```

<img src="images/sentinel2_to_ndvi.png" alt="sentinel2_to_ndvi.png" width="800"/>

---

From here, you can adapt any of these patterns to your own datasets and workflows. Refer to the [functions](functions.md) page for the complete API reference.
