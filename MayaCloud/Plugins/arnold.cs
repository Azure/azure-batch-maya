﻿using System;
using System.Linq;
using System.Collections.Generic;
using System.IO;

namespace Maya.Cloud.Plugins
{
    public class Arnold : MayaPlugin
    {
        private readonly string _exepath;

        public Arnold(string appVersion)
        {
            _exepath = string.Format(@"solidangle\mtoadeploy\{0}", appVersion);
        }

        public override string ExePath
        {
            get
            {
                return _exepath;
            }
        }

        public override string Command
        {
            get
            {
                return @"-ai:sptx ""{2}"" ";
            }
        }

        public override IList<string> PathVariables
        {
            get
            {
                return new List<string> { };
            }
        }

        public override IDictionary<string, string> EnvVariables
        {
            get
            {
                return new Dictionary<string, string> { };
            }
        }

        public override IDictionary<string, string> MayaEnvVariables
        {
            get
            {
                return new Dictionary<string, string>
                {
                    { "MAYA_PLUG_IN_PATH", @"{0}\{1}\plug-ins;" },
                    { "MAYA_RENDER_DESC_PATH", @"{0}\{1};" },
                    { "MTOA_EXTENSIONS_PATH ", @"{0}\{1}\extensions;" },
                    { "MTOA_PROCEDURAL_PATH ", @"{0}\{1}\procedurals;" },
                    { "PYTHONPATH", @"{0}\{1}\scripts;" },
                    { "ARNOLD_PLUGIN_PATH", @"{0}\{1}\shaders;{0}\{1}\procedurals;" },
                    { "MTOA_PATH", @"{0}\{1}\;" },
                    { "MAYA_SCRIPT_PATH", @"{0}\{1}\scripts;" },
                    { "MAYA_PLUGIN_RESOURCE_PATH", @"{0}\{1}\resources;" },
                    { "MAYA_PRESET_PATH", @"{0}\{1}\presets;" },
                    { "MTOA_LOG_PATH", @"{2}" }
                };
            }
        }

        public override void CreateModFile(string exeRoot, string location)
        {
            var mtoaMod = Path.Combine(location, "mtoa.mod");
            if (!File.Exists(mtoaMod))
            {
                using (var modFile = new StreamWriter(mtoaMod))
                {
                    modFile.WriteLine(string.Format("+ mtoa any {0}\\{1}", exeRoot, ExePath));
                    modFile.WriteLine("PATH +:= bin");
                }
            }
        }

        public override void SetupMayaEnv(IDictionary<string, string> mayaEnv, string exeRoot, string localpath)
        {
            var formattedMayaEnv = new Dictionary<string, string>();
            foreach (var item in MayaEnvVariables)
            {
                formattedMayaEnv[item.Key] = string.Format(item.Value, exeRoot, ExePath, localpath);
            }

            MergeParameters(mayaEnv, formattedMayaEnv);
        }
    }
}
