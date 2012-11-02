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
import string

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def getPlacedModel(part, model):
    if 'rot' in part.attrib:
      rot = float(part.attrib['rot'].translate(None, string.letters))
      mirror = part.attrib['rot'].translate(None, string.digits)
    else:
      rot = 0
      mirror='R'
    p = model.copy()
    p.translate(Base.Vector(0,0,totalHeight / 2))

    p.rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),-rot)
    mirrorMultiplicator = 1
    if (mirror[0] == 'M'):
      p.rotate(Base.Vector(0,0,0), Base.Vector(0,1,0), 180)
      mirrorMultiplicator = -1
    p.translate(Base.Vector(float(part.attrib['x']),float(part.attrib['y']),0))
    return p

libFolder = ''
filename = ''
libFolder = str(QtGui.QFileDialog.getExistingDirectory(None, "Select Directory for Libraries"))
filename = str(QtGui.QFileDialog.getOpenFileName(None, 'Open Eagle Board file',''))


totalHeight = 1.5 #TODO: read this from eagle file
holes = []
parts = []
edges = []
packages = {}
missingpackages = {}


tree = ET.ElementTree(file=filename)
root = tree.getroot()
drawing = root[0]
dimensionLibrary = {}
drillLibrary = {}
millingLibrary = {}

#find lines that make up the dimensions of pcbs directly
for elem in drawing.iterfind('board/plain/wire[@layer="20"]'):
  tmpedge = Part.makeLine((elem.attrib['x1'],elem.attrib['y1'],0), (elem.attrib['x2'],elem.attrib['y2'],0))
  edges.append(tmpedge);


#find parts that contain dimension lines or holes or millings
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
    for elem3 in elem2.iterfind('wire[@layer="46"]'):
      if library not in millingLibrary:
        millingLibrary[library] = {}
      if part not in millingLibrary[library]:
        millingLibrary[library][part] = []
      millingLibrary[library][part].append(Part.makeLine((elem3.attrib['x1'], elem3.attrib['y1'],0), (elem3.attrib['x2'],elem3.attrib['y2'],0)))
    for elem3 in elem2.iterfind('hole'):
      if library not in drillLibrary:
        drillLibrary[library] = {}
      if part not in drillLibrary[library]:
        drillLibrary[library][part] = []
      drillLibrary[library][part].append(Part.makeCylinder(float(elem3.attrib['drill']),totalHeight,Base.Vector(float(elem3.attrib['x']),float(elem3.attrib['y']),-totalHeight/2)))


for elem in drawing.iterfind('board/elements/element'):
  #use parts from library to finish list of dimensions
  if elem.attrib['library'] in dimensionLibrary and elem.attrib['package'] in dimensionLibrary[elem.attrib['library']]:
    getPlacedPart(elem, dimensionLibrary[elem.attrib['library']][elem.attrib['package']])
    edges.append(dimensionLineCpy)
  
  #collect used footprints
  footprint = elem.attrib['package']
  for attribute in elem.iterfind('attribute[@name="STEP"]'):
    footprint = attribute.attrib['value']
  packages[footprint] = ''

#look for files with ending .stp or .step and import the models
#if the packages are used on the pcb
for dirname, dirnames, filenames in os.walk(libFolder):
  for filename in filenames:
      file = filename.split('.') #attention: files might have more than one dot in their name
      if (file[len(file)-1]=='stp' or file[len(file)-1]=='step'):
        ending = file.pop(len(file)-1) #remove fileending (.stp or .step)
        file = ".".join(file)
        if (file in packages):
          packages[file] = Part.read(os.path.join(dirname, filename))


#insert parts in drawing using the already imported packages
for elem in drawing.iterfind('board/elements/element'):
  footprint = elem.attrib['package']
  for attribute in elem.iterfind('attribute[@name="STEP"]'):
    footprint = attribute.attrib['value']
  if (packages[footprint] == '' and footprint not in missingpackages):
    print "missing package ", footprint
    missingpackages[footprint] = 'reported'
  elif packages[footprint] != '':
    p = getPlacedModel(elem, packages[footprint])
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
#for hole in holes:
#  extruded = extruded.cut(hole)
for part in parts:
  extruded = extruded.fuse(part)
  #Part.show(part)

Part.show(extruded)

filename = QtGui.QFileDialog.getSaveFileName(None, 'SAVE as STEP Model','')
extruded.exportStep(filename)

