InspectorCell
=============
InspectorCell provides an efficient workflow and graphical interface to generate high-quality training datasets from
highly multiplexed microscopy images.
InspectorCell is devloped to manually analyse large image stacks. It allows straight forward segmentation and annoation of
e.g. cells found in multiplexed microscopy images. 
It can be used as library, for direct embedding in Python 3 applications. It allready comes with such an implementation as
Orange3 Plug-In

Installation
------------
There are several ways to install InspectorCell. The easiest is to use InspectorCell as an Orange 3 Plug-In. You can also follow the
more detailed `install guide <https://inspectorcell.readthedocs.io/en/stable/install.html>`_

- Install `Orange3 <https://orange.biolab.si/>`_ using Conda. Currently Orange3 version >=3.16.0 and <=3.24.1 is needed.
  To install a certain version of Orange use :code:`conda install orange3=3.24.1`

- Get the current stable `inspectorcell-0.2.X-py3-none-any.whl` from the `releases <https://gitlab.com/InspectorCell/inspectorcell/-/releases>`_

- Start Orange3 (e.g. via :code:`python -m Orange.canvas`). In Orange3, open the `Add-Ons...` menu. Drag & drop the `*.whl` into the menu
  (alternatively run :code:`pip install inspectorcell-0.2.X-py3-none-any.whl`)

- Install Orange 3 ImageAnalytics in the Orange3 `Add-Ons...` or using conda `conda install Orange3-ImageAnalytics`

Documentation
-------------
You can find a full documentation at  `readthedocs <https://inspectorcell.readthedocs.io/en/stable/install.html>`

Dataset
-------
A small annotated dataset can be found at `Synapse <https://www.synapse.org/#!Synapse:syn21958516/files/>`

Preview
-------
.. figure:: https://inspectorcell.readthedocs.io/en/latest/_images/annotate3.png
   :figwidth: 100%
   :width: 80%
   :alt: Overview of the InspectorCell ViewContext
   :align: center

   InspectorCell provides a ViewContext, that displays multiple channels of multiplexed images simultaneously. Cells and their segmentation can be evaluated, edited, and annotated in a single workflow.

Prequisites
-----------
- Python 3.x (tested with Python 3.7 and Python 3.8)
- Numpy
- AnyQt (and preferably PyQt5 )
- OpenCV2 (python-openvc)
- sortedcontainers
- pyqtgraph

To use InspectorCell as application directly:
- Orange3 (Any version below <= 3.24.1 should work)
- Orange3-ImageAnalytics


Credits
-------
InspectorCell Version 0.2.0
^^^^^^^^^^^^^^^^^^^^^^^^^^^
| Copyright 2019-2020 (c) InspectorCell
| Developed by: Tatsiana Hofer and Andre Gosselink
| 
| Licensed under the Apache License, Version 2.0 (the "License");
| you may not use this file except in compliance with the License.
| You may obtain a copy of the License at
|
| `http://www.apache.org/licenses/LICENSE-2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_
|
| Unless required by applicable law or agreed to in writing, software
| distributed under the License is distributed on an "AS IS" BASIS,
| WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
| See the License for the specific language governing permissions and
| limitations under the License.

Icons
^^^^^
| Category.svg icon made by surang from https://flaticon.com, used under CC BY
| Mywidget.svg icon made by Freepik from https://flaticon.com, used under CC BY
| icons8*.png icons from https://icons8.com, used under CC BY-ND 3.0
| Other icons made by 2016 Bioinformatics Laboratory, University of Ljubljana from https://github.com/biolab/orange3, used under GPLv3.0
