Version 0.1.0
-------------
Somewhat working version. One might use this version productively, given that one is
faithfull. With a bit of luck, one can produce results

Features
^^^^^^^^
- Show Items/Entities/Cells in a synced view
- Merge entities
- Edit/draw entities
- Create entities
- Set backgroundimages
- Creat entities from contour data input
- Save entities to contour data tabel
- Load images using the Orange3-ImageAnalytics add-on

Bugs
^^^^
No real bugtesting, there are alot

Version 0.0.0
-------------
General project layout and implementation of classes. No functionality yet. This
repository can be seen as a repository for a python meta package. The core functionality
of the app is implemented in ./src/cellinspector. This module will be installed globally.
Additionally namespace modules are installed, to make the cellinspector avaible as addon.
An already implemented addon is ./src/orangecontrib, which wrappes the ./src/cellinspector
into an Orange3 addon

- Project directory layout
- Working setup.py to deploy in orange namespace
