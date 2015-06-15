using System;
using System.Collections.Generic;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Threading;
using System.Globalization;

namespace Maya.Cloud.Plugins
{
    public class Arnold : MayaPlugin
    {
        private readonly string _exepath;

        public Arnold(string AppVersion)
        {
            _exepath = String.Format(@"solidangle\mtoadeploy\{0}", AppVersion);
        }

        public override string ExePath
        {
            get { return _exepath; }
        }

        public override string Command
        {
            get { return @"-ai:sptx ""{2}"" "; }
        }

        public override IList<string> PathVariables
        {
            get { return new List<String> { }; }
        }

        public override IDictionary<String, String> EnvVariables
        {
            get { return new Dictionary<String, String> { }; }
        }

        public override IDictionary<String, String> MayaEnvVariables
        {
            get
            {
                return new Dictionary<String, String> { { "MAYA_PLUG_IN_PATH ", @"{0}\{1}\plug-ins;" },
                                                        { "MTOA_EXTENSIONS_PATH ", @"{0}\{1}\extensions;" },
                                                        { "MTOA_PROCEDURAL_PATH ", @"{0}\{1}\procedurals;" },
                                                        { "PYTHONPATH", @"{0}\{1}\scripts;" },
                                                        { "ARNOLD_PLUGIN_PATH", @"{0}\{1}\shaders;{0}\{1}\procedurals;" },
                                                        { "MTOA_PATH", @"{0}\{1}\;" },
                                                        { "MAYA_SCRIPT_PATH", @"{0}\{1}\scripts;" },
                                                        { "MAYA_PLUGIN_RESOURCE_PATH", @"{0}\{1}\resources;" },
                                                        { "MAYA_PRESET_PATH", @"{0}\{1}\presets;" },

            }; }
        }

        public override void CreateModFile(string location, string executables)
        {
            var mtoaMod = Path.Combine(location, "mtoa.mod");
            if (!File.Exists(mtoaMod))
            {
                var formattedMod = string.Format("+ mtoa any {0}", String.Format(ExePath, executables));
                using (var modFile = new StreamWriter(mtoaMod))
                {
                    modFile.WriteLine(formattedMod);
                    modFile.WriteLine("PATH +:= bin");
                }
            }
        }

        public override void SetupMayaEnv(IDictionary<String, String> MayaEnv, string ExeRoot, string Localpath)
        {
            var FormattedMayaEnv = new Dictionary<String, String>();
            foreach (var item in MayaEnv)
                FormattedMayaEnv[item.Key] = String.Format(item.Value, ExeRoot, ExePath, Localpath);

            MergeParameters(MayaEnv, MayaEnvVariables);
        }
    }
}
