#!/usr/bin/env bash

set -eo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: ./scripts/generate_md.sh build/release/duckdb"
    exit 1
fi

curl -s https://community-extensions.duckdb.org/downloads-last-week.json -o build/downloads-last-week.json

platform=$($1 -csv -c "PRAGMA platform" | tail -n1)
version_raw=$($1 -csv -c "PRAGMA version" | tail -n1)
version=$(echo "$version_raw-,$version_raw" | cut -d '-' -f 2 | cut -d ',' -f 2)

DOCS=build/docs

rm -rf $DOCS
mkdir -p $DOCS

EXTENSIONS_CSV=$DOCS/community_extensions.csv
echo "name,repo,ref,description" > $EXTENSIONS_CSV
for extension_file in build/extension_dir/$version/$platform/*.duckdb_extension;
do
    extension_full=$(basename -- $extension_file)
    extension="${extension_full%%.*}"
    echo "Generating docs for $extension"
    EXTENSION_SCREENSHOT=$DOCS/../screenshot/$extension.md
    EXTENSION_README=$DOCS/$extension.md
    things="extensions functions settings types"
    rm -f pre.db
    rm -f post.db
    for thing in $things; do
        $1 -unsigned pre.db -c "SET extension_directory = 'build/extensions'; CREATE OR REPLACE TABLE $thing AS FROM duckdb_$thing();"
        rm -rf temp
        $1 -unsigned post.db -c "SET extension_directory = 'build/extensions'; FORCE INSTALL $extension FROM 'build/extension_dir'; LOAD $extension; CREATE OR REPLACE TABLE $thing AS FROM duckdb_$thing();"
        rm -rf temp
    done

    mkdir -p $DOCS/$extension
    mkdir -p $DOCS/../screenshot
    
    $1 post.db -c "ATTACH 'pre.db'; CREATE OR REPLACE TABLE fun_no_overload AS SELECT function_name, function_type, split_part(description, chr(10), 1) as description, comment, examples FROM (FROM (SELECT function_name, function_type, description, comment, examples FROM functions ORDER BY function_name, function_type) EXCEPT (SELECT function_name, function_type, description, comment, examples FROM pre.functions ORDER BY function_name, function_type)) GROUP BY ALL ORDER BY function_name, function_type;"
    $1 post.db -c "ATTACH 'pre.db'; CREATE OR REPLACE TABLE fun_with_overload AS SELECT function_name, function_type, split_part(description, chr(10), 1) as description, comment, examples FROM (FROM ( SELECT count(*), function_name, function_type, description, comment, examples FROM functions GROUP BY ALL ORDER BY function_name, function_type) EXCEPT (SELECT count(*), function_name, function_type, description, comment, examples FROM pre.functions GROUP BY ALL ORDER BY function_name, function_type)) GROUP BY ALL ORDER BY function_name, function_type;"
    $1 $DOCS/$extension.db -c "ATTACH 'post.db'; CREATE OR REPLACE TABLE functions AS FROM post.fun_no_overload GROUP BY ALL ORDER BY function_name, function_type;"
    $1 $DOCS/$extension.db -c "ATTACH 'post.db'; CREATE OR REPLACE TABLE functions_overloads AS FROM post.fun_with_overload EXCEPT FROM post.fun_no_overload GROUP BY ALL ORDER BY function_name, function_type;"
    $1 $DOCS/$extension.db -c "ATTACH 'pre.db'; ATTACH 'post.db'; CREATE OR REPLACE TABLE new_settings AS FROM ( SELECT * EXCLUDE (value) FROM post.settings ORDER BY name) EXCEPT (SELECT * EXCLUDE (value) FROM pre.settings ORDER BY name) ORDER BY name;"
    $1 $DOCS/$extension.db -c "ATTACH 'pre.db'; ATTACH 'post.db'; CREATE OR REPLACE TABLE description AS FROM ( SELECT * EXCLUDE (install_path, loaded, installed) FROM post.extensions ORDER BY extension_name) EXCEPT (SELECT * EXCLUDE (install_path, loaded, installed) FROM pre.extensions ORDER BY extension_name) ORDER BY extension_name;"
    $1 $DOCS/$extension.db -c "ATTACH 'pre.db'; ATTACH 'post.db'; CREATE OR REPLACE TABLE types AS FROM ( SELECT type_name, type_size, logical_type, type_category, internal FROM post.types ORDER BY ALL) EXCEPT (SELECT type_name, type_size, logical_type, type_category, internal FROM pre.types ORDER BY ALL) ORDER BY type_name;"

    if [ -s "extensions/$extension/docs/function_descriptions.csv" ]; then
       cp extensions/$extension/docs/function_descriptions.csv $DOCS/functions.csv
       $1 $DOCS/$extension.db -c "CREATE TABLE tmp AS SELECT function_name, function_type, other.description as description, other.comment as comment, [other.example] as examples FROM functions LEFT JOIN read_csv('$DOCS/functions.csv') AS other ON function_name == other.function; DROP TABLE functions; CREATE TABLE functions AS FROM tmp; DROP TABLE tmp;"
       $1 $DOCS/$extension.db -c "CREATE TABLE tmp AS SELECT function_name, function_type, other.description as description, other.comment as comment, [other.example] as examples FROM functions_overloads LEFT JOIN read_csv('$DOCS/functions.csv') AS other ON function_name == other.function; DROP TABLE functions_overloads; CREATE TABLE functions_overloads AS FROM tmp; DROP TABLE tmp;"
       rm $DOCS/functions.csv
    fi

    $1 $DOCS/$extension.db -markdown -c "FROM new_settings;" > $DOCS/$extension/settings.md
    $1 $DOCS/$extension.db -markdown -c "FROM functions;" > $DOCS/$extension/functions.md
    $1 $DOCS/$extension.db -markdown -c "FROM functions_overloads;" > $DOCS/$extension/functions_overloads.md
    $1 $DOCS/$extension.db -markdown -c "FROM description;" > $DOCS/$extension/extension.md
    $1 $DOCS/$extension.db -markdown -c "FROM types;" > $DOCS/$extension/types.md

    rm -f pre.db
    rm -f post.db

    echo "---" > $EXTENSION_README
    echo "warning: DO NOT CHANGE THIS MANUALLY, THIS IS GENERATED BY https://github/duckdb/community-extensions repository, check README there" >> $EXTENSION_README
    echo "title: $extension" >> $EXTENSION_README
    echo "excerpt: |" >> $EXTENSION_README
    echo "  DuckDB Community Extensions" >> $EXTENSION_README
    if [ -s "extensions/$extension/description.yml" ]; then
       echo -n "  " >> $EXTENSION_README
       cat extensions/$extension/description.yml | yq -r ".extension.description" >> $EXTENSION_README
       cat extensions/$extension/description.yml | yq '.extension.name, .repo.github, .repo.ref' | xargs printf '%s,%s,%s,"' >> $EXTENSIONS_CSV
       cat extensions/$extension/description.yml | yq -r '.extension.description' | sed 's/$/"/'  >> $EXTENSIONS_CSV
       echo "" >> $EXTENSION_README
       cat extensions/$extension/description.yml >> $EXTENSION_README
       echo "" >> $EXTENSION_README

       STAR_COUNT=$(python3 scripts/get_stars.py extensions/$extension/description.yml $1)
       STAR_COUNT_PRETTY=$(echo $STAR_COUNT | python3 scripts/pretty_print.py)
       echo "extension_star_count: $STAR_COUNT" >> $EXTENSION_README
       echo "extension_star_count_pretty: $STAR_COUNT_PRETTY" >> $EXTENSION_README

       DOWNLOAD_COUNT=$(cat build/downloads-last-week.json | jq ".${extension}")
       DOWNLOAD_COUNT_PRETTY=$(echo $DOWNLOAD_COUNT | python3 scripts/pretty_print.py)
       echo "extension_download_count: $DOWNLOAD_COUNT" >> $EXTENSION_README
       echo "extension_download_count_pretty: $DOWNLOAD_COUNT_PRETTY" >> $EXTENSION_README
    fi
    echo "image: '/images/community_extensions/social_preview/preview_community_extension_"$extension".png'" >> $EXTENSION_README
    cat $EXTENSION_README > $EXTENSION_SCREENSHOT
    echo "layout: community_extension_sql_screenshot" >> $EXTENSION_SCREENSHOT
    echo "---" >> $EXTENSION_SCREENSHOT
    cat layout/screenshot.md >> $EXTENSION_SCREENSHOT


    echo "layout: community_extension_doc" >> $EXTENSION_README
    echo "---" >> $EXTENSION_README

    cat layout/default.md >> $EXTENSION_README

    if [ -s "$DOCS/$extension/functions.md" ]; then
       echo "### Added Functions" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       echo "<div class=\"extension_functions_table\"></div>" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       cat $DOCS/$extension/functions.md >> $EXTENSION_README
       echo "" >> $EXTENSION_README
    fi
    if [ -s "$DOCS/$extension/functions_overloads.md" ]; then
       echo "### Overloaded Functions" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       echo "<div class=\"extension_functions_table\"></div>" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       cat $DOCS/$extension/functions_overloads.md >> $EXTENSION_README
       echo "" >> $EXTENSION_README
    fi
    if [ -s "$DOCS/$extension/types.md" ]; then
       echo "### Added Types" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       echo "<div class=\"extension_types_table\"></div>" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       cat $DOCS/$extension/types.md >> $EXTENSION_README
       echo "" >> $EXTENSION_README
    fi
    if [ -s "$DOCS/$extension/settings.md" ]; then
       echo "### Added Settings" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       echo "<div class=\"extension_settings_table\"></div>" >> $EXTENSION_README
       echo "" >> $EXTENSION_README
       cat $DOCS/$extension/settings.md >> $EXTENSION_README
       echo "" >> $EXTENSION_README
    fi
    echo "" >> $EXTENSION_README

    rm -rf $DOCS/$extension
    rm -rf $DOCS/$extension.db
done

rm -f x.db
$1 $DOCS/x.db -markdown -c "SELECT '['||#1||']({% link community_extensions/extensions/'||#1||'.md %})' as Name, '[<span class=github>GitHub</span>](https://github.com/'||#2||')' as GitHub , #4 as Description FROM read_csv('build/docs/community_extensions.csv');" > $DOCS/extensions_list.md.tmp
rm -f x.db
