using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Maya.Cloud.Plugins;
using Maya.Cloud.Settings;
using Microsoft.Azure.Batch.Apps.Cloud;

namespace Maya.Cloud
{
    internal class MayaEnvironment
    {
        private readonly string _localpath;
        private readonly string _exeroot;
        private readonly string _exepath;
        private readonly string _userdir;
        private readonly IList<MayaPlugin> _plugins;

        private readonly ILog _log;

        private readonly string _executable = @"{0}\bin\render.exe";

        private readonly string _command =
            @"-renderer {0} -log ""{1}.log"" -proj ""{2}"" -preRender ""renderPrep"" -rd ""{2}"" -im ""{3}"" -s {4} -e {4} ";

        private static readonly IDictionary<string, Func<string, MayaPlugin>> _pluginMap = new Dictionary<string, Func<string, MayaPlugin>>
        {
            { "Arnold", (version) => new Arnold(version) },
            { "Yeti", (version) => new Yeti(version) },
            { "MentalRay", (version) => new MentalRay(version) },
        };

        private readonly IList<string> _pathVariables = new List<string>
        {
            @"{0}\bin;",
            @"{0}\plug-ins\substance\bin;",
            @"{0}\plug-ins\xgen\bin;",
            @"{0}\plug-ins\bifrost\bin;"
        };

        private readonly IDictionary<string, string> _envVariables = new Dictionary<string, string> { { "MAYA_APP_DIR", @"{0}" } };

