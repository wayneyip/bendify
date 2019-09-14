# Bendify
![Bendify_img1](https://i.imgur.com/XK3heOD.png)

Maya Python tool to automate bendy joint chain setup on two given joints.

## Features
- Automatic setup of up to 20 sub-joints within 1 second
- Quadratic weight distribution across parent constraints, for bendy behavior
- Automatic setup of curveInfo and multiplyDivide nodes, for stretchiness

Here's a simple demo of the tool in action:

![Bendify_gif2](https://i.imgur.com/x36FFWO.gif)

## Instructions

- Place `wy_bendify.py` and `wy_bendifyUI.py` in your Maya Scripts folder, found in:
    - Windows: `C:\Users\<Your-Username>\Documents\maya\<20xx>\scripts`
    - OSX: `/Users/<Your-Username>/Library/Preferences/Autodesk/maya/<20xx>/scripts`
    - Linux: `/home/<Your-Username>/maya/<20xx>/scripts`
- Restart/open Maya, then open the Script Editor by:
	- Going to `Windows > General Editors > Script Editor`

		**or**
	- Left-clicking the `{;}` icon at the bottom-right of your Maya window
- Copy/paste and run the following code in your Script Editor:

	```
	import wy_bendifyUI
	reload (wy_bendifyUI)
	wy_bendifyUI.bendifyUI()
	```
	to launch the Bendify tool UI.

- (Extra) Save the UI launch code to a shelf button:
	- Go to `File > Save Script to Shelf` in the Script Editor
	- Type in a name for the button (e.g. "Bendify"), and hit OK
	- Bendify should now be saved as a button in your shelf.

## Details

**Technologies**: Maya, Python

**Developer**: Wayne Yip

**Contact**: yipw@usc.edu

