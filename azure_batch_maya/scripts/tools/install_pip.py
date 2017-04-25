
import os
import tempfile
import sys
import urllib2


_GET_PIP = "https://bootstrap.pypa.io/get-pip.py"


if __name__ == '__main__':
    temp_dir = os.path.join(tempfile.gettempdir(), 'azure-batch-maya')
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    sys.path.append(temp_dir)
    pip_script = os.path.join(temp_dir, 'getpip.py')
    if not os.path.exists(pip_script):
        with open(pip_script, 'w') as script:
            data = urllib2.urlopen(_GET_PIP)
            script.write(data.read())
    import getpip
    try:
        getpip.main()
    except BaseException as e:
        import pip
    sys.exit(0)