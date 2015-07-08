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
using System.Configuration;
using System.IO;
using System.Linq;
using System.Threading;
using System.Globalization;
using System.IO.Compression;
using Maya.Cloud.Exceptions;

using Microsoft.Azure.Batch.Apps.Cloud;
using System.Runtime.CompilerServices;

namespace Maya.Cloud
{
    public class MayaTaskProcessor : ParallelTaskProcessor
    {
        /// <summary>
        /// Path to the Maya executable
        /// </summary>
        private const string RenderPath = @"Maya2015\bin\render.exe";

        /// <summary>
        /// Args with which to run Maya
        /// </summary>
        private const string RenderArgs = @"-renderer {0} -log ""{1}"" -proj ""{2}"" -preRender ""dirMap"" -rd ""{3}"" -s {4} -e {4} ""{5}""";

        /// <summary>
        /// Executes the external process for processing the task
        /// </summary>
        /// <param name="task">The task to be processed.</param>
        /// <param name="settings">Contains information about the processing request.</param>
        /// <returns>The result of task processing.</returns>
        protected override TaskProcessResult RunExternalTaskProcess(ITask task, TaskExecutionSettings settings)
        {
            var taskParameters = MayaParameters.FromTask(task);
            var projDir = ConfigureMayaEnv(LocalStoragePath, ExecutablesPath);
            CreateMappingScript(taskParameters, LocalStoragePath);

            var initialFiles = CollectFiles(LocalStoragePath);

            if (!taskParameters.Valid)
            {
                Log.Error(taskParameters.ErrorText);
                return new TaskProcessResult
                {
                    Success = TaskProcessSuccess.PermanentFailure,
                    ProcessorOutput = "Parameter error: " + taskParameters.ErrorText,
                };
            }

            var inputFile = Path.Combine(LocalStoragePath, taskParameters.JobFile);
            var logFile = string.Format("{0}.log", task.TaskId);

            var externalProcessPath = ExecutablePath(RenderPath);
            var externalProcessArgs = string.Format(CultureInfo.InvariantCulture, RenderArgs, taskParameters.Renderer,
                logFile, LocalStoragePath, LocalStoragePath, task.TaskIndex, inputFile);

            Log.Info("Calling '{0}' with Args '{1}' for Task '{2}' / Job '{3}' .", RenderPath, externalProcessArgs, task.TaskId, task.JobId);
            var processResult = ExecuteProcess(externalProcessPath, externalProcessArgs);

            if (processResult == null)
            {
                if (File.Exists(logFile))
                    return new TaskProcessResult
                    {
                        Success = TaskProcessSuccess.PermanentFailure,
                        ProcessorOutput = File.ReadAllText(logFile)
                    };

                else
                    return new TaskProcessResult { Success = TaskProcessSuccess.PermanentFailure };
            }

            var newFiles = GetNewFiles(initialFiles, LocalStoragePath);
            var result = TaskProcessResult.FromExternalProcessResult(processResult, newFiles);
            if (File.Exists(logFile))
                result.ProcessorOutput = File.ReadAllText(logFile);

            var thumbnail = CreateThumbnail(task, newFiles);

            if (!string.IsNullOrEmpty(thumbnail))
            {
                var taskPreview = new TaskOutputFile
                {
                    FileName = thumbnail,
                    Kind = TaskOutputFileKind.Preview
                };
                result.OutputFiles.Add(taskPreview);
            }

            return result;
        }

        /// <summary>
        /// Method to execute the external processing for merging the tasks output into job output
        /// </summary>
        /// <param name="mergeTask">The merge task.</param>
        /// <param name="settings">Contains information about the processing request.</param>
        /// <returns>The job outputs resulting from the merge process.</returns>
        protected override JobResult RunExternalMergeProcess(ITask mergeTask, TaskExecutionSettings settings)
        {
            var inputFiles = CollectFiles(LocalStoragePath);
            FilterFiles(inputFiles);

            var outputFile = LocalPath("output.zip");
            var result = new JobResult();

            if (inputFiles.Count < 1)
            {
                throw new NoOutputsFoundException("No job outputs found.");
            }

            try
            {
                using (ZipArchive outputs = ZipFile.Open(outputFile, ZipArchiveMode.Create))
                {
                    foreach (var input in inputFiles)
                    {
                        outputs.CreateEntryFromFile(input, Path.GetFileName(input), CompressionLevel.Optimal);
                    }
                }

                result.OutputFile = outputFile;
            }
            catch (Exception ex)
            {
                var error = string.Format("Failed to zip outputs: {0}", ex.ToString());
                throw new ZipException(error, ex);
            }

            result.PreviewFile = CreateThumbnail(mergeTask, inputFiles.ToArray());
            return result;
        }

