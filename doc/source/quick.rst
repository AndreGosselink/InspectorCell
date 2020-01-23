Quick Guide
===========
Install as Orange 3 Add-On
--------------------------
The fastest way to get started is by downloading the wheel and add it to your
existing Orange 3 installation. Orange 3 is a Data Mining and Analysis application,
that aims to provide easy and intiutive access to advanced analysis algorithms.
For a more detailed version please refer to the :ref:`Installation Guide`


Install
-------
.. figure:: /_static/img/addon.png
   :figwidth: 100%
   :width: 80%
   :alt: Install InspectorCell as Orange 3 Add-On
   :align: center

* If you haven't Orange 3, you can find it on their `Orange 3 page <https://orange.biolab.si/download/>`_
* Download the latest Wheel: |LatestWheel|
* Open the Orange 3 `Options->Add-Ons` menu
* Drag & Drop the wheel into the list

Load Images
-----------
.. figure:: /_static/img/workflow.png
   :figwidth: 100%
   :width: 80%
   :alt: Simple InspectorCell workflow
   :align: center

To load images you can use the ImageAnalytics Node. Connect it to the
`Images` input of the InspectorCell node. Now with a doubleclick on
the inspector cell node you can start editing your images

With the button `Set Layout`, you can configure, how many channels are shown.
For this example, we stick with the 4x4 layout

Within any channel, click with the right mouse button to load an backgound
image. Here, we select an mock image. The yellow frame around the channel
always shows, which channel is the active one.

With `Enhance BG` you can change the contrast of the displayed image.

Basic Annotation
----------------
.. figure:: /_static/img/annotate1.png
   :figwidth: 100%
   :width: 80%
   :alt: 
   :align: center

With the mouse wheel you can zoom in and out. Clicking the mouse wheel /
middle mouse button allows you to pan. Pressing ``d`` switches to the draw mode.
Alternative, you can click on the pencile in the left sidebar under
`Object editing` Please see :ref:`Controls` for a comprehnsive overview.
 

.. figure:: /_static/img/annotate2.png
   :figwidth: 100%
   :width: 80%
   :alt: 
   :align: center

   ..

.. figure:: /_static/img/annotate3.png
   :figwidth: 100%
   :width: 80%
   :alt: 
   :align: center

   ..