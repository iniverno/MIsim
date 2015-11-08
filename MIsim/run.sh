#!/bin/bash

if [ "$#" -ne 2 ]; then
  echo "usage: run.sh <net> <layer>"
  exit
fi

source /localhome/juddpatr/caffe_rc

time python testSystem.py $1 $2

#.skel/postprocess.sh
