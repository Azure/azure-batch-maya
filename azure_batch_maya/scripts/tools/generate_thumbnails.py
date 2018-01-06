# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import subprocess
import traceback
import shutil
import string


printable = set(string.printable)
SUPPORTED_FORMATS =  { ".png", ".bmp", ".jpg", ".tga", ".exr", ".jpeg" }

if __name__ == '__main__':
    try:
        cwd = os.getcwd()
        thumb_dir = os.path.join(cwd, 'thumbs')
        if not os.path.isdir(thumb_dir):
            print("Creating directory for thumbnail output.")
            os.makedirs(thumb_dir)
        
        render_exit_code = int(sys.argv[1])
        print("Render process exited with code: {}".format(render_exit_code))
        
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
        try:
            filtered_input_file = input_file.encode('utf-8')
        except UnicodeDecodeError:
            temp_dir = os.path.join(cwd, 'temp_images')
            if not os.path.isdir(temp_dir):
                print("Creating directory for non-unicode outputs.")
                os.makedirs(temp_dir)
            filtered_input_file = filter(lambda x: x in printable, input_file)
            filtered_input_file = os.path.join(temp_dir, os.path.basename(filtered_input_file))
            shutil.copyfile(input_file, filtered_input_file)
        print("Using output '{}' for thumbnail generation.".format(filtered_input_file))

        task_id = os.environ['AZ_BATCH_TASK_ID']
        output_file = os.path.join(thumb_dir, task_id + '_thumb.png')
        commands = ['convert', filtered_input_file, '-thumbnail', '200x150', output_file]
        if os.name == 'nt':
            commands.insert(0, 'magick')

        print("Running imagemagick: {}".format(commands))
        conversion = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        conversion.wait()
        if conversion.returncode != 0:
            print("convert exited with code: {}".format(conversion.returncode))
            stdout, stderr = conversion.communicate()
            print(stdout)
            print(stderr)
            raise Exception("Thumbnail conversion failed.")
        if not os.path.isfile(output_file):
            raise Exception("No output file generated: {}".format(output_file))
        print("Successfully created thumbnail: {}".format(output_file))
    except Exception as exp:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    finally:
        print("Exiting with code: {}".format(render_exit_code))
        sys.exit(render_exit_code)
