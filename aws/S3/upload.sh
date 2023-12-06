#!bin/bash

ENV=stg
aws s3 sync ./resources s3://line-slideshow-s3-$ENV/resources