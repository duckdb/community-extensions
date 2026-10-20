### Compatibility Matrix

The {{ page.extension.name }} extension is available for the following platform and DuckDB version combinations. Note that DuckDB 2.0.0 was only released recently – migrating and building the community extensions may take some time.

| Platform             | 1.4.4 | 1.4.5 | 1.5.5 | 1.5.6 | 2.0.0 |
|----------------------|:-----:|:-----:|:-----:|:-----:|:-----:|
| Linux AMD64          |       |       |       |       |       |
| Linux ARM64          |       |       |       |       |       |
| macOS AMD64          |       |       |       |       |   -   |
| macOS ARM64          |       |       |       |       |       |
| Windows AMD64        |       |       |       |       |       |
| Windows ARM64        |       |       |       |       |       |

### Installing and Loading
```sql
INSTALL {{ page.extension.name }} FROM community;
LOAD {{ page.extension.name }};
```

{% if page.docs.hello_world %}
### Example
```sql
{{ page.docs.hello_world }}```
{% endif %}

{% if page.docs.extended_description %}
### About {{ page.extension.name }}
{{ page.docs.extended_description }}
{% endif %}
