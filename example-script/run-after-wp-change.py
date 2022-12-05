import subprocess
import sys

# After Superpaper changes the wallpaper, it looks for a scipt named
# "run-after-wp-change.py" in the config folder, which by default is
# at the path ~/.config/superpaper
# or at XDG_CONFIG_HOME/superpaper

# The current wallpaper name is passed to the scipt as the argument sys.argv[1].
# argv[0] is the script name.
# list of source image(s) is passed to the script as the args 2-->
wallpaper_image_name = sys.argv[1]
list_of_source_images = sys.argv[2:]

# example command to run that opens the passed image in a default application:
# this is executed by Superpaper after the wallpaper has changed.
subprocess.run(["gio", "open", wallpaper_image_name])
