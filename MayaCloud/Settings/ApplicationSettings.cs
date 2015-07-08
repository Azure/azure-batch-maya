//--------------------------------------------------------------------------
//
// Maya Batch C# Cloud Assemblies 
// 
// Copyright (c) Microsoft Corporation.  All rights reserved. 

using System;
using System.Linq;
using System.Runtime.Serialization;

namespace Maya.Cloud.Settings
{
    [DataContract]
    public class ApplicationSettings
    {
        [DataMember]
        public string Version { get; set; }

        [DataMember]
        public string Application { get; set; }

        [DataMember]
        public string UserDirectory { get; set; }

        [DataMember]
        public string Adlm { get; set; }
    }
}
