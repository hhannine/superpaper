import os
import platform
import sys
from setuptools import setup


def read_version():
    with open("superpaper/__version__.py") as verfile:
        verlines = verfile.readlines()
    for line in verlines:
        if "__version__" in line:
            ver_str = line.split("=")[1].strip().replace('"',"")
            print(ver_str)
            return ver_str
    print("Version not found, exitting install.")
    sys.exit(1)

def establish_config_dir():
    """Sets up config path for settings and profiles.

    On Linux systems use XDG_CONFIG_HOME standard, i.e.
    $HOME/.config/superpaper by default.
    On Windows and Mac use executable portable path for now.
    """
    if platform.system() == "Linux":
        config_path = xdg_path_setup("XDG_CONFIG_HOME",
                                     os.path.join(os.path.expanduser("~"),
                                                  ".config")
                                    )
        return config_path
    else:
        print("This setup.py has been designed for Linux only. Apologies for any inconvenience.")
        sys.exit(1)

def xdg_path_setup(xdg_var, fallback_path):
    """Sets up superpaper folders in the appropriate XDG paths:

    XDG_CONFIG_HOME, or fallback ~/.config/superpaper
    XDG_CACHE_HOME, or fallback ~/.cache/superpaper
    """

    xdg_home = os.environ.get(xdg_var)
    if xdg_home and os.path.isdir(xdg_home):
        xdg_path = os.path.join(xdg_home, "superpaper")
    else:
        xdg_path = os.path.join(fallback_path, "superpaper")
    # Check that the path exists and otherwise make it.
    if os.path.isdir(xdg_path):
        return xdg_path
    else:
        # default path didn't exist
        os.mkdir(xdg_path)
        return xdg_path


def test_import(packaname, humanname):
    try:
        __import__(packaname)
    except ImportError:
        print("{} import failed; refer to the install instructions.".format(humanname))
        sys.exit(1)

if __name__ == "__main__":
    test_import("wx", "wxPython")
    # read_version()
    # print(establish_config_dir())
    # sys.exit(0)

    setup(
        name="superpaper",
        version=read_version(),
        author="Henri Hänninen",
        description="Cross-platform wallpaper manager that focuses on "
                    "multi-monitor support. Features include ppi corrections, "
                    "keyboard shortcuts, slideshow.",
        long_description="todo",
        url="https://github.com/hhannine/superpaper",

        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: X11 Applications",
            # "Environment :: Win32",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: MIT Licence",
            "Natural Language :: English",
            "Operating System :: POSIX :: Linux",
            # "Operating System :: Microsoft :: Windows",
            "Programming Language :: Python :: 3.5",
            "Topic :: Utilities",
        ],
        keywords="dual-monitor multi-monitor wallpaper background manager",
        license="MIT",

        install_requires=[
            "Pillow>=6.0.0",
            "screeninfo>=0.6.1",
        ],
        packages=["superpaper"],
        entry_points={
            "console_scripts": ["superpaper = superpaper.superpaper:main"]
        },      # On windows create a 'gui_scripts' entry
        # include_package_data=True,
        package_data={
            "superpaper": ["resources/superpaper.png"]
        },
        data_files=[
            ("share/applications", ["superpaper/resources/superpaper.desktop"]),
            ("share/icons/hicolor/256x256/apps", ["superpaper/resources/superpaper.png"]),
            # ("resources", ["resources/superpaper.png"]),
            (os.path.join(establish_config_dir(),"profiles"), ["profiles/example.profile", "profiles/example_multi.profile"])
        ]

    )
