using System;
using System.Collections.ObjectModel;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Globalization;
using System.Threading.Tasks;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using Microsoft.Azure.Batch.Apps.Cloud;
using System.IO;

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


    }
}
