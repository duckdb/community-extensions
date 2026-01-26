# AnnData Extension Function Reference

## Function Index

**[Table Functions](#table-functions)**

| Function | Summary |
| --- | --- |
| [`anndata_info`](#anndata_info) | Get metadata and structure information about an AnnData file. |
| [`anndata_scan_obs`](#anndata_scan_obs) | Scan observation (cell) metadata from an AnnData file. |
| [`anndata_scan_var`](#anndata_scan_var) | Scan variable (gene) metadata from an AnnData file. |
| [`anndata_scan_x`](#anndata_scan_x) | Scan the expression matrix from an AnnData file. |
| [`anndata_scan_obsm`](#anndata_scan_obsm) | Scan observation embeddings (e.g., PCA, UMAP) from an AnnData file. |
| [`anndata_scan_varm`](#anndata_scan_varm) | Scan variable embeddings from an AnnData file. |
| [`anndata_scan_layers`](#anndata_scan_layers) | Scan alternative expression matrices (layers) from an AnnData file. |
| [`anndata_scan_obsp`](#anndata_scan_obsp) | Scan observation pairwise matrices from an AnnData file. |
| [`anndata_scan_varp`](#anndata_scan_varp) | Scan variable pairwise matrices from an AnnData file. |

----

## Table Functions

### anndata_info

#### Signature

```sql
anndata_info (path VARCHAR)
```

#### Description

Returns metadata and structure information about an AnnData (.h5ad) file, including the number of observations, variables, available layers, embeddings, and other components.

#### Example

```sql
SELECT * FROM anndata_info('data.h5ad');

┌────────────┬─────────┐
│    key     │  value  │
│  varchar   │ varchar │
├────────────┼─────────┤
│ n_obs      │ 2700    │
│ n_vars     │ 32738   │
│ layers     │ raw     │
│ obsm       │ X_pca   │
│ obsm       │ X_umap  │
└────────────┴─────────┘
```

----

### anndata_scan_obs

#### Signature

```sql
anndata_scan_obs (path VARCHAR)
```

#### Description

Scans the observation (cell) metadata from an AnnData file. Returns all columns from the `obs` DataFrame including cell barcodes, cell types, and other annotations.

#### Example

```sql
SELECT * FROM anndata_scan_obs('data.h5ad') LIMIT 5;

┌──────────────────────┬───────────┬────────────────┐
│       _index         │ n_genes   │   cell_type    │
│       varchar        │   int64   │    varchar     │
├──────────────────────┼───────────┼────────────────┤
│ AAACATACAACCAC-1     │ 781       │ CD4 T cells    │
│ AAACATTGAGCTAC-1     │ 1352      │ B cells        │
│ AAACATTGATCAGC-1     │ 1131      │ CD4 T cells    │
│ AAACCGTGCTTCCG-1     │ 960       │ CD14 Monocytes │
│ AAACCGTGTATGCG-1     │ 522       │ NK cells       │
└──────────────────────┴───────────┴────────────────┘
```

----

### anndata_scan_var

#### Signature

```sql
anndata_scan_var (path VARCHAR)
```

#### Description

Scans the variable (gene) metadata from an AnnData file. Returns all columns from the `var` DataFrame including gene IDs, gene names, and other annotations.

#### Example

```sql
SELECT * FROM anndata_scan_var('data.h5ad') LIMIT 5;

┌─────────────────┬─────────────┬──────────────┐
│     _index      │  gene_name  │ n_cells      │
│     varchar     │   varchar   │    int64     │
├─────────────────┼─────────────┼──────────────┤
│ ENSG00000243485 │ MIR1302-2HG │ 3            │
│ ENSG00000186092 │ OR4F5       │ 1            │
│ ENSG00000238009 │ AL627309.1  │ 9            │
│ ENSG00000241860 │ AL627309.3  │ 36           │
│ ENSG00000187634 │ SAMD11      │ 45           │
└─────────────────┴─────────────┴──────────────┘
```

----

### anndata_scan_x

#### Signature

```sql
anndata_scan_x (path VARCHAR)
```

#### Description

Scans the main expression matrix (X) from an AnnData file. Returns the matrix with observation indices as rows and gene names as columns. Automatically handles both dense and sparse matrix formats.

#### Example

```sql
SELECT obs_idx, CD3D, CD19, CD14 FROM anndata_scan_x('data.h5ad') LIMIT 5;

┌─────────┬─────────┬─────────┬─────────┐
│ obs_idx │  CD3D   │  CD19   │  CD14   │
│  int64  │ double  │ double  │ double  │
├─────────┼─────────┼─────────┼─────────┤
│ 0       │ 2.5     │ 0.0     │ 0.0     │
│ 1       │ 0.0     │ 3.2     │ 0.0     │
│ 2       │ 1.8     │ 0.0     │ 0.0     │
│ 3       │ 0.0     │ 0.0     │ 4.1     │
│ 4       │ 0.0     │ 0.0     │ 0.0     │
└─────────┴─────────┴─────────┴─────────┘
```

----

### anndata_scan_obsm

#### Signature

```sql
anndata_scan_obsm (path VARCHAR, key VARCHAR)
```

#### Description

Scans observation embeddings (obsm) from an AnnData file. Common embeddings include PCA (`X_pca`), UMAP (`X_umap`), and t-SNE (`X_tsne`).

#### Example

```sql
SELECT * FROM anndata_scan_obsm('data.h5ad', 'X_umap') LIMIT 5;

┌─────────┬───────────────┬───────────────┐
│ obs_idx │    dim_0      │    dim_1      │
│  int64  │    double     │    double     │
├─────────┼───────────────┼───────────────┤
│ 0       │ 5.234         │ -2.156        │
│ 1       │ -8.123        │ 3.456         │
│ 2       │ 4.567         │ -1.234        │
│ 3       │ 12.345        │ 8.901         │
│ 4       │ -3.210        │ -7.654        │
└─────────┴───────────────┴───────────────┘
```

----

### anndata_scan_varm

#### Signature

```sql
anndata_scan_varm (path VARCHAR, key VARCHAR)
```

#### Description

Scans variable embeddings (varm) from an AnnData file. These are gene-level embeddings such as PCA loadings.

#### Example

```sql
SELECT * FROM anndata_scan_varm('data.h5ad', 'PCs') LIMIT 5;
```

----

### anndata_scan_layers

#### Signature

```sql
anndata_scan_layers (path VARCHAR, layer VARCHAR)
```

#### Description

Scans alternative expression matrices (layers) from an AnnData file. Common layers include raw counts, normalized data, or scaled data.

#### Example

```sql
SELECT * FROM anndata_scan_layers('data.h5ad', 'raw') LIMIT 5;
```

----

### anndata_scan_obsp

#### Signature

```sql
anndata_scan_obsp (path VARCHAR, key VARCHAR)
```

#### Description

Scans observation pairwise matrices (obsp) from an AnnData file. These typically contain cell-cell distance or connectivity matrices.

#### Example

```sql
SELECT * FROM anndata_scan_obsp('data.h5ad', 'distances') LIMIT 5;
```

----

### anndata_scan_varp

#### Signature

```sql
anndata_scan_varp (path VARCHAR, key VARCHAR)
```

#### Description

Scans variable pairwise matrices (varp) from an AnnData file. These contain gene-gene relationship matrices.

#### Example

```sql
SELECT * FROM anndata_scan_varp('data.h5ad', 'correlations') LIMIT 5;
```
