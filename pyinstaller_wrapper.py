"""
Simple wrapper that makes the module structure of Superpaper
compatible with PyInstaller builds.
"""

from superpaper.superpaper import main

if __name__ == '__main__':
    main()
