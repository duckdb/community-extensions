# DuckDB STAC Extension Function Reference

## Function Index

**[Table Functions](#table-functions)**

| Function | Summary |
| --- | --- |
| [`STAC_Read`](#stac_read) | Reads the content of a STAC catalog from the given URL or JSON file and returns it as a table. |
| [`STAC_Search`](#stac_search) | Searches a STAC catalog based on the given criteria and returns matching items as a table. |

----

## Table Functions

### STAC_Read

#### Signature

```sql
STAC_Read (catalog VARCHAR)
```

#### Description

Reads the content of a SpatioTemporal Asset Catalog (STAC) catalog from the given URL or JSON file
and returns it as a table.

This function exposes a STAC catalog as a relational table, following the
[GeoParquet STAC specification](https://radiantearth.github.io/stac-geoparquet-spec/latest/).

Each row represents a single STAC item. Almost all item fields are mapped to columns;
nested JSON structures are preserved as Parquet structs where possible, but item properties
are promoted to the top level for easier filtering and querying.

#### Example

```sql
SELECT * FROM STAC_Read('https://example.com/stac/collection.json');
```

----

### STAC_Search

#### Signature

```sql
STAC_Search (url VARCHAR,
            [collections VARCHAR[]],
            [ids VARCHAR[]],
            [bbox FLOAT[4]],
            [intersects GEOMETRY('EPSG:4326')],
            [datetime VARCHAR],
            [max_items INTEGER]
            )
```

#### Description

Searches the content of a SpatioTemporal Asset Catalog (STAC) catalog based on the given STAC API - Item Search
filtering criteria (https://api.stacspec.org/v1.0.0/item-search/) and returns matching items as a table.

The `url` parameter specifies the base URL of the STAC API - Item Search endpoint to query.
The optional parameters allow filtering by different criteria:

* `collections`: A list of collection IDs to filter the search results.
* `ids`: A list of item IDs to filter the search results.
* `bbox`: A bounding box to filter items by spatial intersection, specified as an array of four floats representing the minimum longitude, minimum latitude, maximum longitude, and maximum latitude.
* `intersects`: A geometry object (EPSG:4326) to filter items by spatial intersection.
* `datetime`: A string representing a temporal range to filter the search results, specified in the format "start_datetime/end_datetime" (e.g., "2021-01-01T00:00:00Z/2021-12-31T23:59:59Z").
* `max_items`: An integer specifying the maximum number of items to return in each result page.

This function exposes a STAC catalog as a relational table, following the
[GeoParquet STAC specification](https://radiantearth.github.io/stac-geoparquet-spec/latest/).

Each row represents a single STAC item. Almost all item fields are mapped to columns;
nested JSON structures are preserved as Parquet structs where possible, but item properties
are promoted to the top level for easier filtering and querying.

#### Example

```sql
SELECT
    *
FROM
    STAC_Search(
        'https://earth-search.aws.element84.com/v0/search',
        collections := ['sentinel-s2-l2a-cogs'],
        datetime := '2021-09-30/2021-10-30',
        intersects := ST_MakeEnvelope(-1.695007724869786, 42.788757186108654, -1.604482013650674, 42.84244150196227)::GEOMETRY('EPSG::4326')
    )
;
```

----
