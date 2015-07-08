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
        public String Version { get; set; }

        [DataMember]
        public String Application { get; set; }

        [DataMember]
        public String UserDirectory { get; set; }

        [DataMember]
        public String Adlm { get; set; }


    }
}
