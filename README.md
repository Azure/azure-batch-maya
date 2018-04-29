# Azure Batch for Maya

This project demonstrates cloud rendering using the Azure Batch service with integrated licensing for Maya, VRay and Arnold.

Please note that the Azure Batch licensing service for Maya is currently in preview.
For more information and to register your interest, please see [rendering.azure.com](rendering.azure.com).

In order to run this sample, you will need to [create an Azure Batch account](https://docs.microsoft.com/azure/batch/batch-account-create-portal).
You will also need a storage account. You will have the option to create a storage account as part of the Batch account setup for use as `Auto Storage`.
You can use this, or you can [set up a storage account independently](https://docs.microsoft.com/azure/storage/storage-create-storage-account).


## Loading the plug-in in Maya and installing dependencies

Download the latest plug-in release and extract the azure_batch_maya directory to a location of your choice.
The plug-in can be run directly from the azure_batch_maya directory.

To install the plug-in:

1. Run Maya
2. Open Window > Settings/Preferences > Plug-in Manager
3. Click `Browse`
5. Navigate to and select azure_batch_maya/plug-in/AzureBatch.py.
6. Once activated, the plug-in shelf will have appeared in the UI.

The first time the plug-in is loaded, you will be prompted to agree to some terms and conditions, and install some Python dependencies.
The downloading and installing of the Python dependencies may take a few minutes, after which you will need to close and reopen Maya to
ensure the updated dependencies are loaded correctly.

Any errors in the dependency install will be logged to the file "AzureBatchInstall.log" in the "azure-batch-libs" folder, which is created for holding dependencies. In windows this is located at: Users\<username>\Documents\maya\<version>\scripts\azure-batch-libs


![](./docs/images/install_dependencies.png)


## Authentication

Before using the plug-in, it will need to be authenticated using your Azure Batch and Azure Storage account keys.
In order to retrieve this information:

1. Open the Azure management portal (portal.azure.com).
2. Select Azure Batch Accounts in the left-hand menu. This can be found under `More Services` in the `Compute` category.
3. Select your account in the list. Copy and paste the account URL into `Service` field of the plug-in UI. Paste the account name into the `Batch Account` field.
4. In the portal, select `Keys` on the left-hand menu. Copy and paste one of the access keys into the `Batch Key` field in the plug-in.
5. Return to the management portal home, and select Storage Accounts from the left-hand menu. This can be found under `More Services` in the `Storage` category.
6. Select your account from the list. Copy and paste the account name into the `Storage Account` field.
7. In the portal, select `Access Keys` on the left-hand menu. Copy and paste one of the access keys into the `Storage Key` field.
8. Click `Authenticate`.

![](./docs/images/authentication.png)

## Using the Azure Batch plug-in

- [Job configuration](./docs/submitting_jobs.md#job-configuration)
- [Managing assets](./docs/submitting_jobs.md#managing-assets)
- [Environment configuration](./docs/submitting_jobs.md#environment-configuration)
- [Managing Pools](./docs/submitting_jobs.md#managing-pools)
- [Monitoring jobs](./docs/submitting_jobs.md#monitoring-jobs)


## Uninstall

To uninstall the plug-in:

1. Run Maya
2. Open Window > Settings/Preferences > Plug-in Manager
3. Scroll down and find the entry for AzureBatch.py, it may be necessary to expand the folder view
4. Untick the "Load" and "Auto Load" entries for AzureBatch.py
5. Confirm the removal of the shelf 
6. Confirm to remove the dependencies if you wish a clean uninstall

To remove config which is retained for a reinstall, delete the config file "azure_batch.ini". For Windows this is located in:
Users\<username>\Documents\maya\2017\prefs\AzureBatchData

Interrupted uninstalls may fail to delete the "AzureBatch.mod" file and it may be necessary to delete this manually. For Windows this is located in:
ProgramFiles\Maya\Maya2017\modules


##  Upgrading or reinstalling

When upgrading the plugin, it is recommended to Uninstall the previous version of the plugin, then close and reopen Maya before Installing the new version of the plugin, following the instructions above for Uninstall and Install.


##  Side-by-side compatibility

Side-by-side installs are supported for Maya 2017 and 2018. The plugin installs and is managed independently in Maya 2017 and 2018, so you can have it installed for both 2017 and 2018 at one time. Each install can be configured for a different Batch account or they can share an account. If the plugin is installed side-by-side, it is recommended that both installs are of the same identical version / release of the plugin.

## Supported Maya Versions
Earlier versions of the code and releases were supported on Maya2017-Update3 only. 

Release v0.14.0 adds support for Maya2017-Update4 and Maya2018.

Release v0.16.0 supports Maya2017-Update5

## License

This project is licensed under the MIT License.
For details see LICENSE.txt or visit [opensource.org/licenses/MIT](http://opensource.org/licenses/MIT).


## Contributing

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). 
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) 
with any additional questions or comments.
