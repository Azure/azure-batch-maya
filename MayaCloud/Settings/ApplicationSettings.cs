///--------------------------------------------------------------------------
///
/// Maya Batch C# Cloud Assemblies 
/// 
/// Copyright (c) Microsoft Corporation.  All rights reserved. 
/// 
/// MIT License
/// 
/// Permission is hereby granted, free of charge, to any person obtaining a copy 
/// of this software and associated documentation files (the ""Software""), to deal 
/// in the Software without restriction, including without limitation the rights 
/// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
/// copies of the Software, and to permit persons to whom the Software is furnished 
/// to do so, subject to the following conditions:
/// 
/// The above copyright notice and this permission notice shall be included in 
/// all copies or substantial portions of the Software.
/// 
/// THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
/// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
/// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
/// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
/// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
/// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
/// THE SOFTWARE.
/// 
///--------------------------------------------------------------------------


using System;
using System.Collections.ObjectModel;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Globalization;
using System.Threading.Tasks;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using Microsoft.Azure.Batch.Apps.Cloud;
using System.IO;

namespace Maya.Cloud.Settings
{
    [DataContract]
    public class ApplicationSettings
    {
        [DataMember]
        public String Version { get; set; }

        [DataMember]
        public String Application { get; set; }

        [DataMember]
        public String UserDirectory { get; set; }

        [DataMember]
        public String Adlm { get; set; }


    }
}
