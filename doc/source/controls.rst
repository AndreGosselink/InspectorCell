Controls
========
To faciliate a fast and interruption free work flow, InspectorCell promotes the 
use of keyboard shortcuts and modes.

You can switch into different modes using the `Object editing` section in the
gui or the respective keys.

Key Reference
-------------
Modes
^^^^^
* ``n`` Switch to normal mode
* ``d`` Switch to draw mode
* ``e`` Switch to erase mode

* ``+`` Increas brush size in draw/erase mode
* ``-`` Decrease brush size in draw/erase mode

View Context
^^^^^^^^^^^^
A ViewContext has all the information about the Channel layout, the images
name loaded, the enhancments applied to the images, the visibility of the
segments, and the opacity of the segments

* ``Alt`` + ``1`` Switch to ViewContext 1 (It can be any number between 0 and 9)
* ``Alt`` + ``s`` Save all the current ViewContext layouts into `session.json`
* ``Alt`` + ``l`` Load ViewContext into a session.json

Entity Manipulation
^^^^^^^^^^^^^^^^^^^
* ``k`` Entities under the mouse scalar value, with the image name is increased
* ``l`` Entities under mouse scalar value, with the image name is decreased
* ``1`` Entity under mouse gets assigned the tag with the number one in the
  taglist

* ``m`` All selected Entities get merged into a single one. Tags and scalars
  are merged, too
* ``r`` Selected Entities are removed from the scene (marked as `historical`)

* ``v`` Selected Entities are hidden
* ``s`` All hidden Entities are shown

Mouse Reference
---------------

.. figure:: /_static/img/mouse.png
   :figwidth: 100%
   :width: 80%
   :alt: Mouse buttons
   :align: center


+------------+---------------+----------------+--------------+
|Mouse Button| Normal mode   | Draw mode      | Erase mode   |
+============+===============+================+==============+
| Left       |Select Segment | Extend Segment | Erase Segment|
+------------+---------------+----------------+--------------+
| Middle     |Pan            | Pan            | Pan          |
+------------+---------------+----------------+--------------+
| Right      |Context        | Context        | Context      |
+------------+---------------+----------------+--------------+
