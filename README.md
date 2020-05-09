![](https://raw.githubusercontent.com/hhannine/Superpaper/branch-resources/readme-banner.jpg)
![](https://raw.githubusercontent.com/hhannine/Superpaper/branch-resources/gui-screenshot.png)

# Superpaper

Superpaper is an advanced multi monitor wallpaper manager 
for **Linux** and **Windows** operating systems, with partial and untested support for Mac OS X.

### Novel features include
- Advanced spanning options
  - Pixel density correction
  - Bezel correction
  - Perspective correction
  - These are described in more detail on this [wiki page](https://github.com/hhannine/superpaper/wiki/Wallpaper-spanning-with-advanced-options:-what-the-pixel-density-and-perspective-corrections-are-about).
- Extensive Linux support!
  - Aims to support all desktop environments
  - Span wallpaper on KDE and XFCE!
- Works on both Linux and Windows

### Features in detail
- Set a single image across all displays
- Set different image on every display
- **Pixel density correction**: span an image flawlessly across displays of different shapes and sizes!
- **Bezel correction**
- **Perspective correction**: span the image even more flawlessly!
- Manual pixel offsets for fine-tuning
- Slideshow with configurable file order from local sources
- Command-line interface
- Tray applet for slideshow control
- Hotkey support for easy slideshow control (Only Linux and Windows)
- Align test tool to help fine tune your settings (Accessible only from GUI)


In the above banner photo you can see the PPI and bezel corrections in action. The left one is a 27" 4K display, and the right one is a 25" 1440p display.


Supported Linux desktop environments / window managers are:
- BSPWM (needs feh)
- Budgie
- Cinnamon
- Gnome
- i3 (needs feh)
- KDE
- LXDE & LXQt
- Mate
- Pantheon
- XFCE

and additionally there is support for
- feh
- supplying a custom command to set the wallpaper

if support for your system of choice is not built-in.


### Support
If you find Superpaper useful please consider supporting its development: [Support via PayPal][paypal-superpaper] or [Support via Github Sponsors][github-sponsors]. Github matches your donations done through the sponsorship program!

[paypal-superpaper]: https://www.paypal.me/superpaper/5
[github-sponsors]: https://github.com/sponsors/hhannine


## Installation

### Linux

Superpaper is available from PyPI, [here][sp-on-pypi]. To install Superpaper from PyPI, you _first install the `wxPython` dependency as described below_, and then run:
```
pip3 install --user -U superpaper
```
This is the recommended installation on Linux since this will allow Superpaper to integrate the best with your system theme and icons; See the above example screenshot from Manjaro KDE. In the Appimage some of these are bundled in.

Somewhat experimental AppImage package is available on the [releases page](https://github.com/hhannine/superpaper/releases). The AppImage will run once you make it executable.

Snaps are currently not packaged, however for reference: To install the Snap (if available) you need to install it from the downloaded file with:
```
sudo snap install superpaper_1.2.0_amd64_experimental_classic.snap --classic --dangerous
```

[sp-on-pypi]: https://pypi.org/project/superpaper

#### Requirements
- Python 3.6+
- Pillow
- screeninfo
- numpy
- wxpython (tray applet, GUI & slideshow, optional)
- system_hotkey (hotkeys, optional)
- xcffib (dep for system_hotkey)
- xpybutil (dep for system_hotkey)

If you install Superpaper from PyPI, pip will handle everything else other than `wxPython`. It will be easiest to install wxPython from your distribution specific package repository:
#### Arch / Manjaro
```
sudo pacman -S python-wxpython
```
#### Debian / Ubuntu and relatives
```
sudo apt install python3-wxgtk4.0
```
#### Fedora
```
sudo dnf install python3-wxpython4
```
#### Python wheels (if wxPython4 is not in your standard repositories)
For a few CentOS, Debian, Fedora and Ubuntu flavors there are pre-built wheels so on those you can look at the [instructions](https://wxpython.org/pages/downloads/) to install wxpython through pip, without having to build it as you do when installing directly from PyPI.
#### Installing other dependencies manually:
Install via pip3:
```
pip3 install -U Pillow screeninfo numpy system_hotkey xcffib xpybutil
```
#### Running CLI only
If you are going to run only in CLI mode you will need to install the first two modules in the list:
```
pip3 install -U Pillow screeninfo numpy
```
### Installing Superpaper from PyPI
Once wxPython4 is installed, you can just run:
```
pip3 install -U --user superpaper
```
This will install an icon and .desktop file for menu entries.

### Windows
For Windows an installer and a portable package are available under [releases](https://github.com/hhannine/superpaper/releases).
These work on a download-and-run basis without additional requirements. In the portable package, look for the executable "superpaper.exe" in the subfolder "superpaper".

If you want to run the cloned repo on Windows, on top of the requirements listed in the Linux section, you will need the "pywin32" module (instead of the xcffib and xpybutil modules). Installation through pip:
```
pip3 install -U Pillow screeninfo numpy wxpython system_hotkey pywin32
```

### Max OS X
Basic support for OS X has been kept in the script but it has not been tested. If you want to try to run it, best bet would be to install the dependencies through pip:
```
pip install -U wxpython Pillow screeninfo numpy
```
and then clone the repository.



## Usage

You can either run Superpaper to use all of its features, or alternatively you may call it from the command-line to set your multi monitor wallpaper, 
with or without pixel density / bezel corrections or manual offsets. Perspectives cannot be configured through the CLI currently.

**Note**: You might have to set your OS to `span` the wallpaper so it is displayed correctly regardless of the settings you give Superpaper:
- On Windows: Personalization -> Background -> Choose a fit -> Span.


### Full functionality / GUI mode

To provide your desired wallpaper settings, you access the 'Wallpaper Configuration' Tray Menu item, or also during first run. General application settings are under 'Settings' in the Tray.

#### Profile configuration

Example profile configurations are provided and accessible in the Wallpaper Configuration. (or in the superpaper/profiles folder.)


#### General settings

For hotkeys up to three modifiers are supported: "control", "shift", "super" (the win-key) and "alt".

On Linux the option `Set command` accepts a user defined one-liner to set the wallpaper if your system is not supported out of the box.
As a special case, one can tell Superpaper to use `feh` with a tested and built-in command by setting:
```
set_command=feh
```
In the custom command, replace '/path/to/img.jpg' by '{image}', i.e. for example with the Gnome command:
```
gsettings set org.gnome.desktop.background picture-uri file://{image}
```

Lastly, if the included white tray icon doesn't go nicely with your rice, included are a couple of alternative colorations and you may even replace the default icon with anything you wish.
Just overwrite the "superpaper.png" icon file.


### CLI usage

Superpaper supports the following arguments, display specific values are given starting from the first display on the left. Perspectives are not supported at this time.
- "--help"
- "--setimages", list of images to set on your monitors, if given only one it will be spanned across.
- "--inches", optional, expects display diagonals in inches to compute PPIs
- "--bezels", optional, expects display bezels in millimeters
- "--offsets", optional, if image alignment with ppi&bezels isn't quite right you can add additional offset in pixels
- "--command", optional, user can pass a custom command to set the wallpaper.
- "--debug", optional debugging flag.

An example using all corrections to set a single spanned image:
```
superpaper.py --setimages /path/to/img.png --inches 27 25 --bezels 9.5 7.0 --offsets 0 0 40 -100
```
Offsets are given as a pair-wise list of "horizontal_offset vertical_offset" starting from the first monitor on the left, 
i.e. in the above example the display on the left is given no additional offset (0 0) and the display on 
the right is given a horizontal offset to the right by 40px and a vertical offset of 100px up (40 -100).

In the custom command, replace '/path/to/img.jpg' by '{image}', i.e. for example with the Gnome command:
```
gsettings set org.gnome.desktop.background picture-uri file://{image}
```

The resulting image is saved into Superpaper/temp/ and then set as the wallpaper.


## Troubleshooting

If you run into issues and Superpaper closes unexpectedly, you can either:
- Enable logging in the 'general_settings' by setting 'logging=true'
- Run Superpaper from the command-line with the switch '--debug' to get debugging prints.
```
python superpaper.pyw --debug
```


## Known issues

### Linux
- Ubuntu (or Gnome in general?): Tray icon does not show up:
  - One workaround for now is to use the Gnome extension `TopIcons plus`.
- Ubuntu (others?): gsettings memory back-end issue:
  - Solution: run superpaper with
  ```
  GIO_EXTRA_MODULES=/usr/lib/x86_64-linux-gnu/gio/modules/ superpaper
  ```

### Windows
- :)

### Mac OS X
- It is not known whether this works at all. If you try it, tell me how it goes!
- The library implementing global hotkeys does not support Mac OS X at this time unfortunately.


## License
[MIT](https://choosealicense.com/licenses/mit/)
