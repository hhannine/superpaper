# Custom command to set the wallpaper

On Linux the option `Set command` accepts a user defined one-liner to set the wallpaper if your system is not supported out of the box.
As a special case, one can tell Superpaper to use `feh` with a tested and built-in command by setting:
```
set_command=feh
```
In the custom command, replace '/path/to/img.jpg' by '{image}', i.e. for example with the Gnome command:
```
gsettings set org.gnome.desktop.background picture-uri file://{image}
```