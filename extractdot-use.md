	https://github.com/the-snowwhite/classbrowser3g_haldotmod/blob/master/browserwidget-3g/classbrowser3g/extractdot.py

	Requirements:

	Python (2.6 or 2.7)

	net2dot.py (Jon Elson ):
	http://emergent.unpythonic.net/01174426278

first run 

	./net2dot.py xxx.hal >xxx.dot

then
	
	./extractdot.py xxx.dot name-of-component-to-extract >extract.dot
	
---
for viewing:

	xdot.py
	https://github.com/jrfonseca/xdot.py 

	Requirements:
	Python (2.6 or 2.7)

	PyGTK (2.10 or greater)

	Graphviz
to install requirements:

    sudo apt-get install python-gtk2 graphviz



### eventually gedit mod: #########


ctags:

copy .ctags to homefolder

source: (https://launchpad.net/gedit-classbrowser3g)

Manual Installation
-------------------

1. Install exuberant-ctags 
        sudo apt-get install exuberant-ctags
2. Copy the plugin to the gedit plugins folder
        cp -a classbrowser3g.plugin classbrowser3g ~/.local/share/gedit/plugins/
3. Install the gsettings schema with the following commands:
        sudo cp *.gschema.xml /usr/share/glib-2.0/schemas/
        sudo glib-compile-schemas /usr/share/glib-2.0/schemas/
4. Open gedit and click `Edit -> Preferences -> Plugins` and activate the plugin

[note: you may have to change the 2. line Loader=python3 to Loader=python in classbrowser3g.plugin]

gedit-classbrowser3g_haldotmod

copy classbrowser3g_haldotmod to ~/.local/share/gedit/plugins
