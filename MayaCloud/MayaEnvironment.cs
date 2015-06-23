﻿using System;
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
        private string _exeroot;
        private string _exepath;
        private IList<MayaPlugin> _plugins;

        public ILog log;

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

        private IDictionary<String, String> MayaEnvVariables = new Dictionary<String, String> { { "MAYA_MODULE_PATH", @"{0}\{3}\modules;{1}\{4}\modules;{0}\Common Files\Autodesk Shared\Modules\maya\{5}" },
                                                                                                { "FBX_LOCATION", @"{0}\{3}\plug-ing\fbx\" },
                                                                                                { "MAYA_SCRIPT_BASE", @"{0}\{3}" },
                                                                                                { "TEMP", @"{2}" },
                                                                                                { "TMP", @"{2}" },
                                                                                                { "MAYA_LOCATION", @"{0}\{3}" },
                                                                                                { "TMPDIR", @"{2}" },
                                                                                                { "MAYA_PLUG_IN_PATH", @"{0}\{3}\bin\plug-ins;{0}\{3}\plug-ins\bifrost\plug-ins;{0}\{3}\plug-ins\fbx\plug-ins;{0}\{3}\plug-ins\substance\plug-ins;{0}\{3}\plug-ins\xgen\plug-ins;{1};" },
                                                                                                { "PYTHONHOME", @"{0}\{3}\Python" },
                                                                                                { "XGEN_LOCATION", @"{0}\{3}\plug-ins\xgen\" },
                                                                                                { "SUBSTANCES_LOCATION", @"{0}\{3}\plug-ins\substance\substances" },
                                                                                                { "BIFROST_LOCATION", @"{0}\{3}\plug-ins\bifrost\" },
                                                                                                { "PYTHONPATH", @"{0}\{3}\plug-ins\bifrost\scripts\presets;{0}\{3}\plug-ins\bifrost\scripts;{0}\{3}\plug-ins\fbx\scripts;{0}\{3}\plug-ins\substance\scripts;{0}\{3}\plug-ins\xgen\scripts\cafm;{0}\{3}\plug-ins\xgen\scripts\xgenm;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui;{0}\{3}\plug-ins\xgen\scripts\xgenm\xmaya;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\brushes;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\dialogs;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\fxmodules;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\tabs;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\util;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\widgets;{0}\{3}\plug-ins\xgen\scripts;" },
                                                                                                { "ILMDIR", @"{0}\Common Files\Autodesk Shared\Materials" },
                                                                                                { "MAYA_SCRIPT_PATH", @"{0}\{3}\scripts;{0}\{3}\scripts\startup;{0}\{3}\scripts\others;{0}\{3}\scripts\AETemplates;{0}\{3}\scripts\unsupported;{0}\{3}\scripts\paintEffects;{0}\{3}\scripts\fluidEffects;{0}\{3}\scripts\hair;{0}\{3}\scripts\cloth;{0}\{3}\scripts\live;{0}\{3}\scripts\fur;{0}\{3}\scripts\muscle;{0}\{3}\scripts\turtle;{0}\{3}\scripts\FBX;{0}\{3}\scripts\mayaHIK;{0}\{3}\plug-ins\bifrost\scripts\presets;{0}\{3}\plug-ins\bifrost\scripts;{0}\{3}\plug-ins\fbx\scripts;{1};" },
                                                                                                { "MAYA_PLUGIN_RESOURCE_PATH", @"{0}\{3}\plug-ins\bifrost\resources;{0}\{3}\plug-ins\fbx\resources;{0}\{3}\plug-ins\substance\resources;{0}\{3}\plug-ins\xgen\resources;{1}" },
                                                                                                { "MAYA_PRESET_PATH", @"{0}\{3}\plug-ins\bifrost\presets;{0}\{3}\plug-ins\fbx\presets;{0}\{3}\plug-ins\substance\presets;{0}\{3}\plug-ins\xgen\presets" },
                                                                                                { "XBMLANGPATH", @"{0}\{3}\plug-ins\bifrost\" }};

        public MayaEnvironment(MayaParameters AppParams, string Localpath, string ExeRoot, int TaskID, int FrameNumber, ILog Log)
        {
            log = Log;
            _localpath = Localpath;
            _exeroot = ExeRoot;
            _exepath = String.Format(@"{0}\{1}", ExeRoot, AppParams.ApplicationSettings.Application);

            _executable = String.Format(_executable, _exepath);
            _plugins = new List<MayaPlugin>();

            foreach (var plugin in AppParams.PluginSettings.Plugins)
                _plugins.Add(PluginMap[plugin](AppParams.ApplicationSettings.Version));

            log.Info("Env paths: {0}, {1}, {2}, {3}, {4}", _localpath, _exeroot, _exepath, _executable, _plugins.Count);

            SetLicense(AppParams.ApplicationSettings.Adlm);
            SetEnvVariables();
            SetWorkspace(AppParams.ApplicationSettings);
            CreateMayaEnv(AppParams.ApplicationSettings);
            CreatePreRenderScript(AppParams.ApplicationSettings, AppParams.RenderSettings);

            foreach (var plugin in _plugins)
                _command += plugin.Command;

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

        private void SetLicense(string Adlm)
        {
            var license = Path.Combine(_exepath, "bin",  "License.env");
            if (!File.Exists(license))
            {
                var formattedLic = string.Format(MayaScripts.lic, _exeroot);
                using (var licFile = new StreamWriter(license))
                {
                    licFile.Write(formattedLic);
                }
            }

            var client = Path.Combine(_exeroot, "Adlm", "AdlmThinClientCustomEnv.xml");
            if (!File.Exists(client))
            {
                var formattedClient = string.Format(MayaScripts.client, _exeroot, Adlm);
                using (var clientFile = new StreamWriter(client))
                {
                    clientFile.Write(formattedClient);
                }
            }
        }

        private void SetEnvVariables()
        {
            var PathVar = String.Join("", PathVariables.ToArray());
            PathVar = String.Format(PathVar, _exepath);
            log.Info("PathVar: {0}", PathVar);

            Dictionary<string, string> formattedVars = new Dictionary<string, string>();
            foreach (var env in EnvVariables)
            {
                formattedVars[env.Key] = String.Format(env.Value, _localpath);
                log.Info("Formatting env var: {0}, {1}", env.Key, formattedVars[env.Key]);
            }

            foreach (var plugin in _plugins)
            {
                plugin.SetupEnv(formattedVars, _exeroot, _localpath);
                PathVar += plugin.SetupPath(_exeroot, _localpath);
            }

            log.Info("Updated PathVar: {0}", PathVar);
            foreach (var EnvVar in formattedVars)
            {
                log.Info("Checking env var: {0}", EnvVar.Key);
                var CurrentVar = Environment.GetEnvironmentVariable(EnvVar.Key);
                if (CurrentVar == null)
                    log.Info("Setting to {0}", EnvVar.Value);
                    Environment.SetEnvironmentVariable(EnvVar.Key, EnvVar.Value);
            }

            var SysPath = Environment.GetEnvironmentVariable("PATH");
            log.Info("Setting path to {0}", string.Format(@"{0};{1}", SysPath, PathVar));
            Environment.SetEnvironmentVariable("PATH", string.Format(@"{0};{1}", SysPath, PathVar)); 
        }

        private void SetWorkspace(ApplicationSettings app)
        {

            var project = Path.Combine(_localpath, "workspace.mel");
            if (!File.Exists(project))
            {
                using (StreamWriter workspace = new StreamWriter(project))
                {
                    workspace.Write(MayaScripts.workspace);
                }
            }

            var userDir = Path.Combine(_localpath, app.UserDirectory);
            if (!Directory.Exists(userDir))
            {
                Directory.CreateDirectory(userDir);
            }

            var scriptDir = Path.Combine(userDir, "scripts");
            if (!Directory.Exists(scriptDir))
            {
                Directory.CreateDirectory(scriptDir);
            }

            var modDir = Path.Combine(userDir, "modules");
            if (!Directory.Exists(modDir))
            {
                Directory.CreateDirectory(modDir);
            }

            foreach (var plugin in _plugins)
                plugin.CreateModFile(_exeroot, modDir);

            log.Info("Created mod file: {0}", File.Exists(Path.Combine(modDir, "mtoa.mod")));
                
        }

        private void CreateMayaEnv(ApplicationSettings app)
        {
            var userDir = Path.Combine(_localpath, app.UserDirectory);
            Dictionary<string, string> formattedMayaVars = new Dictionary<string, string>();

            foreach (var env in MayaEnvVariables)
            {
                formattedMayaVars[env.Key] = String.Format(env.Value, _exeroot, _localpath, Path.GetTempPath(),
                    app.Application, app.UserDirectory, app.Version);
                log.Info("Formatted Maya env var: {0}, {1}", env.Key, formattedMayaVars[env.Key]);
            }

            foreach (var plugin in _plugins)
                plugin.SetupMayaEnv(formattedMayaVars, _exeroot, _localpath);

            var envPath = Path.Combine(userDir, "Maya.env");
            if (!File.Exists(envPath))
            {
                using (var envFile = new StreamWriter(envPath))
                {
                    foreach (var variable in formattedMayaVars)
                    {
                        log.Info("Writing to env file: {0}", String.Format("{0} = {1}", variable.Key, variable.Value));
                        envFile.WriteLine(String.Format("{0} = {1}", variable.Key, variable.Value));
                    }
                }
            }

        }

        private void CreatePreRenderScript(ApplicationSettings app, RenderSettings render)
        {
            var scriptPath = Path.Combine(_localpath, app.UserDirectory, "scripts", "renderPrep.mel");
            var remappedPaths = render.PathMaps;
            var pathsScript = "";

            if (File.Exists(scriptPath))
                return;

            string formattedScript;

            if (remappedPaths.Count > 0)
            {
                foreach (var p in remappedPaths)
                    pathsScript += string.Format("dirmap -m \"{0}\" \"{1}\";\n", p, _localpath.Replace('\\', '/'));

                formattedScript = string.Format(MayaScripts.dirMap, "dirmap -en true;", pathsScript);
            }
            else
                formattedScript = string.Format(MayaScripts.dirMap, string.Empty, string.Empty);

            using (var scriptFile = new StreamWriter(scriptPath))
            {
                scriptFile.Write(formattedScript);

                foreach(var plugin in _plugins)
                    plugin.PreRenderScript(scriptFile, _exepath, _localpath);

                scriptFile.WriteLine("}");
            }

        }

        
    }
}