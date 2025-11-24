# DuckDB Point Cloud Extension Function Reference

## Function Index

**[Table Functions](#table-functions)**

| Function | Summary |
| --- | --- |
| [`PDAL_Drivers`](#pdal_drivers) | Returns the list of supported stage types of a PDAL Pipeline. |
| [`PDAL_Info`](#pdal_info) | Read the metadata from a point cloud file. |
| [`PDAL_Pipeline`](#pdal_pipeline) | Read and import a point cloud data file, applying also a custom processing pipeline file to the data. |
| [`PDAL_Read`](#pdal_read) | Read and import a variety of point cloud data file formats using the PDAL library. |

----

## Table Functions

### PDAL_Drivers

#### Signature

```sql
PDAL_Drivers ()
```

#### Description


Returns the list of supported stage types of a PDAL Pipeline.

The stages of a PDAL Pipeline are divided into Readers, Filters and Writers: https://pdal.io/en/stable/stages/stages.html


#### Example

```sql

SELECT name, description FROM PDAL_Drivers();

┌─────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────┐
│            name             │                                     description                                 │
│           varchar           │                                       varchar                                   │
├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
│ filters.approximatecoplanar │ Estimates the planarity of a neighborhood of points using eigenvalues.          │
│ filters.assign              │ Assign values for a dimension range to a specified value.                       │
│ filters.chipper             │ Organize points into spatially contiguous, squarish, and non-overlapping chips. │
│ filters.cluster             │ Extract and label clusters using Euclidean distance.                            │
│      ·                      │      ·                                                                          │
│      ·                      │      ·                                                                          │
│      ·                      │      ·                                                                          │
│ readers.slpk                │ SLPK Reader                                                                     │
│ readers.smrmsg              │ SBET smrmsg Reader                                                              │
│ readers.stac                │ STAC Reader                                                                     │
│ readers.terrasolid          │ TerraSolid Reader                                                               │
│ writers.copc                │ COPC Writer                                                                     │
│ writers.gdal                │ Write a point cloud as a GDAL raster.                                           │
│ writers.las                 │ ASPRS LAS 1.0 - 1.4 writer                                                      │
│ writers.text                │ Text Writer                                                                     │
├─────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────┤
│ 119 rows                                                                                            2 columns │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

```

----

### PDAL_Info

#### Signature

```sql
PDAL_Info (file_name_pattern VARCHAR)
```

#### Description


Read the metadata from a point cloud file.

The `PDAL_Info` table function accompanies the `PDAL_Read` table function, but instead of reading the contents of a file, this function scans the metadata instead.


#### Example

```sql

SELECT * FROM PDAL_Info('./test/data/autzen_trim.laz');

```

----

### PDAL_Pipeline

#### Signature

```sql
PDAL_Pipeline (file_name VARCHAR, pipeline_file_name VARCHAR, options MAP(VARCHAR, VARCHAR))
```

#### Description


Read and import a variety of point cloud data file formats using the PDAL library,
applying also a custom processing pipeline file to the data.


#### Example

```sql

SELECT * FROM PDAL_Pipeline('path/to/your/filename.las', 'path/to/your/pipeline.json');

```

----

### PDAL_Read

#### Signature

```sql
PDAL_Read (file_name VARCHAR, options MAP(VARCHAR, VARCHAR))
```

#### Description


Read and import a variety of point cloud data file formats using the PDAL library.


#### Example

```sql

SELECT * FROM PDAL_Read('path/to/your/filename.las') LIMIT 10;

┌───────────┬───────────┬────────┐
│     X     │     Y     │   Z    │
│   double  │   double  │ double │
├───────────┼───────────┼────────┤
│ 637177.98 │ 849393.95 │ 411.19 │
│ 637177.30 │ 849396.95 │ 411.25 │
│ 637176.34 │ 849400.84 │ 411.01 │
│ 637175.45 │ 849404.62 │ 410.99 │
│ 637174.33 │ 849407.37 │ 411.38 │
└───────────┴───────────┴────────┘

SELECT * FROM PDAL_Read('path/to/your/filename.las', options => MAP {'start': 10});

Optional Options parameter can be used to pass reader-specific options as key-value pairs.
For example, for the LAS/LAZ reader, the options are documented at https://pdal.io/en/stable/stages/readers.las.html#options

```

----
