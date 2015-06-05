#-------------------------------------------------------------------------
#
# Batch Apps Maya Plug-in
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

VERSION = "0.2.1"

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

    package = os.path.join(package_dir, "AzureBatch_Maya_Plugin-v{0}.zip".format(VERSION))
    source = os.path.abspath("batchapps_maya")

    with zipfile.ZipFile(package, mode='w') as maya_zip:
        for root, dirs, files in os.walk(source):
            if root.endswith("__pycache__"):
                continue

            for file in files:
                if os.path.splitext(file)[1] in ['.png', '.mel', '.py']:
                    maya_zip.write(os.path.relpath(os.path.join(root, file)))

        depends = os.path.join(os.path.dirname(__file__), "dependencies.py")
        maya_zip.write(depends, "dependencies.py")

    print("Package complete!")

if __name__ == '__main__':
    main()