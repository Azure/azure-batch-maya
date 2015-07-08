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
using System.Linq;
using Maya.Cloud.Exceptions;
using Microsoft.Azure.Batch.Apps.Cloud;

namespace Maya.Cloud
{
    class MayaJobSplitter : JobSplitter
    {
        /// <summary>
        /// Splits a job into more granular tasks to be processed in parallel.
        /// </summary>
        /// <param name="job">The job to be split.</param>
        /// <param name="settings">Contains information and services about the split request.</param>
        /// <returns>A sequence of tasks to be run on compute nodes.</returns>
        protected override IEnumerable<TaskSpecifier> Split(IJob job, JobSplitSettings settings)
        {
            var jobParameters = MayaParameters.FromJob(job);
            if (!jobParameters.Valid)
            {
                Log.Error(jobParameters.ErrorText);
                throw new InvalidParameterException(jobParameters.ErrorText);
            }

            job.Parameters["settings"] = job.JobSettings;

            for (var i = jobParameters.Start; i <= jobParameters.End; i++)
            {
                yield return new TaskSpecifier
                {
                    TaskIndex = i,
                    Parameters = job.Parameters,
                    RequiredFiles = job.Files,
                };

            }

        }
    }
}
