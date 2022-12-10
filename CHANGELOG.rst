Changelog
=========

Version 0.3.2.rc1
-------------
* Small typos in documentation
* CI pipelines

Version 0.3.1
-------------
* Documentation

Version 0.3.0
-------------
* Separate miscmics package for easier processing of resulting file in external scripts
* Pinned versions
* Minor Bugfixes
* Install bash script icell

Version 0.2.5
-------------
* Uniform setter for scalar values to abstract implementation away
* Removed Orange Dropdowns from OrangeWidget. Kept throwing errors in different Orange3 versions
* Accept '\*.json' and '\*.ent' files

Version 0.2.4
-------------
* Better filters for loading dialogs
* Removed unused Inputs and Outputs from Orange3 Widget
* The tags 'C1' - 'C10' and 'done' now have a hardcoded effect on the coloring of segments
* The console script 'entitycli' is working now and allows for non-GUI entity manipulation
  and extraction of information into various formats
* Shortcut P to print the current channel only as a png file
* Shortcut Y to set the 'done' tag for the last active entity (like keys 0-9)
* entitycli can now draw segments by a color scheme
* The features extracted are now a functional mapping

Version 0.2.3
-------------
* EntityManager offers two iterations now: Active only or All
* EntityManager can pop entities, analogous to Dict.pop()
* Entities generated from Pixmap are dilated by one pixel upon loading to allow for easy merging

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
~~~~~~~~~~~
* Parallel display of multiple channels in a single grid layout view
* Background images can be set for each channel individually, e.g., with multiplexed microscopy images
* The view and mouse is synchronized to show the same image region in each channel
* On-the-fly contrast enhancement of each channel

Sessions
~~~~~~~~
* Multiple ViewContext layouts (channel layout, contrast enhancement) can be stored in a session
* Sessions can be persistently saved and loaded between usage

Entities
~~~~~~~~
* Polygon-based objects that can model e.g. cell segments
* Polygons can be edited/drawn
* Overlap of cells can be modeled
* Tags or scalar values can be assigned to Entities
* InfoBox shows annotations of the entity under the mouse cursor
* Entities can be hidden or shown
* Tag-dependent coloring possible (hardcoded ATM)
* All data can be stored in plain JSON
* Modal editing - switching between Normal - Draw - Erase

Orange3 Add-On
~~~~~~~~~~~~~~
* Integration into Orange3
* Load images using the Orange3-ImageAnalytics add-on

Misc
~~~~
* Utility script in `entitytool` to easily work with JSON data

Known Issues
~~~~~~~~~~~~
* Occasionally, the view can not be panned anymore using the middle mouse button in draw mode. Switching to select mode and back into draw mode reenables panning again
