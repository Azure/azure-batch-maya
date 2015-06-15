using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Globalization;
using System.Threading.Tasks;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using Microsoft.Azure.Batch.Apps.Cloud;
using Maya.Cloud.Plugins;
using System.IO;

namespace Maya.Cloud.Settings
{
    [DataContract]
    class PluginSettings
    {
        [DataMember]
        public IList<string> Plugins { get; set; } 

        [DataMember]
        public IDictionary<string, string> EnvVariables { get; set; }
    }
}
