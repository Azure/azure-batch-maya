#-------------------------------------------------------------------------
#
# Azure Batch Maya Plug-in
#
# Copyright (c) Microsoft Corporation.  All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#--------------------------------------------------------------------------

import sys
import os
import subprocess
import shutil
import zipfile


def find_version():
    root_dir = os.path.dirname(os.path.realpath(__file__))
    plugin_path = os.path.join(root_dir, 'azure_batch_maya', 'plug-in', 'AzureBatch.py')
    plugin_version = ""
    with open(plugin_path, 'r') as plugin_file:
        for line in plugin_file:
            if line.startswith('VERSION ='):
                plugin_version = line[9:].strip('\n" \'')
                break
    if not plugin_version:
        raise ValueError("Couldn't detect plugin version from {}".format(plugin_file))
    return plugin_version


def main():
    """Build Maya Plug-in package"""

    print("Building package...")

    package_dir = os.path.abspath("build")
    if not os.path.isdir(package_dir):
        try:
            os.mkdir(package_dir)
        except:
            print("Cannot create build dir at path: {0}".format(package_dir))
            return

    version = find_version()
    package = os.path.join(package_dir, "AzureBatch_Maya_Plugin-v{0}.zip".format(version))
    source = os.path.abspath("azure_batch_maya")

    with zipfile.ZipFile(package, mode='w') as maya_zip:
        for root, dirs, files in os.walk(source):
            if root.endswith("__pycache__"):
                continue

            for file in files:
                if os.path.splitext(file)[1] in ['.png', '.mel', '.py', '.html', '.json']:
                    maya_zip.write(os.path.relpath(os.path.join(root, file)))

    print("Package complete!")

if __name__ == '__main__':
    main()