import os
import sys

def wrap_run(arg_list):
    print(" ".join(arg_list))
    os.system(" ".join(arg_list))
    print("Wrapper: Build finished.")

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == "testing":
            cmd = ["pyinstaller", "--onefile",
                              "--name", "superpaper",
                              "-i", r".\superpaper\resources\superpaper.ico",
                              r".\pyinstaller_wrapper.py"]
            wrap_run(cmd)
        elif sys.argv[1] == "dist":
            cmd = ["pyinstaller", "--onefile", "--noconsole",
                              "--name", "superpaper",
                              "-i", r".\superpaper\resources\superpaper.ico",
                              r".\pyinstaller_wrapper.py"]
            wrap_run(cmd)
    else:
        print("A type of build must be passed as the only argument: 'testing' or 'dist'.")


if __name__ == '__main__':
    main()
