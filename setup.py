import os
import sys
from setuptools import setup, find_packages


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


def test_import(packaname, humanname):
    try:
        __import__(packaname)
    except ImportError:
        print("{} import failed; refer to the install instructions.".format(humanname))
        sys.exit(1)

if __name__ == "__main__":
    test_import("wx", "wxPython")

    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'),
              encoding='utf-8') as f:
        long_description = f.read()

    setup(
        name="superpaper",
        version=read_version(),
        author="Henri Hänninen",
        description="Cross-platform wallpaper manager that focuses on "
                    "multi-monitor support. Features include ppi corrections, "
                    "keyboard shortcuts, slideshow.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/hhannine/superpaper",

        classifiers=[
            # "Development Status :: 4 - Beta",
            "Development Status :: 5 - Production/Stable",
            "Environment :: X11 Applications",
            # "Environment :: Win32",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: POSIX :: Linux",
            # "Operating System :: Microsoft :: Windows",
            "Programming Language :: Python :: 3.6",
            "Topic :: Utilities",
        ],
        keywords="dual-monitor multi-monitor wallpaper background manager",
        license="MIT",

        # python_requires="~=3.5",
        install_requires=[
            "Pillow>=7.0.0",
            "screeninfo>=0.6.1",
            "numpy>=1.18.0",
            "system_hotkey310>=1.0.5",
            "xcffib>=0.8.0",
            "xpybutil>=0.0.5"
        ],
        # packages=["superpaper"],
        packages=find_packages(),
        entry_points={
            "console_scripts": ["superpaper = superpaper.__main__:main"]
            # "gui_scripts": ["superpaper = superpaper.superpaper:main"]    # for possible future windows install support.
        },
        package_data={
            "superpaper": ["resources/superpaper.png",
                           "resources/test.png",
                           "resources/icons8-merge-vertical-96.png",
                           "resources/icons8-merge-horizontal-96.png",
                           "profiles/example.profile",
                           "profiles/example_multi.profile"
                          ]
        },
        data_files=[
            ("share/applications", ["superpaper/resources/superpaper.desktop"]),
            ("share/icons/hicolor/256x256/apps", ["superpaper/resources/superpaper.png"]),
        ]

    )
