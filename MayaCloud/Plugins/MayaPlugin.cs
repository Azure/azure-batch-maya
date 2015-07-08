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
using System.IO;
using System.Linq;

namespace Maya.Cloud.Plugins
{
    public abstract class MayaPlugin
    {
        public abstract string ExePath { get; }

        public abstract string Command { get; }

        public abstract IDictionary<string, string> EnvVariables { get; }

        public abstract IDictionary<string, string> MayaEnvVariables { get; }

        public abstract IList<string> PathVariables { get; }

        public virtual void CreateModFile(string exeRoot, string location)
        {
        }

        public virtual void SetupEnv(IDictionary<string, string> env, string exeRoot, string localpath)
        {
        }

        public virtual void SetupMayaEnv(IDictionary<string, string> mayaEnv, string exeRoot, string localpath)
        {
        }

        public virtual void PreRenderScript(StreamWriter script, string exeRoot, string localPath)
        {
        }

        public virtual string SetupPath(string exeRoot, string localpath)
        {
            return string.Empty;
        }

        protected static IDictionary<string, string> MergeParameters(
            IDictionary<string, string> basedict,
            IDictionary<string, string> mergedict)
        {
            foreach (var item in mergedict)
            {
                if (!basedict.ContainsKey(item.Key))
                {
                    basedict.Add(item.Key, item.Value);
                }
                else
                {
                    basedict[item.Key] = basedict[item.Key] + mergedict[item.Key];
                }
            }

            return basedict;
        }
    }
}
