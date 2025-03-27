# Installation on Linux


## The easy portable way

AppImage packages are available on the [releases page](https://github.com/hhannine/superpaper/releases). The AppImage will run once you make it executable.


## The recommended way

This will allow Superpaper to integrate the best with your system theme and icons.  
See the screenshot in the Readme taken on Manjaro KDE.


### Step 1: Install pipx and wxPython 4.X:

Because of the differences between Linux distributions, the installation options differ:

- Arch / Manjaro: `sudo pacman -S python-pipx python-wxpython`
- Debian / Ubuntu and relatives: `sudo apt install pipx wxpython-tools`
- Fedora : `sudo dnf install pipx python3-wxpython4`
- Older distros with no wxPython4 package: [wxpython.org](https://wxpython.org/pages/downloads/)
  - Install the wheel if available for your OS: CentOS, Debian, Fedora and Ubuntu

Using `pipx` simplifies management of the virtual environment in which Superpaper is installed, but is not a hard requirement.
You may use a manually created venv.


### Step 2: Install superpaper from PyPI

Superpaper is available from [PyPI](https://pypi.org/project/superpaper), and needs `Python 3.6+`.
To install, run in a terminal:

```sh
pipx install --system-site-packages superpaper
```
On some Linux setups, you might need to log out and in, or restart to get the menu/launcher entry to show up.


## Snaps

Snaps are currently not packaged, however for reference: To install the Snap (if available) you need to install it from the downloaded file with:
```
sudo snap install superpaper_1.2.0_amd64_experimental_classic.snap --classic --dangerous
```
