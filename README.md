# Superpaper

Superpaper is an advanced multi monitor wallpaper manager for **Linux** and **Windows** operating systems, with partial and untested support for Mac OS X.

![](https://raw.githubusercontent.com/hhannine/Superpaper/branch-resources/readme-banner.jpg)
![](https://raw.githubusercontent.com/hhannine/Superpaper/branch-resources/gui-screenshot.png)

### Novel features include
- Advanced wallpaper spanning options
  - Pixel density correction
  - Bezel correction
  - Perspective correction
  - These are described in more detail on this [wiki page](https://github.com/hhannine/superpaper/wiki/Wallpaper-spanning-with-advanced-options:-what-the-pixel-density-and-perspective-corrections-are-about).
- Extensive Linux support!
  - Aims to support all desktop environments
  - Span wallpaper on KDE and XFCE!
- Cross-platform: works on Linux and Windows
  - MacOS needs testing and packaging

### Features in detail
- Set a single image across all displays
- Set different image on every display
- Span images on groups of displays: one image on laptop screen and another spanned on two external monitors, for example.
- **Pixel density correction**: span an image flawlessly across displays of different shapes and sizes!
- **Bezel correction**: let the image continuously span behind your bezels.
- **Perspective correction**: span the image even more flawlessly!
- Manual pixel offsets for fine-tuning
- Slideshow with configurable file order from local sources
- Add wallpapers one by one or a folder at a time (no subfolders)
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
- supplying a [custom command](./docs/custom-command.md) to set the wallpaper

if support for your system of choice is not built-in.


### Support
If you find Superpaper useful please consider supporting its development:

- [Support via PayPal](https://www.paypal.me/superpaper/5)
- [Support via Github Sponsors](https://github.com/sponsors/hhannine)

Github matches your donations done through the sponsorship program!


## Installation

### Linux

An AppImage package is available on the [releases page](https://github.com/hhannine/superpaper/releases).  
The AppImage will run once you make it executable.

 For native, and other, installation options head over to: [installing on linux](./docs/installation-linux.md). System theme and icon integration can be better on the native (PyPI) installation.

### Windows 10

 A Windows installer and a portable package are available on the [releases page](https://github.com/hhannine/superpaper/releases).

### Mac OS X

 You must install the dependencies and run the project, see [development-macos](./docs/development-macos.md).


## Usage

You can either:

- Open Superpaper as a graphical application
  - First run opens help and wallpaper settings. Disable 'show help at start' to run Superpaper silently in the background.
  - Control Superpaper in the background from the tray menu or with hotkeys.
- Call it from the [command-line](./docs/cli-usage.md)
  - Perspectives cannot be configured or used through the CLI currently.


## Troubleshooting

If you run into issues and Superpaper closes unexpectedly, you can either:
- Enable logging in the Settings.
- Manually enable logging in the 'general_settings' file by setting 'logging=true'.
- Run Superpaper from the command-line with the switch '--debug' to get debugging prints.
```sh
superpaper --debug
#or
./Superpaper-2.0.2-x86_64.AppImage --debug
```
Check the logs and come create an issue!


## Known issues

For some common problems and solutions, check [Known issues](./docs/known-issues.md).


## License

Superpaper is published under the [MIT License](./LICENSE).
