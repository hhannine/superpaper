import os
import shutil
import subprocess
import sys

DISTPATH = os.path.realpath("./releases/")

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

def make_appimage(dist_path, version):
    appdir = os.path.join(dist_path, version)
    executable = "./dist/superpaper"
    desktop_file = "./superpaper/resources/superpaper.desktop"
    icon = "./superpaper/resources/superpaper.png"
    include_resources = [
        icon,
        "./superpaper/resources/icons8-merge-vertical-96.png",
        "./superpaper/resources/icons8-merge-horizontal-96.png",
        "./superpaper/resources/test.png"
    ]

    # first create appdir with linuxdeploy
    cmd = [
            "VERSION={}".format(version),
            "$HOME/Applications/linuxdeploy-x86_64.AppImage",
            "--appdir={}".format(appdir),
            "--executable={}".format(executable),
            "--desktop-file={}".format(desktop_file),
            "--icon-file={}".format(icon)
          ]
    print(" ".join(cmd))
    os.system(" ".join(cmd))
    print("make-appimage-release: Appdir compilation done.")
    
    # intermediate step: copy resources into appdir directory
    appdir_usr = os.path.join(appdir, "usr")
    appdir_resource_target = os.path.join(appdir_usr, "superpaper/resources")
    if not os.path.exists(appdir_resource_target):
        os.makedirs(appdir_resource_target)
    for resrc in include_resources:
        shutil.copy2(resrc, appdir_resource_target)
    
    # final step: package AppImage from appdir
    cmd2 = [
            "VERSION={}".format(version),
            "$HOME/Applications/linuxdeploy-x86_64.AppImage",
            "--appdir={}".format(appdir),
            "--output appimage"
           ]
    print(" ".join(cmd2))
    os.system(" ".join(cmd2))
    

def main():
    if not os.path.isdir(DISTPATH):
        os.mkdir(DISTPATH)
        print("Made dir %s" % DISTPATH)
    version = read_version()
    dist_path = os.path.join(DISTPATH)
    
    # run pyinstaller build
    try:
        subprocess.call(["python3", "./release-tooling/make-pyinstaller-build.py"])
    except:
        print("\nPyinstaller build FAILED.\n")
        exit(0)
    print("\nPyinstaller build done.\n")

    make_appimage(dist_path, version)    
    print("AppImage package build done.")

    # done
    print("Release built and packaged.")


if __name__ == '__main__':
    main()
