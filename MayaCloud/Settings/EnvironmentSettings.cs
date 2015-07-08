using System;
using System.Linq;
using System.Collections.Generic;

namespace Maya.Cloud.Settings
{
    public class EnvironmentSettings
    {
        public string LicenseServer { get; set; }

        public string LicensePort { get; set; }

        public List<string> PathMaps { get; set; }

        public List<string> Plugins { get; set; }

        public Dictionary<string, string> EnvVariables { get; set; }
    }
}
