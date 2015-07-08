//--------------------------------------------------------------------------
//
// Maya Batch C# Cloud Assemblies 
// 
// Copyright (c) Microsoft Corporation.  All rights reserved. 
// 
// MIT License
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy 
// of this software and associated documentation files (the ""Software""), to deal 
// in the Software without restriction, including without limitation the rights 
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
// copies of the Software, and to permit persons to whom the Software is furnished 
// to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in 
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
// THE SOFTWARE.
// 
//--------------------------------------------------------------------------

using System;
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
                    modFile.WriteLine("+ mtoa any {0}\\{1}", exeRoot, ExePath);
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
