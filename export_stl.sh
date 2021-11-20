#!/bin/bash

for f in ./export/*.scad; do
    name="${f%.*}"
    output_name="${name}.stl"
    echo "Exporting $output_name"
    openscad -o $output_name $f
done
