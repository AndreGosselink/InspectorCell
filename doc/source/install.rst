Installation Guide
==================
The easises way to install InspectorCell is described in the :ref:`Quick Guide`.
Of course you can always install via commandline :ref:`How to get a commandline?`
.. 
.. .. code-block:: bash
.. 
..    $> pip install inspectorcell
.. 
To install from source you can clone our git repository and install via python

.. code-block:: bash

   $> git clone git@gitlab.com:InspectorCell/inspectorcell.git
   $> cd inspectorcell
   $> python setup.py install


Pitfalls
--------
Missing Libraries
^^^^^^^^^^^^^^^^^
The GUI elements in InspectorCell depend on the Qt Framework. If you get an
error like

.. code-block:: bash

   ImportError: Compiled libraries cannot be found.

the Qt libraries might be missing. We suggest to install `PyQt5`, but any Qt
library covered by `AnyQt` shoudl work

.. code-block:: bash

   $> pip install PyQt5

No Permission
^^^^^^^^^^^^^
Often the Python environment is installed with elevated privileges. This might
prevent installations due to lack of permission.

Try to got to a path, where you can create folders. There, open a command line

.. code-block:: bash

   $> python --version

It should be higher than version 3.6. If python is not found or the version is 
2.7, `get Python 3 first <https://www.python.org/downloads/>`. Now create a 
virtual environment. Let's say in ``c:\inspectorcell\`` on Windows or in
``~\.local\insepctocell`` on linux. Create the respective directory and then,
in the commandline. The follwowing steps are only for Windows.

.. code-block:: bash

   $> python -m venv c:\instpectorcell

To create the venv. This must be only done once. To install inspector cell now,
download the |LatestWheel| and then

.. code-block:: bash

   $> call c:\instpectorcell\Scripts\activate
   $> python -m install --upgrade pip
   $> pip install PyQt5
   $> pip install inspectorcell.whl

After installation, you can start Orange 3 with InspectorCell from everywhere
using the commandline and the following `starting commands`

.. code-block:: bash

   $> call c:\instpectorcell\Scripts\activate
   $> python -m Orange.canvas

If you write these lines into a bat file to automate the process. Create a new
file:

.. code-block:: bash

   $> echo > start_ic.bat

Right click on the new ``start_ic.bat`` file and select `Edit`. Now write the 
previous `starting commands` into the bat file. Save your changes, and now
you can start everything with a doubleclick!

How to get a commandline?
^^^^^^^^^^^^^^^^^^^^^^^^^
Got to the folder/directory where you want to use the commandline. In Windows 7 
and later, click into the address bar of the explorer. Type ``cmd`` and hit
enter. Windows cmd commandline will open.

On linux, just rightclick on into the window. Most distributions have an option
``Open Terminal here...``
