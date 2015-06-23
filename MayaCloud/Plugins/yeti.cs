﻿using System;
using System.Collections.Generic;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Threading;
using System.Globalization;

namespace Maya.Cloud.Plugins
{
    class Yeti : MayaPlugin
    {
        public Yeti(string AppVersion) { }

        public override string ExePath
        {
            get { return @"PeregrineLabs\Yeti"; }
        }

        public override string Command
        {
            get { return String.Empty; }
        }

        public override IList<string> PathVariables
        {
            get { return new List<String> { @"{0}\{1}\bin" }; }
        }

        public override IDictionary<String, String> EnvVariables
        {
            get
            {
                return new Dictionary<String, String> { { "YETI_HOME ", @"{0}\{1}\bin;" }, 
                                                        { "YETI_INTERACTIVE_LICENSE ", "0" }};
            }
        }

        public override IDictionary<String, String> MayaEnvVariables
        {
            get
            {
                return new Dictionary<String, String> { { "MAYA_PLUG_IN_PATH ", @"{0}\{1}\plug-ins;" },
                                                        { "MTOA_EXTENSIONS_PATH ", @"{0}\{1}\plug-ins;" },
                                                        { "MTOA_PROCEDURAL_PATH ", @"{0}\{1}\bin;" },
                                                        { "PYTHONPATH", @"{0}\{1}\scripts;" },
                                                        { "PEREGRINE_LOG_FILE", @"{2}\yeti_log.txt" },
                                                        { "YETI_TMP", @"{3}" },
                                                        { "MAYA_SCRIPT_PATH", @"{0}\{1}\scripts;" }};
            }
        }

        public override void CreateModFile(string ExeRoot, string Location)
        {
            var mtoaMod = Path.Combine(Location, "mtoa.mod");
            if (!File.Exists(mtoaMod))
            {
                var formattedMod = string.Format("+ mtoa any {0}\\{1}", ExeRoot, ExePath);
                using (var modFile = new StreamWriter(mtoaMod))
                {
                    modFile.WriteLine(formattedMod);
                    modFile.WriteLine("PATH +:= bin");
                }
            }
        }

        public override string SetupPath(string ExeRoot, string Localpath)
        {
            var FormattedPaths = new List<string>();
            foreach (var item in PathVariables)
                FormattedPaths.Add(String.Format(item, ExeRoot, ExePath));

            return String.Join(";", FormattedPaths.ToArray());
        }

        public override void SetupEnv(IDictionary<String, String> Env, string ExeRoot, string Localpath)
        {
            var FormattedEnv = new Dictionary<String, String>();
            foreach (var item in EnvVariables)
                FormattedEnv[item.Key] = String.Format(item.Value, ExeRoot, ExePath, Localpath);

            MergeParameters(Env, FormattedEnv);
        }

        public override void SetupMayaEnv(IDictionary<String, String> MayaEnv, string ExeRoot, string Localpath)
        {
            var FormattedMayaEnv = new Dictionary<String, String>();
            foreach (var item in MayaEnvVariables)
                FormattedMayaEnv[item.Key] = String.Format(item.Value, ExeRoot, ExePath, Localpath, Path.GetTempPath());

            MergeParameters(MayaEnv, FormattedMayaEnv);
        }

        public override void PreRenderScript(StreamWriter script, string ExeRoot, string LocalPath)
        {
            script.WriteLine("pgYetiRenderCommand -preRenderCache -fileName \"{0}\\fur.%04d.fur\" pgYetiMaya;");
        }
    }
}