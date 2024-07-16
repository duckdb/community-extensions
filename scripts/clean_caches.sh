if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "Usage ./clean-caches.sh <bucket> <endpoint> <pattern>"
  exit 1
fi

BUCKET="$1"
ENDPOINT="$2"
PATTERN="$3"

CLOUDFRONT_DISTRIBUTION_ID=E2Z28NDMI4PVXP

### INVALIDATE THE CLOUDFRONT CACHE AND CLOUDFLARE
# For double checking we are invalidating the correct domain
# CLOUDFRONT_ORIGINS=`aws cloudfront get-distribution --id $CLOUDFRONT_DISTRIBUTION_ID --query 'Distribution.DistributionConfig.Origins.Items[*].DomainName' --output text`

ouput=$(aws s3 sync s3://$BUCKET . --exclude "*" --include "$PATTERN" --dryrun | awk ' { print $5 } ')

#if [ "$DUCKDB_CLEAN_CACHES_SCRIPT_MODE" == "for_real" ]; then
#  echo "CLOUDFRONT INVALIDATION"
#  while IFS= read -r path; do
#    aws cloudfront create-invalidation --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" --paths "$path"
#  done <<< $ouput
#else
  echo "INVALIDATION (DRY RUN)"
  echo "> Domain: $CLOUDFRONT_ORIGINS"
  echo "> Paths:"
  while IFS= read -r path; do
    echo "    $path"
  done <<< $ouput
#fi

echo ""

if [ ! -z "$CLOUDFLARE_CACHE_PURGE_TOKEN" ]; then
   if [ "$DUCKDB_CLEAN_CACHES_SCRIPT_MODE" == "for_real" ]; then
     echo "CLOUDFLARE INVALIDATION"
     while IFS= read -r path; do
       curl  --request POST --url https://api.cloudflare.com/client/v4/zones/84f631c38b77d4631b561207f2477332/purge_cache --header 'Content-Type: application/json' --header "Authorization: Bearer $CLOUDFLARE_CACHE_PURGE_TOKEN" --data "{\"files\": [\"http://$ENDPOINT.duckdb.org/$path\"]}"
       echo ""
     done
   else
     echo "CLOUDFLARE INVALIDATION (DRY RUN)"
     echo "> Paths:"
     while IFS= read -r path; do
       echo "    http://$ENDPOINT.duckdb.org/$path"
     done <<< $ouput
   fi
else
    echo "##########################################"
    echo "WARNING! CLOUDFLARE INVALIDATION DISABLED!"
    echo "##########################################"
fi
