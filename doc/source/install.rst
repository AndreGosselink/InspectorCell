Installation Guide
==================
The easises way to install InspectorCell is via conda, a package system
that not only manages Python, but also binary dependencies. It comes as
slim lightweight distribution `miniconda <https://docs.conda.io/en/latest/miniconda.html>`_
or as full distribution plattform `anaconda <https://www.anaconda.com/>`_

Automated icell script
----------------------
For your convenience, there is an automated installation script, which creates
a local virtual environment to install InspectorCell with Orange3 and all dependencies

.. code-block:: bash
    $> ./icell -h
    Basic usage: icell -i {conda,mamba,venv}
                 icell -c <cmd>
                 icell -[hrv]
    Options:
         h                 This help           
         i <variant>       Install into '/mnt/storage/phd/src/inspectorcell/icell_venv' using <env> = 'conda', 'mamba' or 'venv'
         r                 remove installed environment, if exists
         c <cmd>           Activate environment and run <cmd> 
         d                 Build and open the HTML documentation
         v                 Print version strings and exit

By hand
-------
With conda after installtion into a local environment

.. code-block:: bash

   $> conda env create -p icell_venv -f condaenv.yml

Now you can install InspectorCell via drag and drop as described in the :ref:`Quick Guide`
Alternatively, you can now install InspectorCell and its dependencies via 

.. code-block:: bash

   $> pip install . --force-reinstall --no-deps

To start inspectorcell you can either use the icell script

.. code-block:: bash

   $> ./icell

Or activate the conda environment and start Oragne3 by hand

.. code-block:: bash

   $> conda activate icell_venv
   $> python -m Orange.canvas

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
