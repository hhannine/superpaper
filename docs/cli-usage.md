## CLI usage

Superpaper supports the following arguments, display specific values are given starting from the first display on the left.
- "--help"
- "--profile", run Superpaper by starting a specific pre-configured wallpaper profile.
- "--setimages", list of images to set on your monitors, if given only one it will be spanned across.
- "--advanced", optional, changes spanning to advanced mode, which must first be configured in the GUI.
- "--perspective", optional, accepts a valid perspective profile name. Configuration through GUI.
- "--spangroups", optional, takes a list of spanning groups formatted as: 0 123 46 5.
- "--offsets", optional, image alignment adjustment with pixel offsets.
- "--command", optional, user can pass a custom command to set the wallpaper.
- "--debug", debugging flag.

An example using all corrections to set a single spanned image:
```
superpaper --setimages /path/to/img.png --advanced --perspective default --spangroups 0 12 --offsets 0 0 40 -100 0 0
```
Offsets are given as a pair-wise list of "horizontal_offset vertical_offset" starting from the first monitor on the left, 
i.e. in the above example the display on the left is given no additional offset (0 0) and the display in 
the middle is given a horizontal offset to the right by 40px and a vertical offset of 100px up (40 -100).

In the custom command, replace '/path/to/img.jpg' by '{image}', i.e. for example with the Gnome command:
```
gsettings set org.gnome.desktop.background picture-uri file://{image}
```

The resulting image is saved into XDG_CACHE_HOME/superpaper/temp/ and then set as the wallpaper. On Windows either the installation or portable path temp/ directory is used.
