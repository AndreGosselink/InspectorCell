Overview
========
Script transfering the filesystem datastructure of MICS/Tecan experiments into ome.tif format. Just implements infrastructure but not the final meta data structure. Aims to be as modular as possible, to allow for simple substitiute of metadata formats.

Structure
=========
The OMETiff class holds all shared information about the specimen, tissue,... found in each image. The images can be accessed via the ImageStack class, holding the image data with the metadata assosiated just with the image like fields, marker,... 

Dependencies
------------
- Python 3.x
- OpenCV2
