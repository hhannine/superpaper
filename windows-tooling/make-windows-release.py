import os
import shutil
import subprocess
import sys

from distutils.dir_util import copy_tree

SRCPATH = os.path.realpath("./superpaper")
DISTPATH = os.path.realpath("./releases/")
INNO_STUB = os.path.realpath("./releases/innostub")

def read_version():
    with open("superpaper/__version__.py") as verfile:
        verlines = verfile.readlines()
    for line in verlines:
        if "__version__" in line:
            ver_str = line.split("=")[1].strip().replace('"',"")
            print("Found version: %s" % ver_str)
            return ver_str
    print("Version not found, exitting install.")
    sys.exit(1)

def make_portable(dst_path):
    portpath = os.path.join(dst_path, "superpaper-portable")
    portres = os.path.join(portpath, "superpaper/resources")
    portprof = os.path.join(portpath, "profiles")
    portexec = os.path.join(portpath, "superpaper")
    # copy resources
    copy_tree(os.path.join(SRCPATH, "resources"), portres)
    # copy profiles
    copy_tree(os.path.join(SRCPATH, "profiles-win"), portprof)
    # copy exe-less structure to be used by innosetup
    copy_tree(portpath, INNO_STUB)

    # copy executable
    shutil.copy2("./dist/superpaper.exe", portexec)
    # zip it
    shutil.make_archive(os.path.join(dst_path, "superpaper-portable"), 'zip', portpath)

def update_inno_script(version_str, output_path):
    # update both VERSTION_STR and OUTPUT PATH
    return 0

def run_inno_script():
    inno_cmd = "iscc scriptfile.iss"
    os.system(inno_cmd)

def main():
    if not os.path.isdir(DISTPATH):
        os.mkdir(DISTPATH)
        print("Made dir %s" % DISTPATH)
    version = read_version()
    dist_path = os.path.join(DISTPATH, version)
    if not os.path.isdir(dist_path):
        os.mkdir(dist_path)
        print("Made dir %s" % dist_path)
    
    # run pyinstaller build
    # os.system("python make-pyinstaller-build.py dist")
    try:
        subprocess.call(["python", "./windows-tooling/make-pyinstaller-build.py", "dist"])
    except:
        print("\nPyinstaller build FAILED.\n")
        exit(0)
    print("\nPyinstaller build done.\n")

    # copy binary, resources and examples into package structure
    make_portable(dist_path)
    
    print("Portable package build done.")
    exit(0)

    # update inno script
    update_inno_script(version, dist_path)

    # run inno installer compilation
    run_inno_script()

    # done
    print("Release built and packaged.")


if __name__ == '__main__':
    main()
