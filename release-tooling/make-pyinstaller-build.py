import os
import platform
import sys

def wrap_run(arg_list):
    print(" ".join(arg_list))
    os.system(" ".join(arg_list))
    print("make-pyinstaller-build: Build finished.")

def main():
    platform_sys = platform.system()
    if platform_sys == "Linux":
        cmd = ["pyinstaller", "--onefile",
               "--name", "superpaper",
               "superpaper/__main__.py"]
        wrap_run(cmd)
    elif platform_sys == "Windows":
        if len(sys.argv) == 2:
            if sys.argv[1] == "testing":
                cmd = ["pyinstaller", "--onefile",
                       "--name", "superpaper",
                       "-i", r".\superpaper\resources\superpaper.ico",
                       r".\superpaper\__main__.py"]
                wrap_run(cmd)
            elif sys.argv[1] == "dist":
                cmd = ["pyinstaller", "--onefile",
                       "--noconsole",
                       "--name", "superpaper",
                       "-i", r".\superpaper\resources\superpaper.ico",
                       r".\superpaper\__main__.py"]
                wrap_run(cmd)
        else:
            print("A type of build must be passed as the only argument: 'testing' or 'dist'.")
    else:
        print("Running on currently unsupported or untested OS: {}".format(platform_sys))


if __name__ == '__main__':
    main()
