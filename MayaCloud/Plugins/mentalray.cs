using System;
using System.Collections.Generic;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Threading;
using System.Globalization;

namespace Maya.Cloud.Plugins
{
    class MentalRay : MayaPlugin
    {

        private readonly string _exepath;

        public MentalRay(string AppVersion)
        {
            _exepath = String.Format(@"mentalrayForMaya{0}", AppVersion);
        }

        public override string ExePath
        {
            get { return _exepath; }
        }

        public override string Command
        {
            get { return String.Empty; }
        }

        public override IList<string> PathVariables
        {
            get { return new List<String> { @"{0}\{1}\bin;" }; }
        }

        public override IDictionary<String, String> EnvVariables
        {
            get
            {
                return new Dictionary<String, String> { };
            }
        }

        public override IDictionary<String, String> MayaEnvVariables
        {
            get
            {
                return new Dictionary<String, String> { { "MAYA_PLUG_IN_PATH", @"{0}\{1}\plug-ins;" },
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
                                                        { "XBMLANGPATH", @"{0}\{1}\icons;" },};
            }
        }

        public override string SetupPath(string ExeRoot, string Localpath)
        {
            var FormattedPaths = new List<string>();
            foreach (var item in PathVariables)
                FormattedPaths.Add(String.Format(item, ExeRoot, ExePath));

            return String.Join(";", FormattedPaths.ToArray());
        }

        public override void SetupMayaEnv(IDictionary<String, String> MayaEnv, string ExeRoot, string Localpath)
        {
            var FormattedMayaEnv = new Dictionary<String, String>();
            foreach (var item in MayaEnvVariables)
                FormattedMayaEnv[item.Key] = String.Format(item.Value, ExeRoot, ExePath);

            MergeParameters(MayaEnv, FormattedMayaEnv);
        }
    }
}
