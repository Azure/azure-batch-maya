using System;
using System.Collections.Generic;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Threading;
using System.Globalization;
using Maya.Cloud.Settings;
using Maya.Cloud.Plugins;
using Microsoft.Azure.Batch.Apps.Cloud;

namespace Maya.Cloud
{
    class MayaEnvironment
    {

        private string _localpath;
        private string _exepath;
        private IList<MayaPlugin> _plugins;

        private string _executable = @"{0}\bin\render.exe";

        private string _command = @"-renderer {0} -log ""{1}.log"" -proj ""{2}"" -preRender ""renderPrep"" -rd ""{2}"" -im ""{3}"" -s {4} -e {4} ";

        private static IDictionary<string, Func<string, MayaPlugin>> PluginMap = new Dictionary<string, Func<string, MayaPlugin>>
        {
            { "Arnold", (_version) => new Arnold(_version) },
            { "Yeti", (_version) => new Yeti(_version) },
            { "MentalRay", (_version) => new MentalRay(_version) },
        };

        private IList<String> PathVariables = new List<String> { @"{0}\bin;",
                                                                 @"{0}\plug-ins\substance\bin;",
                                                                 @"{0}\plug-ins\xgen\bin;",
                                                                 @"{0}\plug-ins\bifrost\bin;" };

        private IDictionary<String, String> EnvVariables = new Dictionary<String, String> { { "MAYA_APP_DIR", @"{0}" } };

        private IDictionary<String, String> MayaEnvVariables = new Dictionary<String, String> { { "MAYA_MODULE_PATH", @"{0}/{3}/modules;{1}/{4}/modules;{0}/Common Files/Autodesk Shared/Modules/maya/{5}" }.
                                                                                                { "FBX_LOCATION", @"{0}/{3}/plug-ing/fbx/" },
                                                                                                { "MAYA_SCRIPT_BASE", @"{0}/{3}" },
                                                                                                { "TEMP", @"{2}" },
                                                                                                { "TMP", @"{2}" },
                                                                                                { "MAYA_LOCATION", @"{0}\{3}" },
                                                                                                { "TMPDIR", @"{2}" },
                                                                                                { "MAYA_PLUG_IN_PATH", @"{0}/{3}/bin/plug-ins;{0}/{3}/plug-ins/bifrost/plug-ins;{0}/{3}/plug-ins/fbx/plug-ins;{0}/{3}/plug-ins/substance/plug-ins;{0}/{3}/plug-ins/xgen/plug-ins;{1};" },
                                                                                                { "PYTHONHOME", @"{0}/{3}/Python" },
                                                                                                { "XGEN_LOCATION", @"{0}/{3}/plug-ins/xgen/" },
                                                                                                { "SUBSTANCES_LOCATION", @"{0}/{3}/plug-ins/substance/substances" },
                                                                                                { "BIFROST_LOCATION", @"{0}/{3}/plug-ins/bifrost/" },
                                                                                                { "PYTHONPATH", @"{0}/{3}/plug-ins/bifrost/scripts/presets;{0}/{3}/plug-ins/bifrost/scripts;{0}/{3}/plug-ins/fbx/scripts;{0}/{3}/plug-ins/substance/scripts;{0}/{3}/plug-ins/xgen/scripts/cafm;{0}/{3}/plug-ins/xgen/scripts/xgenm;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui;{0}/{3}/plug-ins/xgen/scripts/xgenm/xmaya;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui/brushes;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui/dialogs;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui/fxmodules;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui/tabs;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui/util;{0}/{3}/plug-ins/xgen/scripts/xgenm/ui/widgets;{0}/{3}/plug-ins/xgen/scripts;" },
                                                                                                { "ILMDIR", @"{0}/Common Files/Autodesk Shared/Materials" },
                                                                                                { "MAYA_SCRIPT_PATH", @"{0}/{3}/scripts;{0}/{3}/scripts/startup;{0}/{3}/scripts/others;{0}/{3}/scripts/AETemplates;{0}/{3}/scripts/unsupported;{0}/{3}/scripts/paintEffects;{0}/{3}/scripts/fluidEffects;{0}/{3}/scripts/hair;{0}/{3}/scripts/cloth;{0}/{3}/scripts/live;{0}/{3}/scripts/fur;{0}/{3}/scripts/muscle;{0}/{3}/scripts/turtle;{0}/{3}/scripts/FBX;{0}/{3}/scripts/mayaHIK;{0}/{3}/plug-ins/bifrost/scripts/presets;{0}/{3}/plug-ins/bifrost/scripts;{0}/{3}/plug-ins/fbx/scripts;{1};" },
                                                                                                { "MAYA_PLUGIN_RESOURCE_PATH", @"{0}/{3}/plug-ins/bifrost/resources;{0}/{3}/plug-ins/fbx/resources;{0}/{3}/plug-ins/substance/resources;{0}/{3}/plug-ins/xgen/resources;{1}" },
                                                                                                { "MAYA_PRESET_PATH", @"{0}/{3}/plug-ins/bifrost/presets;{0}/{3}/plug-ins/fbx/presets;{0}/{3}/plug-ins/substance/presets;{0}/{3}/plug-ins/xgen/presets" },
                                                                                                { "XBMLANGPATH", @"{0}/{3}/plug-ins/bifrost/" }};

