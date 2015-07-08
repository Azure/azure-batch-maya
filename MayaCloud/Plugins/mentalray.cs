﻿using System;
using System.Collections.Generic;
using System.Linq;

namespace Maya.Cloud.Plugins
{
    internal class MentalRay : MayaPlugin
    {
        private readonly string _exepath;

        public MentalRay(string appVersion)
        {
            _exepath = string.Format(@"mentalrayForMaya{0}", appVersion);
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
                return string.Empty;
            }
        }

        public override IList<string> PathVariables
        {
            get
            {
                return new List<string> { @"{0}\{1}\bin;" };
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
                    { "MENTALRAY_LOCATION ", @"{0}\{1}\;" },
                    { "MENTALRAY_BIN_LOCATION ", @"{0}\{1}\bin;" },
                    { "PYTHONPATH", @"{0}\{1}\scripts\AETemplates;{0}\{1}\scripts\mentalray;{0}\{1}\scripts\unsupported;{0}\{1}\scripts;" },
                    { "MENTALRAY_SHADERS_LOCATION", @"{0}\{1}\shaders;" },
                    { "MAYA_RENDER_DESC_PATH", @"{0}\{1}\rendererDesc;" },
                    { "MENTAL_RAY_INCLUDE_LOCATION", @"{0}\{1}\shaders\include;" },
                    { "MAYA_SCRIPT_PATH", @"{0}\{1}\scripts\AETemplates;{0}\{1}\scripts\mentalray;{0}\{1}\scripts\unsupported;{0}\{1}\scripts;" },
                    { "IMF_PLUG_IN_PATH", @"{0}\{1}\bin\image;" },
                    { "MAYA_PLUGIN_RESOURCE_PATH", @"{0}\{1}\resources;" },
                    { "MAYA_PRESET_PATH", @"{0}\{1}\presets\attrPresets;{0}\{1}\presets\attrPresets\maya_bifrost_liquid;{0}\{1}\presets\attrPresets\mia_material;{0}\{1}\presets\attrPresets\mia_material_x;{0}\{1}\presets\attrPresets\mia_material_x_passes;{0}\{1}\presets;" },
                    { "XBMLANGPATH", @"{0}\{1}\icons;" },
                };
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

        public override void SetupMayaEnv(IDictionary<string, string> mayaEnv, string exeRoot, string localpath)
        {
            var formattedMayaEnv = new Dictionary<string, string>();
            foreach (var item in MayaEnvVariables)
            {
                formattedMayaEnv[item.Key] = string.Format(item.Value, exeRoot, ExePath);
            }

            MergeParameters(mayaEnv, formattedMayaEnv);
        }
    }
}
