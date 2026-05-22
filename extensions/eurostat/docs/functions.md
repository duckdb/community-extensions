# DuckDB EUROSTAT Extension Function Reference

## Function Index
**[Scalar Functions](#scalar-functions)**

| Function | Summary |
| --- | --- |
| [`EUROSTAT_GetGeoLevelFromGeoCode`](#eurostat_getgeolevelfromgeocode) | Returns the level for a GEO code in the NUTS classification or if it is considered aggregates. |

**[Table Functions](#table-functions)**

| Function | Summary |
| --- | --- |
| [`EUROSTAT_Dataflows`](#eurostat_dataflows) | Returns info of the dataflows provided by EUROSTAT Providers. |
| [`EUROSTAT_Endpoints`](#eurostat_endpoints) | Returns the list of supported EUROSTAT API Endpoints. |
| [`EUROSTAT_DataStructure`](#eurostat_datastructure) | Returns information of the data structure of an EUROSTAT Dataflow. |
| [`EUROSTAT_Read`](#eurostat_read) | Returns the dataset of an EUROSTAT Dataflow. |

----

## Scalar Functions

### EUROSTAT_GetGeoLevelFromGeoCode


#### Signature

```sql
VARCHAR EUROSTAT_GetGeoLevelFromGeoCode (geo_code VARCHAR)
```

#### Description


Returns the level for a GEO code in the NUTS classification or if it is considered aggregates.

This scalar function is used by the `EUROSTAT_Read` function to add the `geo_level`
dimension as a normal column.

The supported levels are:
- aggregate
- country
- nuts1
- nuts2
- nuts3
- city

See more details about `geo_level` [here](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/api#APIGettingstartedwithstatisticsAPI-FilteringongeoLevel).

#### Example

```sql
SELECT EUROSTAT_GetGeoLevelFromGeoCode('DE');        -- returns 'country'
SELECT EUROSTAT_GetGeoLevelFromGeoCode('DE1');       -- returns 'nuts1'
SELECT EUROSTAT_GetGeoLevelFromGeoCode('DE12');      -- returns 'nuts2'
SELECT EUROSTAT_GetGeoLevelFromGeoCode('DE123');     -- returns 'nuts3'
SELECT EUROSTAT_GetGeoLevelFromGeoCode('DE_DEL1');   -- returns 'city'
SELECT EUROSTAT_GetGeoLevelFromGeoCode('EU27_2020'); -- returns 'aggregate'
```

----

## Table Functions

### EUROSTAT_Dataflows

#### Signature

```sql
EUROSTAT_Dataflows (providers VARCHAR[] = [], dataflows VARCHAR[] = [], language VARCHAR = 'en')
```

#### Description


Returns info of the dataflows provided by EUROSTAT Providers.


#### Example

```sql
SELECT * FROM EUROSTAT_Dataflows();
SELECT * FROM EUROSTAT_Dataflows(providers = ['ESTAT','ECFIN'], language := 'en');

--- You can also filter by specific datasets:

SELECT
	provider_id,
	dataflow_id,
	class,
	version,
	label
FROM
	EUROSTAT_Dataflows(providers = ['ESTAT'], dataflows = ['DEMO_R_D2JAN'], language := 'de')
;

┌─────────────┬──────────────┬─────────┬─────────┬───────────────────────────────────────────────────────────────────┐
│ provider_id │  dataflow_id │  class  │ version │                               label                               │
│   varchar   │   varchar    │ varchar │ varchar │                              varchar                              │
├─────────────┼──────────────┼─────────┼─────────┼───────────────────────────────────────────────────────────────────┤
│ ESTAT       │ DEMO_R_D2JAN │ dataset │ 1.0     │ Bevölkerung am 1. Januar nach Alter, Geschlecht und NUTS-2-Region │
└─────────────┴──────────────┴─────────┴─────────┴───────────────────────────────────────────────────────────────────┘

```

----

### EUROSTAT_Endpoints

#### Signature

```sql
EUROSTAT_Endpoints ()
```

#### Description


Returns the list of supported EUROSTAT API Endpoints.


#### Example

```sql
SELECT provider_id, organization, description FROM EUROSTAT_Endpoints();

┌─────────────┬──────────────┬──────────────────────────────────────────────────────┐
│ provider_id │ organization │                     description                      │
│   varchar   │   varchar    │                       varchar                        │
├─────────────┼──────────────┼──────────────────────────────────────────────────────┤
│ ECFIN       │ DG ECFIN     │ Economic and Financial Affairs                       │
│ EMPL        │ DG EMPL      │ Employment, Social Affairs and Inclusion             │
│ ESTAT       │ EUROSTAT     │ EUROSTAT database                                    │
│ GROW        │ DG GROW      │ Internal Market, Industry, Entrepreneurship and SMEs │
│ TAXUD       │ DG TAXUD     │ Taxation and Customs Union                           │
└─────────────┴──────────────┴──────────────────────────────────────────────────────┘
```

----

### EUROSTAT_DataStructure

#### Signature

```sql
EUROSTAT_DataStructure (provider VARCHAR, dataflow VARCHAR, language VARCHAR = 'en')
```

#### Description


Returns information of the data structure of an EUROSTAT Dataflow.


#### Example

```sql
SELECT
	provider_id,
	dataflow_id,
	position,
	dimension,
	concept
FROM
	EUROSTAT_DataStructure('ESTAT', 'DEMO_R_D2JAN', language := 'en')
;

┌─────────────┬──────────────┬──────────┬─────────────┬─────────────────────────────────┐
│ provider_id │ dataflow_id  │ position │  dimension  │             concept             │
│   varchar   │   varchar    │  int32   │   varchar   │             varchar             │
├─────────────┼──────────────┼──────────┼─────────────┼─────────────────────────────────┤
│ ESTAT       │ DEMO_R_D2JAN │        1 │ freq        │ Time frequency                  │
│ ESTAT       │ DEMO_R_D2JAN │        2 │ unit        │ Unit of measure                 │
│ ESTAT       │ DEMO_R_D2JAN │        3 │ sex         │ Sex                             │
│ ESTAT       │ DEMO_R_D2JAN │        4 │ age         │ Age class                       │
│ ESTAT       │ DEMO_R_D2JAN │        5 │ geo         │ Geopolitical entity (reporting) │
│ ESTAT       │ DEMO_R_D2JAN │       -1 │ geo_level   │ NUTS classification level       │
│ ESTAT       │ DEMO_R_D2JAN │        6 │ time_period │ Time                            │
└─────────────┴──────────────┴──────────┴─────────────┴─────────────────────────────────┘
```

`geo_level` is a dimension that is not part of the dataflow source, but it is computed based
on the `geo` dimension values. See the function [EUROSTAT_GetGeoLevelFromGeoCode](#eurostat_getgeolevelfromgeocode) below for
more details.

----

### EUROSTAT_Read

#### Signature

```sql
EUROSTAT_Read (provider VARCHAR, dataflow VARCHAR)
```

#### Description


Returns the dataset of an EUROSTAT Dataflow.


#### Example

```sql
SELECT * FROM EUROSTAT_Read('ESTAT', 'DEMO_R_D2JAN') LIMIT 5;

┌─────────┬─────────┬─────────┬─────────┬─────────┬───────────┬─────────────┬───────────────────┐
│  freq   │  unit   │   sex   │   age   │   geo   │ geo_level │ TIME_PERIOD │ observation_value │
│ varchar │ varchar │ varchar │ varchar │ varchar │  varchar  │   varchar   │      double       │
├─────────┼─────────┼─────────┼─────────┼─────────┼───────────┼─────────────┼───────────────────┤
│ A       │ NR      │ F       │ TOTAL   │ AL      │ country   │ 2000        │         1526762.0 │
│ A       │ NR      │ F       │ TOTAL   │ AL      │ country   │ 2001        │         1535822.0 │
│ A       │ NR      │ F       │ TOTAL   │ AL      │ country   │ 2002        │         1532563.0 │
│ A       │ NR      │ F       │ TOTAL   │ AL      │ country   │ 2003        │         1526180.0 │
│ A       │ NR      │ F       │ TOTAL   │ AL      │ country   │ 2004        │         1520481.0 │
└─────────┴─────────┴─────────┴─────────┴─────────┴───────────┴─────────────┴───────────────────┘
```

----
