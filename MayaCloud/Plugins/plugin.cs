using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Maya.Cloud.Plugins
{
    public abstract class MayaPlugin
    {
        public abstract string ExePath { get; }

        public abstract string Command { get; }

        public abstract IDictionary<String, String> EnvVariables { get; }

        public abstract IDictionary<String, String> MayaEnvVariables { get; }

        public abstract IList<string> PathVariables { get; }

        public abstract void CreateModFile(string location);

        public abstract void SetupEnv(IDictionary<String, String> Env, string ExeRoot, string Localpath) { }

        public abstract void SetupMayaEnv(IDictionary<String, String> MayaEnv, string ExeRoot, string Localpath) { }

        public abstract string SetupPath(string ExeRoot, string Localpath)
        {
            return String.Empty;
        }

        protected static IDictionary<String, String> MergeParameters(IDictionary<String, String> basedict, IDictionary<String, String> mergedict)
        {
            foreach (var item in mergedict)
                if (!basedict.ContainsKey(item.Key))
                    basedict.Add(item.Key, item.Value);
                else
                    basedict[item.Key] = basedict[item.Key] + mergedict[item.Key];

            return basedict;
        }



    }
}
