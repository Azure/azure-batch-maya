using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Maya.Cloud.Plugins
{
    public abstract class MayaPlugin
    {
        public abstract string ExePath { get; }

        public abstract string Command { get; }

        public abstract IDictionary<string, string> EnvVariables { get; }

        public abstract IDictionary<string, string> MayaEnvVariables { get; }

        public abstract IList<string> PathVariables { get; }

        public virtual void CreateModFile(string exeRoot, string location)
        {
        }

        public virtual void SetupEnv(IDictionary<string, string> env, string exeRoot, string localpath)
        {
        }

        public virtual void SetupMayaEnv(IDictionary<string, string> mayaEnv, string exeRoot, string localpath)
        {
        }

        public virtual void PreRenderScript(StreamWriter script, string exeRoot, string localPath)
        {
        }

        public virtual string SetupPath(string exeRoot, string localpath)
        {
            return string.Empty;
        }

        protected static IDictionary<string, string> MergeParameters(
            IDictionary<string, string> basedict,
            IDictionary<string, string> mergedict)
        {
            foreach (var item in mergedict)
            {
                if (!basedict.ContainsKey(item.Key))
                {
                    basedict.Add(item.Key, item.Value);
                }
                else
                {
                    basedict[item.Key] = basedict[item.Key] + mergedict[item.Key];
                }
            }

            return basedict;
        }
    }
}
