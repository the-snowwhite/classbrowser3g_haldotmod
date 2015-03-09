
Trying to decode whats inside a hal file and how components are connected can be
challenging.
I found a utility that enables visualization of machinekit hal files [net2dot.py](http://emergent.unpythonic.net/01174426278) 
However the result includes everything in the hal and results in a very large difficult to navigate image.
So I set out on a quest to see if it was possible to extract function blocks out of the full picture.
and came up with [extractdot.py](https://github.com/the-snowwhite/classbrowser3g_haldotmod/blob/master/browserwidget-3g/classbrowser3g/extractdot.py) which will extract every line containing the name input + the surroundings, from the output of net2dot

So far so good I thought that it would be nice to have a class like panel to be able to select the component or net directly in my editor (gedit) right-cliky on it and have a window pop up with the generated extract.

This is what the classbrowser3g_haldotmod gedit plugin does together with the .ctags file.
 
> Written with [StackEdit](https://stackedit.io/).