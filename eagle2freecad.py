#################################################################################
#This is licenced under CC-BY-NC (http://creativecommons.org/licenses/by-nc/2.0/)
#Please contact Christian Aurich for commercial use of this software.
#http://c-aurich.de
#################################################################################

import Part
from FreeCAD import Base
import csv
import FreeCAD, FreeCADGui, Part
import math
from PyQt4 import QtGui
from PyQt4 import QtCore
import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


csvArray = []
totalHeight = 1.5
holes = []
parts = []
edges = []
packages = {}
missingpackages = {}
libFolder = ''

filename = QtGui.QFileDialog.getOpenFileName(None, 'Open file','')



   
#for row in csvArray:  
#  if (row[0]=='settings'):
#    libFolder = row[1]
#  if (row[0]=='outline-complete'):
#    totalHeight = float(row[1])
#  if (row[0]=='hole'):
#    partCylinder = Part.makeCylinder(float(row[3]),float(row[4])*2,Base.Vector(float(row[1]),float(row[2]),-totalHeight/2),Base.Vector(0,0,1),360)
#    holes.append(partCylinder)
#  if (row[0]=='package'):
#    if (row[8]!=''):
#      packages[row[8]]=''
#    else:
#      packages[row[6]]=''
 
 
 
tree = ET.ElementTree(file=filename)
root = tree.getroot()
drawing = root[0]
dimensionLibrary = {}

#find lines that make up the dimensions of pcbs directly
for elem in drawing.iterfind('board/plain/wire[@layer="20"]'):
  tmpedge = Part.makeLine((elem.attrib['x1'],elem.attrib['y1'],0), (elem.attrib['x2'],elem.attrib['y2'],0))
  edges.append(tmpedge);


#find parts that contain dimension lines
for elem in drawing.iterfind('board/libraries/library'):
  library = elem.attrib['name']
  for elem2 in elem.iterfind('packages/package'):
    part = elem2.attrib['name']
    for elem3 in elem2.iterfind('wire[@layer="20"]'):
      if library not in dimensionLibrary:
        dimensionLibrary[library] = {}
      if part not in dimensionLibrary[library]:
        dimensionLibrary[library][part] = []
      dimensionLibrary[library][part].append(Part.makeLine((elem3.attrib['x1'], elem3.attrib['y1'],0), (elem3.attrib['x2'],elem3.attrib['y2'],0)))

#use parts from library to finish list of dimensions
for elem in drawing.iterfind('board/elements/element'):
  if elem.attrib['library'] in dimensionLibrary and elem.attrib['package'] in dimensionLibrary[elem.attrib['library']]:
    if 'rot' in elem.attrib:
      rot = float(elem.attrib['rot'].translate(None, string.letters))
      mirror = elem.attrib['rot'].translate(None, string.digits)
    else:
      rot = 0
      mirror = '' #TODO: use!?
    for dimensionLineCpy in dimensionLibrary[elem.attrib['library']][elem.attrib['package']]:
      dimensionLineCpy.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), rot)
      dimensionLineCpy.translate(Base.Vector(float(elem.attrib['x']),float(elem.attrib['y']),0))
      edges.append(dimensionLineCpy)

for dirname, dirnames, filenames in os.walk(libFolder):
  for filename in filenames:
      file = filename.split('.')
      if (file[len(file)-1]=='stp' or file[len(file)-1]=='step'):
        ending = file.pop(len(file)-1) #remove fileending (.stp or .step)
        file = ".".join(file)
        if (file in packages):
          packages[file] = Part.read(os.path.join(dirname, filename))
          
    
for row in csvArray:
  if (row[0]=='package'):
    partname = row[6];
    if (row[8]!=''):
      partname = row[8];
    if (packages[partname] == '' and not partname in missingpackages):
      print "missing package " + partname
missingpackages[partname] = 'reported'
    elif packages[partname] != '':
      p = packages[partname].copy()
      p.rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),float(row[4]))
      if (float(row[7])<0):
        p.rotate(Base.Vector(0,0,0), Base.Vector(1,0,0), 180)
      p.Placement.Base = (row[2],row[3],row[7])
      parts.append(p)


#sort edges to form a single closed 2D shape
newEdges = [];
newEdges.append(edges.pop(0))
nextCoordinate = newEdges[0].Curve.EndPoint
while(len(edges)>0):
  for j, edge in enumerate(edges):
    if edges[j].Curve.StartPoint == nextCoordinate:
      nextCoordinate = edges[j].Curve.EndPoint
      newEdges.append(edges.pop(j))
    elif edges[j].Curve.EndPoint == nextCoordinate:
      nextCoordinate = edges[j].Curve.StartPoint
      newEdges.append(edges.pop(j))

edges = newEdges

#extrude 2D shape to get a 3D model of the pcb
dimension = Part.Wire(edges)
face = Part.Face(dimension)
face.translate(Base.Vector(0,0,-totalHeight/2))

extruded = face.extrude(Base.Vector(0,0,totalHeight))
for hole in holes:
  extruded = extruded.cut(hole)
for part in parts:
  extruded = extruded.fuse(part)
  #Part.show(part)

Part.show(extruded)

filename = QtGui.QFileDialog.getSaveFileName(None, 'SAVE as STEP Model','')
extruded.exportStep(filename)