        private static string ConfigureMayaEnv(string cwd, string exe)
        {
            Environment.SetEnvironmentVariable("MAYA_APP_DIR", cwd);
            var sysPath = Environment.GetEnvironmentVariable("PATH");
            Environment.SetEnvironmentVariable("PATH", string.Format(@"{0};{1}\Maya2015\bin;{1}\mentalrayForMaya2015\bin", sysPath, exe));

            var project = Path.Combine(cwd, "workspace.mel");
            if (!File.Exists(project))
            {
                using (StreamWriter workspace = new StreamWriter(project))
                {
                    workspace.Write(MayaScripts.workspace);
                }
            }

            var license = Path.Combine(exe, "Maya2015", "bin", "License.env");
            if (!File.Exists(license))
            {
                var formattedLic = string.Format(MayaScripts.lic, exe);
                using (var licFile = new StreamWriter(license))
                {
                    licFile.Write(formattedLic);
                }
            }

            var client = Path.Combine(exe, "Adlm", "AdlmThinClientCustomEnv.xml");
            if (!File.Exists(client))
            {
                var formattedClient = string.Format(MayaScripts.client, exe);
                using (var clientFile = new StreamWriter(client))
                {
                    clientFile.Write(formattedClient);
                }
            }

            var envDir = Path.Combine(cwd, "2015-x64"); //TODO: Fix this to make the version depend on vhd version
            if (!Directory.Exists(envDir))
            {
                Directory.CreateDirectory(envDir);
            }

            var scriptDir = Path.Combine(envDir, "scripts");
            if (!Directory.Exists(scriptDir))
            {
                Directory.CreateDirectory(scriptDir);
            }

            var envPath = Path.Combine(envDir, "Maya.env");
            if (!File.Exists(envPath))
            {
                var formattedEnv = string.Format(MayaScripts.env, exe, cwd, Path.GetTempPath());
                using (var envFile = new StreamWriter(envPath))
                {
                    envFile.Write(formattedEnv);
                }
            }
                
            return project;
        }

        private void CreateMappingScript(MayaParameters parameters, string localPath)
        {
            var scriptPath = Path.Combine(localPath, "2015-x64", "scripts", "dirMap.mel");
            var remappedPaths = parameters.Settings.PathMaps;
            var pathsScript = "";
            if (!File.Exists(scriptPath) && remappedPaths.Count > 0)
            {
                foreach (var p in remappedPaths)
                {
                    pathsScript += string.Format("dirmap -m \"{0}\" \"{1}\";\n", p, localPath.Replace('\\', '/'));
                }
                var formattedScript = string.Format(MayaScripts.dirMap, pathsScript);

                using (var scriptFile = new StreamWriter(scriptPath))
                {
                    scriptFile.Write(formattedScript);
                }
            }

        }

        /// <summary>
        /// Retrieve a list of files that currently exist in a given location, according to a 
        /// given naming pattern.
        /// </summary>
        /// <param name="location">The directory to list the contents of.</param>
        /// <param name="pattern">The naming convention the returned files names adhere to.</param>
        /// <returns>A HashSet of the paths of the files in the directory.</returns>
        private static HashSet<string> CollectFiles(string location, string pattern = "*")
        {
            return new HashSet<string>(Directory.GetFiles(location, pattern, SearchOption.AllDirectories));
        }

