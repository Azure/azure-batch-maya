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
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using Microsoft.Azure.Batch.Apps.Cloud;

namespace Maya.Cloud
{
    public abstract class MayaParameters
    {
        public static readonly IList<String> SupportedFormats = new List<String> { ".png", ".bmp", ".jpg", ".tga", ".exr" };

        public abstract bool Valid { get; }

        public abstract int Start { get; }

        public abstract int End { get; }

        public abstract MayaSettings Settings { get; }

        public abstract string JobFile { get; }

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
        public static MayaParameters FromTask(ITask task)
        {
            var errors = new List<string>();

            string jobfile = GetStringParameter(task.Parameters, "jobfile", errors);
            string engine = GetStringParameter(task.Parameters, "engine", errors);
            MayaSettings settings = GetSettingsParameter(task.Parameters, "settings", errors);
            
            if (errors.Any())
            {
                return new InvalidMayaParameters(string.Join(Environment.NewLine, errors.Select(e => "* " + e)));
            }

            return new ValidMayaParameters(jobfile, engine, settings);
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

        private static MayaSettings GetSettingsParameter(IDictionary<string, string> parameters, string parameterName, List<string> errors)
        {
            var jsonSettings = GetStringParameter(parameters, parameterName, errors);
            var settings = new MayaSettings();

            try
            {
                DataContractJsonSerializer ser = new DataContractJsonSerializer(typeof(MayaSettings));
                MemoryStream stream = new MemoryStream(Encoding.UTF8.GetBytes(jsonSettings));
                settings = (MayaSettings)ser.ReadObject(stream);
            }
            catch (Exception ex)
            {
                errors.Add("Error deserializing json settings: " + ex.Message);
            }
            return settings;
        }

        [DataContract]
        public class MayaSettings
        {
            [DataMember]
            public List<string> PathMaps { get; set; }
        }


        private class ValidMayaParameters : MayaParameters
        {
            private readonly int _start;
            private readonly int _end;
            private readonly string _jobfile;
            private readonly string _renderer;
            private readonly MayaSettings _settings;

            public ValidMayaParameters(int start, int end, string jobfile, string engine)
            {
                _start = start;
                _end = end;
                _jobfile = jobfile;
                _renderer = engine;
            }

            public ValidMayaParameters(string jobfile, string engine, MayaSettings settings)
            {
                _jobfile = jobfile;
                _renderer = engine;
                _settings = settings;
            }

            public override bool Valid
            {
                get { return true; }
            }

            public override int Start
            {
                get { return _start; }
            }

            public override int End
            {
                get { return _end; }
            }

            public override string JobFile
            {
                get { return _jobfile; }
            }

            public override string Renderer
            {
                get { return _renderer; }
            }

            public override MayaSettings Settings
            {
                get { return _settings; }
            }

            public override string ErrorText
            {
                get { throw new InvalidOperationException("ErrorText does not apply to valid parameters"); }
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
                get { return false; }
            }

            public override int Start
            {
                get { throw new InvalidOperationException("Start does not apply to invalid parameters"); }
            }

            public override int End
            {
                get { throw new InvalidOperationException("End does not apply to invalid parameters"); }
            }

            public override string JobFile
            {
                get { throw new InvalidOperationException("JobFile does not apply to invalid parameters"); }
            }

            public override string Renderer
            {
                get { throw new InvalidOperationException("Renderer does not apply to invalid parameters"); }
            }

            public override MayaSettings Settings
            {
                get { throw new InvalidOperationException("Settings does not apply to invalid parameters"); }
            }

            public override string ErrorText
            {
                get { return _errorText; }
            }
        }
    }
}
