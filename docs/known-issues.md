### Linux
- Ubuntu (or Gnome in general?): Tray icon does not show up:
  - One workaround for now is to use the Gnome extension `TopIcons plus`.
- Ubuntu (others?): gsettings memory back-end issue:
  - Solution: run superpaper with
  ```
  GIO_EXTRA_MODULES=/usr/lib/x86_64-linux-gnu/gio/modules/ superpaper
  ```
- Doesn't run on PopOS
  - This is fixed in upcoming release.
  - Solution before then: run with
  ```
  DESKTOP_SESSION=gnome superpaper
  ```

### Windows
- :)

### Mac OS X
- It is not known whether this works at all. If you try it, tell me how it goes!
- The library implementing global hotkeys does not support Mac OS X at this time unfortunately.
