# DuckDB EEA Reference Grid Function Reference

## Function Index 
**[Scalar Functions](#scalar-functions)**

| Function | Summary |
| --- | --- |
| [`EEA_CoordXY2GridNum`](#eea_coordxy2gridnum) | Returns the EEA Reference Grid code to a given XY coordinate (EPSG:3035). |
| [`EEA_GridNum2CoordX`](#eea_gridnum2coordx) | Returns the X-coordinate (EPSG:3035) of the grid cell corresponding to a given EEA Reference Grid code. |
| [`EEA_GridNum2CoordY`](#eea_gridnum2coordy) | Returns the Y-coordinate (EPSG:3035) of the grid cell corresponding to a given EEA Reference Grid code. |
| [`EEA_GridNumAt100m`](#eea_gridnumat100m) | Returns the Grid code at 100 m resolution given an EEA reference Grid code. |
| [`EEA_GridNumAt10km`](#eea_gridnumat10km) | Returns the Grid code at 10 km resolution given an EEA reference Grid code. |
| [`EEA_GridNumAt1km`](#eea_gridnumat1km) | Returns the Grid code at 1 km resolution given an EEA reference Grid code. |

----

## Scalar Functions

### EEA_CoordXY2GridNum


#### Signature

```sql
BIGINT EEA_CoordXY2GridNum (col0 BIGINT, col1 BIGINT)
```

#### Description

Returns the EEA Reference Grid code to a given XY coordinate (EPSG:3035).

#### Example

```sql
SELECT CoordXY2GridNum(5078600, 2871400); -> 23090257455218688
```

----

### EEA_GridNum2CoordX


#### Signature

```sql
BIGINT EEA_GridNum2CoordX (col0 BIGINT)
```

#### Description

Returns the X-coordinate (EPSG:3035) of the grid cell corresponding to a given EEA Reference Grid code.

#### Example

```sql
SELECT EEA_GridNum2CoordX(23090257455218688); -> 5078600
```

----

### EEA_GridNum2CoordY


#### Signature

```sql
BIGINT EEA_GridNum2CoordY (col0 BIGINT)
```

#### Description

Returns the Y-coordinate (EPSG:3035) of the grid cell corresponding to a given EEA Reference Grid code.

#### Example

```sql
SELECT EEA_GridNum2CoordY(23090257455218688); -> 2871400
```

----

### EEA_GridNumAt100m


#### Signature

```sql
BIGINT EEA_GridNumAt100m (col0 BIGINT)
```

#### Description

Returns the Grid code at 100 m resolution given an EEA reference Grid code.

#### Example

```sql
SELECT EEA_GridNumAt100m(23090257455218688); -> 23090257455218688
```

----

### EEA_GridNumAt10km


#### Signature

```sql
BIGINT EEA_GridNumAt10km (col0 BIGINT)
```

#### Description

Returns the Grid code at 10 km resolution given an EEA reference Grid code.

#### Example

```sql
SELECT EEA_GridNumAt10km(23090257455218688); -> 23090255284404224
```

----

### EEA_GridNumAt1km


#### Signature

```sql
BIGINT EEA_GridNumAt1km (col0 BIGINT)
```

#### Description

Returns the Grid code at 1 km resolution given an EEA reference Grid code.

#### Example

```sql
SELECT EEA_GridNumAt1km(23090257455218688); -> 23090257448665088
```

----

