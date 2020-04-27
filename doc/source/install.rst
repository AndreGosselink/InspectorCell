Installation Guide
==================
The easises way to install InspectorCell is via conda, a package system
that not only manages Python, but also binary dependencies. It comes as
slim lightweight distribution `miniconda <https://docs.conda.io/en/latest/miniconda.html>`_
or as full distribution plattform `anaconda <https://www.anaconda.com/>`_


With conda install version 3.24.1 of orange

.. code-block:: bash

   $> conda install orange3=3.24.1

As recent changes in the are not yet reflected in InspectorCell.
A installation guide to Orange3 can be found `here <https://orange.biolab.si/download>`_

Download a `*.whl` from the InspectorCell `releases <https://gitlab.com/InspectorCell/inspectorcell/-/releases>`_
and install it using pip, whithin your conda environment.

.. code-block:: bash

   $> pip install inspectorcell-0.2.X-py3-none-any.whl

Alternatively, you can also install InspectorCell via drag and drop
using the Orange3 GUI. Orange3 can be run via `python -m Orange.canvas`


.. figure:: https://inspectorcell.readthedocs.io/en/latest/_images/addon.png
   :figwidth: 100%
   :width: 80%
   :alt: Install an Orange3 Add-On via drag&drop
   :align: center

Then install Orange3 ImageAnalytics using conda or by using the Orange3 Add-Ons menus

.. code-block:: bash

   $> conda install Orange3-ImageAnalytics


Pitfalls
--------
Missing Libraries
^^^^^^^^^^^^^^^^^
The GUI elements in InspectorCell depend on the Qt Framework. If you get an
error like

.. code-block:: bash

   ImportError: Compiled libraries cannot be found.

the Qt libraries might be missing. We suggest to install `PyQt5`, but any Qt
library covered by `AnyQt` should work. Using conda you do:

.. code-block:: bash

   $> conda install PyQt5

or similar via pip

.. code-block:: bash

   $> pip install PyQt5

No Permission with pip
^^^^^^^^^^^^^^^^^^^^^^
Sometimes the Python is installed with elevated privileges. This might
prevent installations due to lack of permission. To solve this:

- Use an virtual environment `venv <https://docs.python.org/3/library/venv.html>`_ 
- Install as user (`--user`) with `pip install  --user  inspectorcell-0.2.X-py3-none-any.whl`

How to get a commandline?
^^^^^^^^^^^^^^^^^^^^^^^^^
Got to the folder/directory where you want to use the commandline. In Windows 7 
and later, click into the address bar of the explorer. Type ``cmd`` and hit
enter. Windows cmd commandline will open.

On linux, just rightclick on into the window. Most distributions have an option
``Open Terminal here...``
