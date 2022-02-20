"""Define paths used by Superpaper."""

import os
import platform
import shutil
import sys

# Set path to binary / script
if getattr(sys, 'frozen', False):
    PATH = os.path.dirname(os.path.dirname(os.path.realpath(sys.executable)))
else:
    PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
print(PATH)

def setup_config_path():
    """Sets up config path for settings and profiles.

    On Linux systems use XDG_CONFIG_HOME standard, i.e.
    $HOME/.config/superpaper by default.
    Snap package uses SNAP_USER_DATA.
    On Windows and Mac use executable portable path for now.
    """
    # from sp_logging import DEBUG, G_LOGGER

    if platform.system() == "Linux":
        if os.environ.get("SNAP_USER_DATA"):
            config_path = os.environ.get("SNAP_USER_DATA")
            return config_path
        else:
            config_path = xdg_path_setup("XDG_CONFIG_HOME",
                                        os.path.join(os.path.expanduser("~"),
                                                    ".config")
                                        )
            # if DEBUG: G_LOGGER.info("config path: %s", config_path)
            return config_path
    elif platform.system() == "Windows":
        # Windows and Mac default to the old portable config behavior
        config_path = PATH
        # and test if it is writable:
        if not test_full_write_access(config_path) or test_git_path(PATH):
            # if it is not writable, use %LOCALAPPDATA%\Superpaper
            config_path = os.path.join(os.getenv("LOCALAPPDATA"), "Superpaper")
            if not os.path.isdir(config_path):
                os.mkdir(config_path)
        return config_path
    else:
        # Mac & other default to the old portable config behavior
        config_path = PATH
        return config_path


def setup_cache_path():
    """Sets up temp wallpaper path.

    On Linux systems use XDG_CACHE_HOME standard. Snap package uses SNAP_USER_COMMON.
    On Windows and Mac use executable portable path (PATH/temp) for now.
    """
    # from sp_logging import DEBUG, G_LOGGER

    if platform.system() == "Linux":
        if os.environ.get("SNAP_USER_COMMON"):
            common_path = os.environ.get("SNAP_USER_COMMON")
            temp_path = os.path.join(common_path, "temp")
            return temp_path
        else:
            cache_path = xdg_path_setup("XDG_CACHE_HOME",
                                        os.path.join(os.path.expanduser("~"),
                                                    ".cache")
                                        )
            temp_path = os.path.join(cache_path, "temp")
            # if DEBUG: G_LOGGER.info("temp path: %s", temp_path)
            return temp_path
    elif platform.system() == "Windows":
        # Windows and Mac default to the old portable temp behavior
        parent_path = PATH
        temp_path = os.path.join(parent_path, "temp")
        # and test if it is writable:
        if not test_full_write_access(parent_path) or test_git_path(PATH):
            # if it is not writable, use %LOCALAPPDATA%\Superpaper\temp
            temp_path = os.path.join(os.getenv("LOCALAPPDATA"), os.path.join("Superpaper", "temp"))
            if not os.path.isdir(temp_path):
                os.mkdir(temp_path)
        return temp_path
    else:
        # Mac & other keep the old portable config behavior for now.
        temp_path = os.path.join(PATH, "temp")
        return temp_path


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

def test_full_write_access(path):
    try:
        testdir = os.path.join(path, "test_write_access")
        os.mkdir(testdir)
        os.rmdir(testdir)
        return True
    except PermissionError:
        # There is no access to create folders in path:
        return False

def test_git_path(path):
    if "github\superpaper" in path.lower():
        return True
    else:
        return False


# Derivative paths
CONFIG_PATH = setup_config_path()   # Save profiles and settings here.
print(CONFIG_PATH)
TEMP_PATH = setup_cache_path()     # Save adjusted wallpapers in here.
if not os.path.isdir(TEMP_PATH):
    os.mkdir(TEMP_PATH)
PROFILES_PATH = os.path.join(CONFIG_PATH, "profiles")
print(PROFILES_PATH)
if not os.path.isdir(PROFILES_PATH):
    # Profiles folder didn't exist, so create it and copy example
    # profiles in there assuming it's a first time run.
    os.mkdir(PROFILES_PATH)
    example_src = os.path.join(PATH, "superpaper/profiles")
    if os.path.isdir(example_src):
        for example_file in os.listdir(example_src):
            shutil.copy(os.path.join(example_src, example_file), PROFILES_PATH)
