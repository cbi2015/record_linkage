#!/bin/bash
set -e
set -u

mkdir -p logs

python product_listing.py -p products.txt -l listings.txt > go_result

result_file=`cat go_result`

result_output=`curl -XPOST -F file=@${result_file} https://challenge-check.sortable.com/validate`
echo $result_output
