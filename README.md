# CVAT-Export-Helper
This project contains a series of scripts that are used for exporting YOLO data from CVAT and data augmentation. 

## To recompile:
- Change "building = True"
- For the first time just do "pyinstaller CVAT-Export-Helper.py --noconfirm"
- Every subsequent time should be "pyinstaller CVAT-Export-Helper.spec --noconfirm"
If the spec is overwritten, use the copy of the spec and replace