        public MayaEnvironment(MayaParameters AppParams, string Localpath, string ExeRoot, int TaskID, int FrameNumber)
        {
            _localpath = Localpath;
            _exepath = String.Format(@"{0}\{1}", ExeRoot, AppParams.ApplicationSettings.Application);

            _executable = String.Format(_executable, _exepath);
            _plugins = new List<MayaPlugin>();

            foreach (var env in EnvVariables)
                EnvVariables[env.Key] = String.Format(env.Value, Localpath);

            foreach (var plugin in AppParams.PluginSettings.Plugins)
                _plugins.Add(PluginMap[plugin](AppParams.ApplicationSettings.Version));

            foreach (var plugin in _plugins)
            {
                _command += plugin.Command;
                plugin.SetupEnv(EnvVariables, ExeRoot, Localpath);
                plugin.SetupMayaEnv(MayaEnvVariables, ExeRoot, Localpath);
            }

            SetEnvVariables(ExeRoot, Localpath);

            _command = String.Format(_command, AppParams.Renderer, TaskID, Localpath, AppParams.OutputName, FrameNumber);

            

        }

        public string Command
        {
            get { return _command; }
        }

        public string Executable
        {
            get { return _executable; }
        }

        private void SetEnvVariables(string ExePath, string Localpath)
        {
            foreach (var EnvVar in EnvVariables)
            {
                var CurrentVar = Environment.GetEnvironmentVariable(EnvVar.Key);
                if (CurrentVar == null)
                {
                    var NewVar = String.Format(EnvVar.Value, ExePath, Localpath);
                    Environment.SetEnvironmentVariable(EnvVar.Key, NewVar);
                }
            }

            var SysPath = Environment.GetEnvironmentVariable("PATH");

            var PathVar = String.Join("", PathVariables.ToArray());
            PathVar = String.Format(PathVar, _exepath);
            foreach (var plugin in _plugins)
                PathVar += plugin.SetupPath(ExePath, Localpath);

            Environment.SetEnvironmentVariable("PATH", string.Format(@"{0};{1}", SysPath, PathVar)); 
        }

        private string ConfigureMayaEnv(ApplicationSettings app)
        {

            var project = Path.Combine(LocalStoragePath, "workspace.mel");
            if (!File.Exists(project))
            {
                using (StreamWriter workspace = new StreamWriter(project))
                {
                    workspace.Write(MayaScripts.workspace);
                }
            }

            var license = Path.Combine(ExecutablesPath, app.Application, "bin",  "License.env");
            if (!File.Exists(license))
            {
                var formattedLic = string.Format(MayaScripts.lic, ExecutablesPath);
                using (var licFile = new StreamWriter(license))
                {
                    licFile.Write(formattedLic);
                }
            }

            var client = Path.Combine(ExecutablePath("Adlm"), "AdlmThinClientCustomEnv.xml");
            if (!File.Exists(client))
            {
                var formattedClient = string.Format(MayaScripts.client, ExecutablesPath, app.Adlm);
                using (var clientFile = new StreamWriter(client))
                {
                    clientFile.Write(formattedClient);
                }
            }

            var envDir = Path.Combine(LocalStoragePath, app.UserDirectory);
            if (!Directory.Exists(envDir))
            {
                Directory.CreateDirectory(envDir);
            }

            var scriptDir = Path.Combine(envDir, "scripts");
            if (!Directory.Exists(scriptDir))
            {
                Directory.CreateDirectory(scriptDir);
            }

            var modDir = Path.Combine(envDir, "modules");
            if (!Directory.Exists(modDir))
            {
                Directory.CreateDirectory(modDir);
            }

            var envPath = Path.Combine(envDir, "Maya.env");
            if (!File.Exists(envPath))
            {
                var formattedEnv = string.Format(MayaScripts.env, ExecutablesPath, LocalStoragePath, Path.GetTempPath(),
                    app.Application, app.UserDirectory, app.Version);

                using (var envFile = new StreamWriter(envPath))
                {
                    envFile.Write(formattedEnv);
                }
            }
                
            return project;
        }

        private void CreateEnvVariables(ApplicationSettings app)
        {
            foreach (var EnvVar in MayaParameters.EnvVariables)
            {
                var CurrentVar = Environment.GetEnvironmentVariable(EnvVar.Key);
                if (CurrentVar == null)
                {
                    var NewVar = String.Format(EnvVar.Value, ExecutablesPath, app.Application, LocalStoragePath);
                    Environment.SetEnvironmentVariable(EnvVar.Key, NewVar);
                }
            }

            var SysPath = Environment.GetEnvironmentVariable("PATH");

            var PathVar = String.Join(";", MayaParameters.PathVariables.ToArray());
            PathVar = String.Format(PathVar, ExecutablesPath, app.Application, LocalStoragePath);

            Environment.SetEnvironmentVariable("PATH", string.Format(@"{0};{1}", SysPath, PathVar)); 
        }

        
    }
}
