# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from azure.batch.models import PoolSpecification


class ExtendedPoolSpecification(PoolSpecification):
    """Specification for creating a new pool.

    :param display_name: The display name for the pool. The display name need
     not be unique and can contain any Unicode characters up to a maximum
     length of 1024.
    :type display_name: str
    :param vm_size: The size of the virtual machines in the pool. All virtual
     machines in a pool are the same size. For information about available
     sizes of virtual machines for Cloud Services pools (pools created with
     cloudServiceConfiguration), see Sizes for Cloud Services
     (http://azure.microsoft.com/documentation/articles/cloud-services-sizes-specs/).
     Batch supports all Cloud Services VM sizes except ExtraSmall. For
     information about available VM sizes for pools using images from the
     Virtual Machines Marketplace (pools created with
     virtualMachineConfiguration) see Sizes for Virtual Machines (Linux)
     (https://azure.microsoft.com/documentation/articles/virtual-machines-linux-sizes/)
     or Sizes for Virtual Machines (Windows)
     (https://azure.microsoft.com/documentation/articles/virtual-machines-windows-sizes/).
     Batch supports all Azure VM sizes except STANDARD_A0 and those with
     premium storage (STANDARD_GS, STANDARD_DS, and STANDARD_DSV2 series).
    :type vm_size: str
    :param cloud_service_configuration: The cloud service configuration for
     the pool. This property must be specified if the pool needs to be created
     with Azure PaaS VMs. This property and virtualMachineConfiguration are
     mutually exclusive and one of the properties must be specified. If neither
     is specified then the Batch service returns an error; if you are calling
     the REST API directly, the HTTP status code is 400 (Bad Request). This
     property cannot be specified if the Batch account was created with its
     poolAllocationMode property set to 'UserSubscription'.
    :type cloud_service_configuration: :class:`CloudServiceConfiguration
     <azure.batch.models.CloudServiceConfiguration>`
    :param virtual_machine_configuration: The virtual machine configuration
     for the pool. This property must be specified if the pool needs to be
     created with Azure IaaS VMs. This property and cloudServiceConfiguration
     are mutually exclusive and one of the properties must be specified. If
     neither is specified then the Batch service returns an error; if you are
     calling the REST API directly, the HTTP status code is 400 (Bad Request).
    :type virtual_machine_configuration: :class:`VirtualMachineConfiguration
     <azure.batch.models.VirtualMachineConfiguration>`
    :param max_tasks_per_node: The maximum number of tasks that can run
     concurrently on a single compute node in the pool. The default value is 1.
     The maximum value of this setting depends on the size of the compute nodes
     in the pool (the vmSize setting).
    :type max_tasks_per_node: int
    :param task_scheduling_policy: How tasks are distributed among compute
     nodes in the pool.
    :type task_scheduling_policy: :class:`TaskSchedulingPolicy
     <azure.batch.models.TaskSchedulingPolicy>`
    :param resize_timeout: The timeout for allocation of compute nodes to the
     pool. This timeout applies only to manual scaling; it has no effect when
     enableAutoScale is set to true. The default value is 15 minutes. The
     minimum value is 5 minutes. If you specify a value less than 5 minutes,
     the Batch service rejects the request with an error; if you are calling
     the REST API directly, the HTTP status code is 400 (Bad Request).
    :type resize_timeout: timedelta
    :param target_dedicated: The desired number of compute nodes in the pool.
     This property must not be specified if enableAutoScale is set to true. It
     is required if enableAutoScale is set to false.
    :type target_dedicated: int
    :param enable_auto_scale: Whether the pool size should automatically
     adjust over time. If false, the targetDedicated element is required. If
     true, the autoScaleFormula element is required. The pool automatically
     resizes according to the formula. The default value is false.
    :type enable_auto_scale: bool
    :param auto_scale_formula: The formula for the desired number of compute
     nodes in the pool. This property must not be specified if enableAutoScale
     is set to false. It is required if enableAutoScale is set to true. The
     formula is checked for validity before the pool is created. If the formula
     is not valid, the Batch service rejects the request with detailed error
     information.
    :type auto_scale_formula: str
    :param auto_scale_evaluation_interval: The time interval at which to
     automatically adjust the pool size according to the autoscale formula. The
     default value is 15 minutes. The minimum and maximum value are 5 minutes
     and 168 hours respectively. If you specify a value less than 5 minutes or
     greater than 168 hours, the Batch service rejects the request with an
     invalid property value error; if you are calling the REST API directly,
     the HTTP status code is 400 (Bad Request).
    :type auto_scale_evaluation_interval: timedelta
    :param enable_inter_node_communication: Whether the pool permits direct
     communication between nodes. Enabling inter-node communication limits the
     maximum size of the pool due to deployment restrictions on the nodes of
     the pool. This may result in the pool not reaching its desired size. The
     default value is false.
    :type enable_inter_node_communication: bool
    :param network_configuration: The network configuration for the pool.
    :type network_configuration: :class:`NetworkConfiguration
     <azure.batch.models.NetworkConfiguration>`
    :param start_task: A task to run on each compute node as it joins the
     pool. The task runs when the node is added to the pool or when the node is
     restarted.
    :type start_task: :class:`StartTask <azure.batch.models.StartTask>`
    :param certificate_references: A list of certificates to be installed on
     each compute node in the pool. For Windows compute nodes, the Batch
     service installs the certificates to the specified certificate store and
     location. For Linux compute nodes, the certificates are stored in a
     directory inside the task working directory and an environment variable
     AZ_BATCH_CERTIFICATES_DIR is supplied to the task to query for this
     location. For certificates with visibility of 'remoteUser', a 'certs'
     directory is created in the user's home directory (e.g.,
     /home/{user-name}/certs) and certificates are placed in that directory.
    :type certificate_references: list of :class:`CertificateReference
     <azure.batch.models.CertificateReference>`
    :param application_package_references: The list of application packages to
     be installed on each compute node in the pool. This property is currently
     not supported on auto pools created with the virtualMachineConfiguration
     (IaaS) property.
    :type application_package_references: list of
     :class:`ApplicationPackageReference
     <azure.batch.models.ApplicationPackageReference>`
    :param user_accounts: The list of user accounts to be created on each node
     in the pool.
    :type user_accounts: list of :class:`UserAccount
     <azure.batch.models.UserAccount>`
    :param metadata: A list of name-value pairs associated with the pool as
     metadata. The Batch service does not assign any meaning to metadata; it is
     solely for the use of user code.
    :type metadata: list of :class:`MetadataItem
     <azure.batch.models.MetadataItem>`
    :param package_references: A list of packages to be installed on the compute
     nodes. Must be of a Package Manager type in accordance with the selected
     operating system.
    :type package_references: list of :class:`PackageReferenceBase
     <azure.batch_extensions.models.PackageReferenceBase>`
    """

    _validation = {
        'vm_size': {'required': True},
    }

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'vm_size': {'key': 'vmSize', 'type': 'str'},
        'cloud_service_configuration': {'key': 'cloudServiceConfiguration', 'type': 'CloudServiceConfiguration'},
        'virtual_machine_configuration': {'key': 'virtualMachineConfiguration', 'type': 'VirtualMachineConfiguration'},
        'max_tasks_per_node': {'key': 'maxTasksPerNode', 'type': 'int'},
        'task_scheduling_policy': {'key': 'taskSchedulingPolicy', 'type': 'TaskSchedulingPolicy'},
        'resize_timeout': {'key': 'resizeTimeout', 'type': 'duration'},
        'target_dedicated': {'key': 'targetDedicated', 'type': 'int'},
        'enable_auto_scale': {'key': 'enableAutoScale', 'type': 'bool'},
        'auto_scale_formula': {'key': 'autoScaleFormula', 'type': 'str'},
        'auto_scale_evaluation_interval': {'key': 'autoScaleEvaluationInterval', 'type': 'duration'},
        'enable_inter_node_communication': {'key': 'enableInterNodeCommunication', 'type': 'bool'},
        'network_configuration': {'key': 'networkConfiguration', 'type': 'NetworkConfiguration'},
        'start_task': {'key': 'startTask', 'type': 'StartTask'},
        'certificate_references': {'key': 'certificateReferences', 'type': '[CertificateReference]'},
        'application_package_references': {'key': 'applicationPackageReferences', 'type': '[ApplicationPackageReference]'},
        'user_accounts': {'key': 'userAccounts', 'type': '[UserAccount]'},
        'metadata': {'key': 'metadata', 'type': '[MetadataItem]'},
        'package_references': {'key': 'packageReferences', 'type': '[PackageReferenceBase]'}
    }

    def __init__(self, vm_size, display_name=None, cloud_service_configuration=None, virtual_machine_configuration=None,
                 max_tasks_per_node=None, task_scheduling_policy=None, resize_timeout=None, target_dedicated=None, enable_auto_scale=None,
                 auto_scale_formula=None, auto_scale_evaluation_interval=None, enable_inter_node_communication=None, 
                 network_configuration=None, start_task=None, certificate_references=None,
                 application_package_references=None, user_accounts=None, metadata=None, package_references=None):
        super(ExtendedPoolSpecification, self).__init__(
            display_name=display_name,
            vm_size=vm_size,
            cloud_service_configuration=cloud_service_configuration,
            virtual_machine_configuration=virtual_machine_configuration,
            max_tasks_per_node=max_tasks_per_node,
            task_scheduling_policy=task_scheduling_policy,
            resize_timeout=resize_timeout,
            target_dedicated=target_dedicated,
            enable_auto_scale=enable_auto_scale,
            auto_scale_formula=auto_scale_formula,
            auto_scale_evaluation_interval=auto_scale_evaluation_interval,
            enable_inter_node_communication=enable_inter_node_communication,
            network_configuration=network_configuration,
            start_task=start_task,
            certificate_references=certificate_references,
            application_package_references=application_package_references,
            user_accounts=user_accounts,
            metadata=metadata)
        self.package_references = package_references
