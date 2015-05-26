========================
Azure Batch Maya Sample
========================

Microsoft Azure Batch Apps is an Azure service offering on-demand capacity for compute-intensive workloads.
This sample uses the Azure Batch Apps SDK and the Azure Batch Apps Python client to show how 
one could set up a cloud-based rendering platform using Maya.

The sample involves two parts, the cloud assembly project, and the Maya client project for job submission.
For more information on Batch Apps concepts, terms, and project structure `check out this article <http://azure.microsoft.com/en-us/documentation/articles/batch-dotnet-get-started/#tutorial2>`_.

The client project is a Python plug-in for Maya, to allow for a seamless user experience for submitting render
jobs to the cloud from within Maya.

The compiled components can be downloaded in the release.


License
========

This project is licensed under the MIT License.
For details see LICENSE.txt or visit `opensource.org/licenses/MIT <http://opensource.org/licenses/MIT>`_.


Set up
======

In order to build the projects you will need to have the following tools:

- `Visual Studio <http://www.visualstudio.com/>`_
- `Microsoft Azure Batch Apps Cloud SDK <http://www.nuget.org/packages/Microsoft.Azure.Batch.Apps.Cloud/>`_
- `Python Tools for Visual Studio <http://pytools.codeplex.com/>`_
- `Azure Batch Apps Python Client and it's required packages <https://github.com/Azure/azure-batch-apps-python>`_


Part 1. Maya.Cloud
======================

This project builds a cloud assembly for running rendering jobs using Maya.  
A "cloud assembly" is a zip file containing an application-specific DLL with logic for splitting
jobs into tasks, and for executing each of those tasks.  In this sample, we split the job into
a task for each frame to be rendered, and execute each task by running Maya's render.exe application. 
The cloud assembly goes hand in hand with an "application image", a zip file 
containing the program or programs to be executed.  In this sample, we have used Maya and 
ImageMagick in the application image.
 

Building the Cloud Assembly
---------------------------

To build the cloud assembly zip file:

1. Build the Maya.Cloud project.
2. Open the output folder of the Maya.Cloud project.
3. Select all the DLLs (and optionally PDB files) in the output folder.
4. Right-click and choose Send To > Compressed Folder.


Building the Application Image
-------------------------------

The application image contains the following applications:

- `Maya <http://www.autodesk.com/products/maya>`_. The application we want to cloud-enable. To run Maya on the cloud we will need
  to include a number of additional components that are installed during the Maya setup process.
- `ImageMagick <http://www.imagemagick.org/script/binary-releases.php#windows>`_. (Optional) Tool for creating preview thumbnails 
  of the rendered frames. Locate the portable Win32 static build.

To build the application image zip file, read the included document `<MayaApplicationImageSetup.pdf>`_.

The final application image zip file should have the following structure::

	Maya.zip
	|
	| -- AdLM
	|    |
	|    | -- ASR
	|    | -- R9
	|    | -- other AdLM components
	|
	| -- Common Files
	|    |
	|    | -- Autodesk Shared
	|
	| -- ImageMagick
	|    |
	|    | -- convert.exe
	|    | -- other ImageMagick components
	|
	| -- Maya2015
	|    |
	|    | -- bin
	|    | -- other Maya components
	|
	| -- mentalrayForMaya2015
	|    |
	|    | -- bin
	|    | -- other MentalRay components



Uploading the Application to Your Batch Apps Service
-----------------------------------------------------

1. Open the Azure management portal (manage.windowsazure.com).
2. Select Batch Services in the left-hand menu.
3. Select your account in the list and click "Manage Batch Apps" to open the Batch Apps management 
   portal. Your Batch Apps Service should be displayed, or you can navigate to it using the Services left-hand menu option.
4. Choose the Manage Applications tab.
5. Click New Application.
6. Under "Select and upload a cloud assembly", choose your cloud assembly zip file and click Upload.
7. Under "Select and upload an application image," choose your application image zip file and click Upload.  
   (Be sure to leave the version as "default".)
8. Click Done.



Part 2. Maya.Client
=======================

Now that the Maya rendering service is configured in Batch Apps, we need a way to submit Maya files
to be rendered.
The sample client is an Plug-in for Maya written in Python, that can be used on multiple platforms.