        /// <summary>
        /// Performs a difference between the current contents of a directory and a supplied file list.
        /// </summary>
        /// <param name="oldFiles">Set of file paths to compare.</param>
        /// <param name="location">Path to the directory.</param>
        /// <returns>An array of files paths in the directory that do not appear in the supplied set.</returns>
        private static string[] GetNewFiles(HashSet<string> oldFiles, string location)
        {
            var filesNow = CollectFiles(location);
            filesNow.RemoveWhere(oldFiles.Contains);
            FilterFiles(filesNow);

            return filesNow.ToArray();
        }

        private static void FilterFiles(HashSet<string> fileSet)
        {
            fileSet.RemoveWhere(f => f.EndsWith(".temp"));
            fileSet.RemoveWhere(f => f.EndsWith(".stdout"));
            fileSet.RemoveWhere(f => f.EndsWith(".log"));
            fileSet.RemoveWhere(f => f.EndsWith(".xml"));
            fileSet.RemoveWhere(f => f.EndsWith("mayaLog"));
            fileSet.RemoveWhere(f => f.EndsWith(".mel"));
            fileSet.RemoveWhere(f => f.EndsWith(".gbtaskcompletion"));
        }

        /// <summary>
        /// Create an image thumbnail for the task. If supplied image format is incompatible, no thumb
        /// will be created and no error thrown.
        /// </summary>
        /// <param name="task">The task that needs a thumbnail.</param>
        /// <param name="inputs">The task output from which to generate the thumbnail.</param>
        /// <returns>The path to the new thumbnail if created, else an empty string.</returns>
        protected string CreateThumbnail(ITask task, string[] inputs)
        {
            var imagemagick = ExecutablePath(@"ImageMagick\convert.exe");
            if (!File.Exists(imagemagick))
            {
                Log.Info("ImageMagick not found. Skipping thumbnail creation.");
                return string.Empty;
            }

            var filtered = inputs.Where(x => MayaParameters.SupportedFormats.Contains(Path.GetExtension(x)));
            if (filtered.Count() < 1)
            {
                Log.Info("No thumbnail compatible images found.");
                return string.Empty;
            }

            var thumbInput = filtered.First();
            var thumbOutput = LocalPath(string.Format("{0}_{1}_thumbnail.png", task.JobId, task.TaskIndex));

            var process = new ExternalProcess
            {
                CommandPath = imagemagick,
                Arguments = string.Format(@"""{0}"" -thumbnail 200x150> ""{1}""", thumbInput, thumbOutput),
                WorkingDirectory = LocalStoragePath
            };

            try
            {
                process.Run();
            }
            catch (ExternalProcessException ex)
            {
                Log.Info("No thumbnail generated: {0}", ex);
                return string.Empty;
            }

            Log.Info("Generated thumbnail from {0} at {1}", Path.GetFileName(thumbInput), Path.GetFileName(thumbOutput));
            return thumbOutput;
        }

        /// <summary>
        /// Run a, executable with a given set of arguments.
        /// </summary>
        /// <param name="exePath">Path the executable.</param>
        /// <param name="exeArgs">The command line arguments.</param>
        /// <returns>The ExternalProcessResult if run successfully, or null if an error was thrown.</returns>
        private ExternalProcessResult ExecuteProcess(string exePath, string exeArgs)
        {
            var process = new ExternalProcess
            {
                CommandPath = exePath,
                Arguments = exeArgs,
                WorkingDirectory = LocalStoragePath
            };

            try
            {
                return process.Run();
            }
            catch (ExternalProcessException ex)
            {
                string outputInfo = "No program output";
                if (!string.IsNullOrEmpty(ex.StandardError) || !string.IsNullOrEmpty(ex.StandardOutput))
                {
                    outputInfo = Environment.NewLine + "stderr: " + ex.StandardError + Environment.NewLine + "stdout: " + ex.StandardOutput;
                }

                Log.Error("Failed to invoke command {0} {1}: exit code was {2}.  {3}", ex.CommandPath, ex.Arguments, ex.ExitCode, outputInfo);
                return null;
            }
            catch (Exception ex)
            {
                Log.Error("Error in task processor: {0}", ex.ToString());
                return null;
            }

        }
    }
}
