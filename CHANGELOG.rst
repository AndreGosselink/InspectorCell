Changelog
=========
Version 0.2.3
-------------
* Pop functionality for EntityManager

Version 0.2.2
-------------
* Segmentation pixmaps can be loaded directly

Version 0.2.1
-------------
* Changed to Apache Licence

Version 0.2.0
-------------
* Initial release

ViewContext
^^^^^^^^^^^
* Parallel display of multiple channels in a single grid layout view
* Background images can be set for each channel individually, e.g. with multiplexed microscopy images
* The view and mouse is synchronize to show the same image region in each channel
* On-the-fly contrast enhancement of each channel

Sessions
^^^^^^^^
* Multiple ViewContext layouts (channel layout, contrast enhancement) can be stored in a session
* Sessions can be persitently saved and loaded between usage

Entities
^^^^^^^^
* Polygon based objects that can model e.g. cell segments
* Polygons can be edited/drawn
* Overlap of cells can be modeled
* Tags or scalar values can be assignted to Entities
* InfoBox shows annotations of entity under mouse cursor
* Entities can be hidden or shown
* Tag-dependen coloring possible (hardcoded ATM)
* All data can be stroed in plain JSON
* Modal editing - switching between Normal - Draw - Erase

Orange3 Add-On
^^^^^^^^^^^^^^
* Integration into Orange3
* Load images using the Orange3-ImageAnalytics add-on

Misc
^^^^
* Utility scipt in `entitytool` to easily work with JSON data

Known Issues
^^^^^^^^^^^^
* Occasionally the view can not be panned anymore using the middle mouse button in draw mode. Switching to select mode and back into draw mode reenabels panning again
