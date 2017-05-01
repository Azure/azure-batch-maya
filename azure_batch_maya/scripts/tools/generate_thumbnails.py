# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import sys
import subprocess

SUPPORTED_FORMATS =  { ".png", ".bmp", ".jpg", ".tga", ".exr", ".jpeg" }

if __name__ == '__main__':
    try:
        render_exit_code = int(sys.argv[1])
        print("Render process exited with code: {}".format(render_exit_code))
        cwd = os.getcwd()
        job_outputs = os.path.join(cwd, 'images')
        if not os.path.isdir(job_outputs):
            raise Exception("Unable to locate output directory: {}".format(job_outputs))

        print("Looking for all outputs in: {}".format(job_outputs))
        all_outputs = []
        for root, dirs, files in os.walk(job_outputs):
            all_outputs.extend([os.path.join(root, f) for f in files])
        print("Found {} total output files.".format(len(all_outputs)))
        filtered = [o for o in all_outputs if os.path.splitext(o)[1].lower() in SUPPORTED_FORMATS]
        if not filtered:
            raise Exception("Found no output files using a supported format. Skipping thumbnail generation.")

        print("Found {} applicable output files.".format(len(filtered)))
        input_file = filtered[0]
        if len(filtered) > 1:
            beauty_pass = [o for o in filtered if 'beauty' in o.lower()]
            if beauty_pass:
                input_file = beauty_pass[0]
        print("Using output '{}' for thumbnail generation.".format(input_file))

        thumb_dir = os.path.join(cwd, 'thumbs')
        if not os.path.isdir(thumb_dir):
            print("Creating directory for thumbnail output.")
            os.makedirs(thumb_dir)

        task_id = os.environ['AZ_BATCH_TASK_ID']
        output_file = os.path.join(thumb_dir, task_id + '_thumb.png')
        commands = ['magick', 'convert', input_file, '-thumbnail', '200x150', output_file]
        conversion = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        conversion.wait()
        if conversion.returncode != 0:
            print("convert exited with code: {}".format(conversion.returncode))
            stdout, stderr = conversion.communicate()
            print("Stdout: {}".format(stdout))
            print("Stderr: {}".format(stderr))
            raise Exception("Thumbnail conversion failed.")
        if not os.path.isfile(output_file):
            raise Exception("No output file generated: {}".format(output_file))
        print("Successfully created thumbnail: {}".format(output_file))
    except Exception as exp:
        print(exp)
    finally:
        print("Exiting with code: {}".format(render_exit_code))
        sys.exit(render_exit_code)
