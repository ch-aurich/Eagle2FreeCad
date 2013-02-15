Eagle2FreeCad
============

This expansion to freecad imports your eagle boards. If you have STEP Models of your parts available it will model the ready to use pcb. You can even have multiple PCBs in a single board file. These boards can be assembled in a certain way. See the Wikipage on Github for more information.

Please note that this just works for the recently introduced XML format of Eagle 6.

License
======

This software is licenced under CC-BY (http://creativecommons.org/licenses/by/3.0/) but feel free to donate  to the Open Source Hardware Foundation (http://www.oshwa.org/) if you want to pay something for the usage of this software.

Installation
===========

- download eagle.FCMacro
- put it in your freecad macro folder
- optional: make sure that the option to print python output in the console is active

That is all you have to do. 

Running the import
================

- open freecad
- open the macro dialog 
- execute the macro called "eagle.FCMacro"
- you will be asked for a folder where your STEP model reside. Just navigate to it and click "Open"
- the next dialog asks you for the eagle board file you want to open, select it an click "Open"
- the script will run now - this can take a while, especially for complex PCBs with many parts
- when the macro is finished you will see the model
- if you do not have all STEP models needed for building the 3D Model of your board there will be 
  a list of the missing packages in the python console (only if you choose to do the optional part
  in the installation section)
