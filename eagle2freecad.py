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


csvArray = []
totalHeight = 0
holes = []
parts = []
edges = []
packages = {}

filename = QtGui.QFileDialog.getOpenFileName(None, 'Open file','')

libFolder = ''

with open(filename, 'rb') as csvfile:
  reader = csv.reader(csvfile, delimiter=';', quotechar='|')
  for row in reader:
    csvArray.append(row)
   
  for row in csvArray:  
    if (row[0]=='settings'):
      libFolder = row[1]
    if (row[0]=='outline-complete'):
      totalHeight = float(row[1])
    if (row[0]=='outline-line'):
      tmpedge = Part.makeLine((row[1],row[2],0), (row[3],row[4],0))
      edges.append(tmpedge);
    if (row[0]=='hole'):
      partCylinder = Part.makeCylinder(float(row[3]),float(row[4])*2,Base.Vector(float(row[1]),float(row[2]),-totalHeight/2),Base.Vector(0,0,1),360)
      holes.append(partCylinder)
    if (row[0]=='package'):
      if (row[8]!=''):
        packages[row[8]]=''
      else:
        packages[row[6]]=''
    
    
  for dirname, dirnames, filenames in os.walk(libFolder):
    for filename in filenames:
        #print os.path.join(dirname, filename)
        file = filename.split('.')
        #print file
        if (file[len(file)-1]=='stp' or file[len(file)-1]=='step'):
          file.pop(len(file)-1) #remove fileending (.stp or .step)
          file = ".".join(file)
          #print '-->' + file
          if (file in packages):
            packages[file] = Part.read(os.path.join(dirname, filename))
            
      
  for row in csvArray:
    if (row[0]=='package'):
      #package;C1;15.840;3.440;90;10µ;C0805;0.800;(OPTIONAL STEP MODEL NAME)
      partname = row[6];
      if (row[8]!=''):
        partname = row[8];
      if (packages[partname] == ''):
        print "missing package " + partname
      else:
        p = packages[partname].copy()
        p.rotate(Base.Vector(0,0,0),Base.Vector(0,0,1),float(row[4]))
        if (float(row[7])<0):
          p.rotate(Base.Vector(0,0,0), Base.Vector(1,0,0), 180)
        p.Placement.Base = (row[2],row[3],row[7])
        parts.append(p)

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