Python Setup
-------------

The plug-in requires some additional Python packages in order to run.
Maya is shipped with its own Python environment, so it's into this environment that these
packages will need to be installed.
There are several approaches one could take:

- Run the included dependencies.py script with mayapy.exe. This is an experimental script to conveniently
  download and unpack the required modules into MAya's Python environment. To execute, run the following
  command from a terminal/command line with administrator privileges::

	>> mayapy.exe dependencies.py

- If there is already an installation of Python 2.7 on the machine, one can use pip to install the required
  packages, choosing the Maya bundled Python environment as the target directory for the installation. Note that by
  installing azure-batch-apps first, all the remaining packages will be installed automatically as dependencies::

	>> pip install --target "Autodesk/Maya2015/Python/Lib/site-packages" azure-batch-apps

- Download the packages directly from `pypi.python.org <http://pypi.python.org>`_. Extract their module subfolders and copy them into the 
  Maya bundled Python environment::

	Destination: ~/Autodesk/Maya2015/Python/Lib/site-packages

The required packages are the following:

- `Batch Apps Python Client <https://pypi.python.org/pypi/azure-batch-apps>`_
- `Keyring <https://pypi.python.org/pypi/keyring>`_
- `OAuthLib <https://pypi.python.org/pypi/oauthlib>`_
- `Requests-OAuthLib <https://pypi.python.org/pypi/requests-oauthlib>`_
- `Requests <https://pypi.python.org/pypi/requests>`_

The Maya site-packages folder should look like this when complete::

	site-packages
	|
	| -- batchapps
	|    |
	|    | -- __init__.py
	|    | -- other batchapps components
	|
	| -- keyring
	|    |
	|    | -- __init__.py
	|    | -- other keyring components
	|
	| -- oauthlib
	|    |
	|    | -- __init__.py
	|    | -- other oauthlib components
	|
	| -- requests
	|    |
	|    | -- __init__.py
	|    | -- other requests components
	|
	| -- requests_oauthlib
	|    |
	|    | -- __init__.py
	|    | -- other requests_oauthlib components
	|
	| -- Other installed modules (e.g. pymel)


Building and Installing the Plug-in
----------------------------------

The plug-in can be run directly from the the batchapps_maya directory, which can be placed anywhere.

To install the Plug-in:

1. Run Maya
2. Open Window > Settings/Preferences > Plug-in Manager
3. Click 'Browse'
5. Navigate to and select batchapps_maya/plug-in/batchapps.py.
6. The Plug-in should be loaded automatically, you can also chose to select Auto Load for future sessions. 
7. Once activated, the plug-in shelf will have appeared in the UI.


Plug-in Logging and Configuration
--------------------------------

The sample plug-in logs to both Maya's script editor and to file.
By default this log file will be saved to $HOME/BatchAppsData. This directory is also the location of the Plug-in
configuration file.

The authentication details and logging level are configurable within the Plug-in UI.

1. Run Maya.
2. Load the plug-in as per the steps above.
3. Run the plug-in by selecting the first button on the BatchApps shelf.
4. The first tab to load will be the config tab, set up your authentication details here (further instructions below).
5. Click 'Save Changes' and 'Authenticate'.
6. The plug-in is now ready to submit.


Authentication
---------------

To run this plug-in you will need:

- Your Batch Apps service URL
- Unattended account credentials for your Batch Apps service

1. Open the Azure management portal (manage.windowsazure.com).
2. Select Batch Services in the left-hand menu.
3. Select your account in the list and click "Manage Batch Apps" to open the Batch Apps management 
   portal. Your Batch Apps Service should be displayed, or you can navigate to it using the Services left-hand menu option.
4. Copy the service URL from the page and paste it into the 'Service' field in the Maya plug-in config tab.
5. Click the Unattended Account button at the bottom of the page. 
6. Copy the Account ID from the page and paste it into the 'Unattended Account' field in the Maya plug-in config tab.
7. Below the Account Keys list, select the desired duration and click the Add Key button.
   Copy the generated key and paste it into the 'Unattended Key' field in the Maya plug-in config tab.
   NOTE: the generated key will be shown only once!  If you accidentally close the page
   before copying the key, just reopen it and add a new key.