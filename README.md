![](https://raw.githubusercontent.com/hhannine/Superpaper/branch-resources/readme-banner.jpg)

# Superpaper

Superpaper is an advanced multi monitor wallpaper manager 
for Linux and Windows operating systems, with partial and untested support for Mac OS X.

Supported Linux desktop environments / window managers are:
- Cinnamon
- Gnome
- i3
- KDE
- LXDE
- Mate
- Pantheon
- XFCE

and additionally there is support for
- feh
- supplying a custom command to set the wallpaper

if support for your system of choice is not built-in.

### Features
- Set a single image across all displays
- Set different image on every display
- Pixel per inch correction: span an image flawlessly across displays of different shapes and sizes!
- Bezel correction
- Manual pixel offsets for fine-tuning
- Slideshow with configurable file order from local sources
- Command-line interface
- Tray applet for slideshow control
- Hotkey support for easy slideshow control (Only Linux and Windows)

A single horizontal row of monitors is supported at this time. Monitors can be in portrait.
By default Superpaper assumes that your displays' center points are on a horizontal line, if they are not you can adjust the wallpaper
using the manual offset.

In the above banner shot you can see the PPI and bezel corrections in action.
					  
## Installation

You may either clone the repository or just download the script, examples and resources, and run the script. However you then need to take care of its dependencies.

#### Requirements
- Python 3.5+
- Pillow (or the slower PIL should also work)
- screeninfo
- wxpython (tray applet & slideshow, optional)
- system_hotkey (hotkeys, optional)

If you are going to run only in CLI mode you need to install the first three in the list. For full functionality you will of course need to install all of them.

One can install these easily via pip3:
```
pip3 install Pillow
pip3 install screeninfo
pip3 install wxpython
pip3 install system_hotkey
```
System_hotkey has dependencies: on linux it needs "xcffib" and "xpybutil" modules, and on Windows it needs "pywin32".
Note that on Linux wxpython needs to be built and even though it is automated via pip, it has its own [dependencies](https://wxpython.org/blog/2017-08-17-builds-for-linux-with-pip/index.html), 
and the build may take some time.
However for a few Centos, Debian, Fedora and Ubuntu flavors there are pre-built wheels so on those you can look at the [instructions](https://wxpython.org/pages/downloads/) to install wxpython
without having to build it yourself.


## Usage

You can either run Superpaper to use all of its features, or alternatively you may call it from the command-line to set your multi monitor wallpaper, 
with or without pixel density / bezel corrections or manual offsets.

### Full functionality / tray applet mode

To provide your desired wallpaper settings, you create yourprofile.profile files in Superpaper/profiles.

#### Profile configuration

Example profile configurations are provided in the Superpaper/profiles folder.

Following settings are supported and they are expected in this form:
```
name=example
spanmode=single
slideshow=true
delay=600
sortmode=shuffle
offsets=0,0;0,0
bezels=9.5;7
diagonal_inches=27;25
hotkey=control+super+shift+x
display1paths=C:\Path\To\Image\Folder1;C:\Path\To\Image\Folder2;C:\Path\To\Image\Folder3
```
Accepted values and their explanations are:
- spanmode:
	- single
	- multi
- slideshow:
	- true
	- false
- delay:
	- integer, slideshow delay in seconds
- sortmode:
	- shuffle
	- alphabetical
- offsets
	- horizontal,vertical pixel offsets with offsets of different monitors separated by ";"
- bezels
	- List of monitor bezel thicknesses in millimeters, floats are accepted, values separated by ";". 
	- Measure at the edges where monitor sides meet. A possible gap can be included in the values given.
- diagonal_inches
	- List of monitor diagonals in inches. Used for computing display pixel densities (PPI).
- hotkey
	- Up to three modifiers are supported for a hotkey: "control", "shift", "super" (the win-key) and "alt". 
	- Separate keys with a "+" as shown above.
- display1paths
	- List of local image source paths, separate paths with a ";".
	- display1paths is used by the left-most display.
- display2paths
	- Same as display1paths, but for the 2nd monitor from the left.
	- For any additional displays paths are given via display3paths, display4paths, etc.


#### General settings

General settings are saved in Superpaper/general_settings and formatted in the following way:
```
logging=false
use hotkeys=true
next wallpaper hotkey=control+super+w
pause wallpaper hotkey=control+super+shift+p
set_command=gsettings set ...
```
Up to three modifiers are supported for a hotkey: "control", "shift", "super" (the win-key) and "alt".

Set_command accepts a user defined one liner to set the wallpaper if your system is not supported. One can tell Superpaper to use feh by setting
```
set_command=feh
```
In the custom command, replace /path/to/img.jpg by '{image}', i.e. for example with the Gnome command:
```
gsettings set org.gnome.desktop.background picture-uri file://{image}
```

Lastly, if the included white tray icon doesn't go nicely with your rice, included are a couple of alternative colorations and you may even replace the default icon with anything you wish.
Just overwrite the "default_icon.png".


### CLI usage

Superpaper supports the following arguments, display specific values are given starting from the first display on the left.
- "--help"
- "--setimages", list of images to set on your monitors, if given only one it will be spanned across.
- "--inches", optional, expects display diagonals in inches to compute PPIs
- "--bezels", optional, expects display bezels in millimeters
- "--offsets", optional, if image alignment isn't quite right you can add additional offset in pixels
- "--command", optional, user can pass a custom command to set the wallpaper.

An example using all corrections to set a single spanned image:
```
superpaper.py --setimages /path/to/img.png --inches 27 25 --bezels 9.5 7.0 --offsets 0 0 40 -100
```
Offsets are given as a pair-wise list of "horizontal_offset vertical_offset" starting from the first monitor on the left, 
i.e. in the above example the display on the left is given no additional offset (0 0) and the display on 
the right is given a horizontal offset to the right by 40px and a vertical offset of 100px up (40 -100).

In the custom command, replace /path/to/img.jpg by '{image}', i.e. for example with the Gnome command:
```
gsettings set org.gnome.desktop.background picture-uri file://{image}
```

The resulting image is saved into Superpaper/temp/ and then set as the wallpaper.


## Known issues

### General shortcomings
- Only a single horizontal row of displays is supported at this time, i.e. monitors side by side. 
As a workaround to set separate images on the monitors you could set the monitors to be side by side virtually on the desktop, though this is understandably fairly undesirable.

### Linux
- At shutdown OS might nag that the app is not responding just before the app exits.

### Windows
- A rare and hard to reproduce issue where setting the wallpaper fails and leads to a black wallpaper. Might be related to source image properties.

### Mac OS X
- It is not known whether this works at all. If you try it, tell me how it goes!
- The library implementing global hotkeys does not support Mac OS X at this time unfortunately.


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Support
If you find Superpaper useful please consider supporting its development by buying me a coffee: [Link](here)


## License
[MIT](https://choosealicense.com/licenses/mit/)
