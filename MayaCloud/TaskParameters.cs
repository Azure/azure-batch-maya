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
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Maya.Cloud.Settings;
using Microsoft.Azure.Batch.Apps.Cloud;
using Newtonsoft.Json;

namespace Maya.Cloud
{
    public abstract class MayaParameters
    {
        public static readonly IList<string> ThumbFormats = new List<string> { ".png", ".bmp", ".jpg", ".tga", ".exr" };

        public abstract bool Valid { get; }

        public abstract int Start { get; }

        public abstract int End { get; }

        public abstract ApplicationSettings ApplicationSettings { get; }

        public abstract EnvironmentSettings EnvironmentSettings { get; }

        public abstract string JobFile { get; }

        public abstract string OutputName { get; }

        public abstract string Renderer { get; }

        public abstract string ErrorText { get; }

        public static MayaParameters FromJob(IJob job)
        {
            var errors = new List<string>();

            int start = GetInt32Parameter(job.Parameters, "start", errors);
            int end = GetInt32Parameter(job.Parameters, "end", errors);

            string jobfile = GetStringParameter(job.Parameters, "jobfile", errors);
            string engine = GetStringParameter(job.Parameters, "engine", errors);

            if (errors.Any())
            {
                return new InvalidMayaParameters(string.Join(Environment.NewLine, errors.Select(e => "* " + e)));
            }

            return new ValidMayaParameters(start, end, jobfile, engine);
        }

        public static MayaParameters FromTask(ITask task, String applicationpath)
        {
            var errors = new List<string>();

            string jobfile = GetStringParameter(task.Parameters, "jobfile", errors);
            string engine = GetStringParameter(task.Parameters, "engine", errors);
            string filename = GetStringParameter(task.Parameters, "prefix", errors);

            EnvironmentSettings envsettings = GetSettingsParameter(task.Parameters, "settings", errors);
            ApplicationSettings appsettings = GetApplicationSettings(Path.Combine(applicationpath, "app.config"), errors);
            
            if (errors.Any())
            {
                return new InvalidMayaParameters(string.Join(Environment.NewLine, errors.Select(e => "* " + e)));
            }

            return new ValidMayaParameters(jobfile, engine, filename, envsettings, appsettings);
        }

        private static int GetInt32Parameter(IDictionary<string, string> parameters, string parameterName, List<string> errors)
        {
            int value = 0;
            try
            {
                string text = parameters[parameterName];
                value = int.Parse(text, CultureInfo.InvariantCulture);
                if (value < 0)
                {
                    errors.Add(parameterName + " parameter is not a positive integer");
                }
            }
            catch (KeyNotFoundException)
            {
                errors.Add(parameterName + " parameter not specified");
            }
            catch (FormatException)
            {
                errors.Add(parameterName + " parameter is not a valid integer");
            }
            catch (Exception ex)
            {
                errors.Add("Unexpected error reading parameter " + parameterName + ": " + ex.Message);
            }
            return value;
        }

        private static string GetStringParameter(IDictionary<string, string> parameters, string parameterName, List<string> errors)
        {
            string text = "";
            try
            {
                text = parameters[parameterName];
            }
            catch (KeyNotFoundException)
            {
                errors.Add(parameterName + " parameter not specified");
            }
            catch (Exception ex)
            {
                errors.Add("Unexpected error reading parameter " + parameterName + ": " + ex.Message);
            }
            return text;
        }

        private static EnvironmentSettings GetSettingsParameter(
            IDictionary<string, string> parameters,
            string parameterName,
            List<string> errors)
        {
            var jsonSettings = GetStringParameter(parameters, parameterName, errors);
            var settings = new EnvironmentSettings();

            
            try
            {
                settings = JsonConvert.DeserializeObject<EnvironmentSettings>(jsonSettings);
            }
            catch (Exception ex)
            {
                errors.Add("Error deserializing json environment settings: " + ex.Message);
            }
            return settings;
        }

        private static ApplicationSettings GetApplicationSettings(String configfile, List<string> errors)
        {
            var settings = new ApplicationSettings();
            if (!(File.Exists(configfile)))
            {
                errors.Add("No config file found on the Application Image");
                return settings;
            }

            try
            {
                settings = JsonConvert.DeserializeObject<ApplicationSettings>(File.ReadAllText(configfile));
            }
            catch (Exception ex)
            {
                errors.Add("Error deserializing json application settings: " + ex.Message);
            }
            return settings;
        }
        

        private class ValidMayaParameters : MayaParameters
        {
            private readonly int _start;
            private readonly int _end;
            private readonly string _jobfile;
            private readonly string _renderer;
            private readonly string _output;
            private readonly EnvironmentSettings _env_settings;
            private readonly ApplicationSettings _app_settings;

            public ValidMayaParameters(int start, int end, string jobfile, string engine)
            {
                _start = start;
                _end = end;
                _jobfile = jobfile;
                _renderer = engine;
            }

            public ValidMayaParameters(string jobfile, string engine, string output,
                EnvironmentSettings envsettings, ApplicationSettings appsettings)
            {
                _jobfile = jobfile;
                _renderer = engine;
                _output = output;
                _env_settings = envsettings;
                _app_settings = appsettings;
            }

            public override bool Valid
            {
                get
                {
                    return true;
                }
            }

            public override int Start
            {
                get
                {
                    return _start;
                }
            }

            public override int End
            {
                get
                {
                    return _end;
                }
            }

            public override string JobFile
            {
                get
                {
                    return _jobfile;
                }
            }

            public override string Renderer
            {
                get
                {
                    return _renderer;
                }
            }

            public override string OutputName
            {
                get { return _output; }
            }

            public override ApplicationSettings ApplicationSettings
            {
                get { return _app_settings; }
            }

            public override EnvironmentSettings EnvironmentSettings
            {
                get
                {
                    return _env_settings;
                }
            }

            public override string ErrorText
            {
                get
                {
                    throw new InvalidOperationException("ErrorText does not apply to valid parameters");
                }
            }
        }

        private class InvalidMayaParameters : MayaParameters
        {
            private readonly string _errorText;

            public InvalidMayaParameters(string errorText)
            {
                _errorText = errorText;
            }

            public override bool Valid
            {
                get
                {
                    return false;
                }
            }

            public override int Start
            {
                get
                {
                    throw new InvalidOperationException("Start does not apply to invalid parameters");
                }
            }

            public override int End
            {
                get
                {
                    throw new InvalidOperationException("End does not apply to invalid parameters");
                }
            }

            public override string JobFile
            {
                get
                {
                    throw new InvalidOperationException("JobFile does not apply to invalid parameters");
                }
            }

            public override string Renderer
            {
                get
                {
                    throw new InvalidOperationException("Renderer does not apply to invalid parameters");
                }
            }

            public override string OutputName
            {
                get { throw new InvalidOperationException("OutputName does not apply to invalid parameters"); }
            }

            public override EnvironmentSettings EnvironmentSettings
            {
                get { throw new InvalidOperationException("EnvironmentSettings does not apply to invalid parameters"); }
            }

            public override ApplicationSettings ApplicationSettings
            {
                get
                {
                    throw new InvalidOperationException("ApplicationSettings does not apply to invalid parameters");
                }
            }

            public override string ErrorText
            {
                get
                {
                    return _errorText;
                }
            }
        }
    }
}
