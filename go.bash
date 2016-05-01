#!/bin/bash
set -e
set -u
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p ${DIR}/logs

python ${DIR}/product_listing.py -p products.txt -l listings.txt > result_go

result_file=`cat result_go`

result_output=`curl -XPOST -F file=@${result_file} https://challenge-check.sortable.com/validate`
echo $result_output
