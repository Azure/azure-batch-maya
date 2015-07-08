using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Maya.Cloud.Plugins
{
    internal class Yeti : MayaPlugin
    {
        public Yeti(string appVersion)
        {
        }

        public override string ExePath
        {
            get
            {
                return @"PeregrineLabs\Yeti";
            }
        }

        public override string Command
        {
            get
            {
                return string.Empty;
            }
        }

        public override IList<string> PathVariables
        {
            get
            {
                return new List<string> { @"{0}\{1}\bin" };
            }
        }

        public override IDictionary<string, string> EnvVariables
        {
            get
            {
                return new Dictionary<string, string>
                {
                    { "YETI_HOME ", @"{0}\{1}\bin;" },
                    { "YETI_INTERACTIVE_LICENSE ", "0" }
                };
            }
        }

        public override IDictionary<string, string> MayaEnvVariables
        {
            get
            {
                return new Dictionary<string, string>
                {
                    { "MAYA_PLUG_IN_PATH ", @"{0}\{1}\plug-ins;" },
                    { "MTOA_EXTENSIONS_PATH ", @"{0}\{1}\plug-ins;" },
                    { "MTOA_PROCEDURAL_PATH ", @"{0}\{1}\bin;" },
                    { "PYTHONPATH", @"{0}\{1}\scripts;" },
                    { "PEREGRINE_LOG_FILE", @"{2}\yeti_log.txt" },
                    { "YETI_TMP", @"{3}" },
                    { "MAYA_SCRIPT_PATH", @"{0}\{1}\scripts;" }
                };
            }
        }

        public override void CreateModFile(string exeRoot, string location)
        {
            var mtoaMod = Path.Combine(location, "mtoa.mod");
            if (!File.Exists(mtoaMod))
            {
                var formattedMod = string.Format("+ mtoa any {0}\\{1}", exeRoot, ExePath);
                using (var modFile = new StreamWriter(mtoaMod))
                {
                    modFile.WriteLine(formattedMod);
                    modFile.WriteLine("PATH +:= bin");
                }
            }
        }

        public override string SetupPath(string exeRoot, string localpath)
        {
            var formattedPaths = new List<string>();
            foreach (var item in PathVariables)
            {
                formattedPaths.Add(string.Format(item, exeRoot, ExePath));
            }

            return string.Join(";", formattedPaths.ToArray());
        }

        public override void SetupEnv(IDictionary<string, string> env, string exeRoot, string localpath)
        {
            var formattedEnv = new Dictionary<string, string>();
            foreach (var item in EnvVariables)
            {
                formattedEnv[item.Key] = string.Format(item.Value, exeRoot, ExePath, localpath);
            }

            MergeParameters(env, formattedEnv);
        }

        public override void SetupMayaEnv(IDictionary<string, string> mayaEnv, string exeRoot, string localpath)
        {
            var formattedMayaEnv = new Dictionary<string, string>();
            foreach (var item in MayaEnvVariables)
            {
                formattedMayaEnv[item.Key] = string.Format(item.Value, exeRoot, ExePath, localpath, Path.GetTempPath());
            }

            MergeParameters(mayaEnv, formattedMayaEnv);
        }

        public override void PreRenderScript(StreamWriter script, string exeRoot, string localPath)
        {
            script.WriteLine("pgYetiRenderCommand -preRenderCache -fileName \"{0}\\fur.%04d.fur\" pgYetiMaya;");
        }
    }
}