        private readonly IDictionary<string, string> _mayaEnvVariables = new Dictionary<string, string>
        {
            { "MAYA_MODULE_PATH", @"{0}\{3}\modules;{1}\{4}\modules;{0}\Common Files\Autodesk Shared\Modules\maya\{5}" },
            { "FBX_LOCATION", @"{0}\{3}\plug-ing\fbx\" },
            { "MAYA_SCRIPT_BASE", @"{0}\{3}" },
            { "TEMP", @"{2}" },
            { "TMP", @"{2}" },
            { "MAYA_LOCATION", @"{0}\{3}" },
            { "TMPDIR", @"{2}" },
            { "MAYA_PLUG_IN_PATH", @"{0}\{3}\bin\plug-ins;{0}\{3}\plug-ins\bifrost\plug-ins;{0}\{3}\plug-ins\fbx\plug-ins;{0}\{3}\plug-ins\substance\plug-ins;{0}\{3}\plug-ins\xgen\plug-ins;" },
            { "PYTHONHOME", @"{0}\{3}\Python" },
            { "XGEN_LOCATION", @"{0}\{3}\plug-ins\xgen\" },
            { "SUBSTANCES_LOCATION", @"{0}\{3}\plug-ins\substance\substances" },
            { "BIFROST_LOCATION", @"{0}\{3}\plug-ins\bifrost\" },
            { "PYTHONPATH", @"{0}\{3}\plug-ins\bifrost\scripts\presets;{0}\{3}\plug-ins\bifrost\scripts;{0}\{3}\plug-ins\fbx\scripts;{0}\{3}\plug-ins\substance\scripts;{0}\{3}\plug-ins\xgen\scripts\cafm;{0}\{3}\plug-ins\xgen\scripts\xgenm;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui;{0}\{3}\plug-ins\xgen\scripts\xgenm\xmaya;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\brushes;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\dialogs;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\fxmodules;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\tabs;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\util;{0}\{3}\plug-ins\xgen\scripts\xgenm\ui\widgets;{0}\{3}\plug-ins\xgen\scripts;" },
            { "ILMDIR", @"{0}\Common Files\Autodesk Shared\Materials" },
            { "MAYA_SCRIPT_PATH", @"{0}\{3}\scripts;{0}\{3}\scripts\startup;{0}\{3}\scripts\others;{0}\{3}\scripts\AETemplates;{0}\{3}\scripts\unsupported;{0}\{3}\scripts\paintEffects;{0}\{3}\scripts\fluidEffects;{0}\{3}\scripts\hair;{0}\{3}\scripts\cloth;{0}\{3}\scripts\live;{0}\{3}\scripts\fur;{0}\{3}\scripts\muscle;{0}\{3}\scripts\turtle;{0}\{3}\scripts\FBX;{0}\{3}\scripts\mayaHIK;{0}\{3}\plug-ins\bifrost\scripts\presets;{0}\{3}\plug-ins\bifrost\scripts;{0}\{3}\plug-ins\fbx\scripts;{1}\{4}\scripts;" },
            { "MAYA_PLUGIN_RESOURCE_PATH", @"{0}\{3}\plug-ins\bifrost\resources;{0}\{3}\plug-ins\fbx\resources;{0}\{3}\plug-ins\substance\resources;{0}\{3}\plug-ins\xgen\resources;" },
            { "MAYA_PRESET_PATH", @"{0}\{3}\plug-ins\bifrost\presets;{0}\{3}\plug-ins\fbx\presets;{0}\{3}\plug-ins\substance\presets;{0}\{3}\plug-ins\xgen\presets;{1}\{4}\presets;" },
            { "XBMLANGPATH", @"{0}\{3}\plug-ins\bifrost\" }
        };

        public MayaEnvironment(MayaParameters appParams, string localpath, string exeRoot, int taskId, int frameNumber, ILog Log)
        {
            _log = Log;
            _localpath = localpath;
            _exeroot = exeRoot;
            _exepath = string.Format(@"{0}\{1}", exeRoot, appParams.ApplicationSettings.Application);
            _userdir = Path.Combine(_localpath, appParams.ApplicationSettings.UserDirectory);

            _executable = string.Format(_executable, _exepath);
            _plugins = new List<MayaPlugin>();

            foreach (var plugin in appParams.EnvironmentSettings.Plugins)
            {
                _log.Info("Using plugin: {0}", plugin);
                _plugins.Add(_pluginMap[plugin](appParams.ApplicationSettings.Version));
            }

            _log.Info("Env paths: {0}, {1}, {2}, {3}, {4}", _localpath, _exeroot, _exepath, _executable, _plugins.Count);

            SetLicense(appParams.EnvironmentSettings, appParams.ApplicationSettings.Adlm);
            SetEnvVariables(appParams.EnvironmentSettings);
            SetWorkspace(appParams.ApplicationSettings);
            CreateMayaEnv(appParams.ApplicationSettings);
            CreatePreRenderScript(appParams.ApplicationSettings, appParams.EnvironmentSettings);

            foreach (var plugin in _plugins)
            {
                _command += plugin.Command;
            }

            _command = string.Format(_command, appParams.Renderer, taskId, localpath, appParams.OutputName, frameNumber);
        }

        public string Command
        {
            get
            {
                return _command;
            }
        }

        public string Executable
        {
            get
            {
                return _executable;
            }
        }

        private void SetLicense(EnvironmentSettings envSettings, string adlm)
        {
            var license = Path.Combine(_exepath, "bin", "License.env");
            var licensePath = Path.Combine(_exeroot, "Adlm");
            if (!File.Exists(license))
            {
                var formattedLicEnv = string.Format(MayaScripts.license_env, _exeroot);
                using (var licFile = new StreamWriter(license))
                {
                    licFile.Write(formattedLicEnv);
                }
            }

            if (envSettings.LicenseServer != string.Empty && envSettings.LicensePort != string.Empty)
            {
                var licenseServer = Path.Combine(_localpath, "LICPATH.LIC");
                licensePath = _localpath;
                if (!File.Exists(licenseServer))
                {
                    var formattedLic = string.Format(MayaScripts.license, envSettings.LicenseServer, envSettings.LicensePort);
                    using (var licFile = new StreamWriter(licenseServer))
                    {
                        licFile.Write(formattedLic);
                    }
                }
            }

            var client = Path.Combine(_exeroot, "Adlm", "AdlmThinClientCustomEnv.xml");
            if (!File.Exists(client))
            {
                var formattedClient = string.Format(MayaScripts.client, _exeroot, adlm, licensePath);
                using (var clientFile = new StreamWriter(client))
                {
                    clientFile.Write(formattedClient);
                }
            }
        }

        private void SetEnvVariables(EnvironmentSettings envSettings)
        {
            var pathVar = string.Join("", _pathVariables.ToArray());
            pathVar = string.Format(pathVar, _exepath);
            _log.Info("PathVar: {0}", pathVar);

            Dictionary<string, string> formattedVars = new Dictionary<string, string>();
            foreach (var env in _envVariables)
            {
                formattedVars[env.Key] = string.Format(env.Value, _localpath);
                _log.Info("Formatting env var: {0}, {1}", env.Key, formattedVars[env.Key]);
            }

            foreach (var plugin in _plugins)
            {
                plugin.SetupEnv(formattedVars, _exeroot, _localpath);
                pathVar += plugin.SetupPath(_exeroot, _localpath);
            }

            _log.Info("Updated PathVar: {0}", pathVar);
            foreach (var envVar in formattedVars)
            {
                _log.Info("Checking env var: {0}", envVar.Key);
                var currentVar = Environment.GetEnvironmentVariable(envVar.Key);
                if (currentVar == null)
                {
                    _log.Info("Setting to {0}", envVar.Value);
                    Environment.SetEnvironmentVariable(envVar.Key, envVar.Value);
                }
            }

            foreach (var customEnvVar in envSettings.EnvVariables)
            {
                _log.Info("Checking custom env var: {0}", customEnvVar.Key);
                var currentVar = Environment.GetEnvironmentVariable(customEnvVar.Key);
                if (currentVar == null)
                {
                    _log.Info("Setting to {0}", FormatCustomEnvVar(customEnvVar.Value.ToString()));
                    Environment.SetEnvironmentVariable(customEnvVar.Key, FormatCustomEnvVar(customEnvVar.Value.ToString()));
                }
            }

            var sysPath = Environment.GetEnvironmentVariable("PATH");
            _log.Info("Setting path to {0}", string.Format(@"{0};{1}", sysPath, pathVar));
            Environment.SetEnvironmentVariable("PATH", string.Format(@"{0};{1}", sysPath, pathVar));
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

            if (!Directory.Exists(_userdir))
            {
                Directory.CreateDirectory(_userdir);
            }

            var scriptDir = Path.Combine(_userdir, "scripts");
            if (!Directory.Exists(scriptDir))
            {
                Directory.CreateDirectory(scriptDir);
            }

            var modDir = Path.Combine(_userdir, "modules");
            if (!Directory.Exists(modDir))
            {
                Directory.CreateDirectory(modDir);
            }

            foreach (var plugin in _plugins)
            {
                plugin.CreateModFile(_exeroot, modDir);
            }

            _log.Info("Created mod file: {0}", File.Exists(Path.Combine(modDir, "mtoa.mod")));
        }

        private void CreateMayaEnv(ApplicationSettings app)
        {
            Dictionary<string, string> formattedMayaVars = new Dictionary<string, string>();

            foreach (var env in _mayaEnvVariables)
            {
                formattedMayaVars[env.Key] = string.Format(
                    env.Value,
                    _exeroot,
                    _localpath,
                    Path.GetTempPath(),
                    app.Application,
                    app.UserDirectory,
                    app.Version);

                _log.Info("Formatted Maya env var: {0}, {1}", env.Key, formattedMayaVars[env.Key]);
            }

            foreach (var plugin in _plugins)
            {
                plugin.SetupMayaEnv(formattedMayaVars, _exeroot, _localpath);
            }

            var envPath = Path.Combine(_userdir, "Maya.env");
            if (!File.Exists(envPath))
            {
                using (var envFile = new StreamWriter(envPath))
                {
                    foreach (var variable in formattedMayaVars)
                    {
                        _log.Info("Writing to env file: {0}", string.Format("{0} = {1}", variable.Key, variable.Value));
                        envFile.WriteLine(string.Format("{0} = {1}", variable.Key, variable.Value));
                    }
                }
            }
        }

        private void CreatePreRenderScript(ApplicationSettings app, EnvironmentSettings env)
        {
            var scriptPath = Path.Combine(_localpath, app.UserDirectory, "scripts", "renderPrep.mel");
            var remappedPaths = env.PathMaps;
            var pathsScript = "";

            if (File.Exists(scriptPath))
            {
                return;
            }

            string formattedScript;

            if (remappedPaths.Count > 0)
            {
                foreach (var p in remappedPaths)
                {
                    pathsScript += string.Format("dirmap -m \"{0}\" \"{1}\";\n", p, _localpath.Replace('\\', '/'));
                }

                formattedScript = string.Format(MayaScripts.render_prep, "dirmap -en true;", pathsScript);
            }
            else
            {
                formattedScript = string.Format(MayaScripts.render_prep, string.Empty, string.Empty);
            }

            using (var scriptFile = new StreamWriter(scriptPath))
            {
                scriptFile.Write(formattedScript);

                foreach (var plugin in _plugins)
                {
                    plugin.PreRenderScript(scriptFile, _exepath, _localpath);
                }

                scriptFile.WriteLine("}");
            }
        }

        private string FormatCustomEnvVar(string envVar)
        {
            string formattedvar = envVar.Replace("<storage>", _localpath);
            formattedvar = formattedvar.Replace("<maya_root>", _exepath);
            formattedvar = formattedvar.Replace("<user_scripts>", Path.Combine(_userdir, "scripts"));
            formattedvar = formattedvar.Replace("<user_modules>", Path.Combine(_userdir, "modules"));
            formattedvar = formattedvar.Replace("<temp_dir>", Path.GetTempPath());
            return formattedvar;
        }
    }
}
