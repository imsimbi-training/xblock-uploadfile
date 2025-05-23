aws s3 sync --profile imsimbi-cf --cache-control 'max-age=604800' assets/ s3://imsimbi-documents-public/xblock-table/ --acl public-read
