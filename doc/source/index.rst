.. InspectorCell documentation master file, created by
   sphinx-quickstart on Tue Nov 19 13:04:55 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to InspectorCell's documentation!
=========================================
What is the main feature?
-------------------------
InspectorCell is an application for efficient manual analysis of
higly-multiplexed images. Primarly, it can be used to evaluate correctness of
unsupervised segmentation and annotation results. Moreover, it can be used to
generate training data for supervised segmentation and annotation. See how it
works in the :ref:`Quick Guide`

Why is this tool interesting for me?
------------------------------------
If you find yourself working with large image stacks, chances are you will also
find there little applications to efficently work with such kind of data.
However, such tools are needed if:

* You want to efficiently evaluate output from by unsupervised image analysis
* You want to generate high quality training datasets on highly-multiplexed
  image data
* You want to manually segment and annotate you image stack with respect to all 
  the important channels

If you feel addressed by that, look no further! We address all these issues in 
the :ref:`Quick Guide`!

.. toctree::
   :maxdepth: 1
   
   quick.rst
   controls.rst
   install.rst
   how2cite.rst
   apidoc.rst
   changelog.rst

.. Indices and tables
.. ==================
.. 
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

