import re

import svgwrite
import os
import math

import numpy as np
import shutil

from shapely import geometry

# importing element tree
# under the alias of ET
import xml.etree.ElementTree as ET

# importing element tree
# under the alias of TT
import xml.etree.ElementTree as TT

folderName="Triceratops"
processedFolderName=folderName+"Processed"

skipCount=30

def getLargestPolygonPoints(fileName):

    aTree=TT.parse(fileName)

    
    # getting the parent tag of
    # the xml document
    #baseRoot=basetree.getroot()
    aroot = aTree.getroot()

    # printing the root (parent) tag
    # of the xml document, along with
    # its memory location
    namespace=aroot.tag.split('}')[0].strip('{')
    largestPath=None
    largestPathArea=0
    for child in aroot:
        tagName=child.tag
        tagName=tagName.replace(namespace, "")
        tagName=tagName.replace("{}", "")

        if(tagName=="path"):
            #child.attrib["stroke"]="#F00"
            #print(child.attrib["stroke"])

            # for every coordinate from the top layer, we only want circular spots on the base layer.
            # Every Path that we have, the first is a move command
            # all the co ordinates are comma seperated, with the form X0, Y0, X1, Y1, X2, Y2
            pathCoordinates=child.attrib["d"]
            lpathArray=pathCoordinates.split(",")

            pathArea=computerArea(lpathArray)

            if(pathArea>0 and pathArea > largestPathArea):
                largestPathArea=pathArea
                largestPath=lpathArray
                #print(pathArea)

    largestPath[0]=largestPath[0].replace("M", "")
    #print(largestPath)
    setArray=[]
    for i in range(0, len(largestPath),2):
        setArray.append((largestPath[i], largestPath[i+1]))

    #print(largestPath)
    #print(setArray)
    return setArray




def computerArea(lpathArray):
    #in the path array x and Y cocordinates come one after the other as such [x0,y0,x1,y1,x2,y2,x3,y3...]
    areaDelta=0
    if len(lpathArray)<6:
        return 0
    lpathArray[-1]=lpathArray[-1][0:-1]
    for i in range (2, len(lpathArray)-3, 2): # ignore the first x and y combination
        # see https://www.mathopenref.com/coordpolygonarea.html
        areaDelta=areaDelta+float(lpathArray[i]) * float(lpathArray[i+3])-float(lpathArray[i+1]) * float(lpathArray[i+2])

    # do the same for second ( First corodinate is just a positioning G0) and last corodinates combination
    areaDelta=areaDelta + float(lpathArray[3]) * float(lpathArray[-2])-float(lpathArray[2]) *float(lpathArray[-1])

    totalArea=areaDelta/2

    return totalArea





isExists=os.path.exists(processedFolderName)

if not isExists:

   # Create a new directory because it does not exist
   os.makedirs(processedFolderName)







def makeCircleElement(x,y):

    # circleElement=ET.Element("circle")
    # circleElement.attrib["cx"]=x
    # circleElement.attrib["cy"]=y
    # circleElement.attrib["stroke"]="#F00"
    # circleElement.attrib["stroke-width"]="1"
    # circleElement.attrib["fill"]="none"

    # return circleElement

    return '<circle cx="{}" cy="{}" r="1" stroke="#F00" stroke-width="1" fill="None" />'.format(x,y)


metadataFile=open(folderName+"/"+folderName+".txt")
metaInfo=metadataFile.readlines()

layerInfoRegex=r'#(\d+),(\d+)?'
baseLayerNumber=0
topLayerNumber=0
for line in metaInfo:
    infoMatch = re.match(layerInfoRegex, line)
    #print(instructionMatch)
    if infoMatch:
        baseLayerNumber=infoMatch.group(1)
        topLayerNumber=infoMatch.group(2)
         

        baseLayerFileName=folderName+"/"+'layer_'+str(baseLayerNumber)+'.svg'
        topLayerFileName=folderName+"/"+'layer_'+str(topLayerNumber)+'.svg'

        boundingpolygon=getLargestPolygonPoints(baseLayerFileName)
        line = geometry.LineString(boundingpolygon)
        #point = geometry.Point(Point_X, Point_Y)
        polygon = geometry.Polygon(line)

        #exit()
        #basetree = ET.parse(baseLayerFileName)
        topTree=ET.parse(topLayerFileName)

        baseFile=open(baseLayerFileName, 'r')
        baseFileContent= baseFile.read()
        baseFileContent=baseFileContent[:-6] # Remove last instance of svg

        #print(baseFileContent)
        #exit()


    
        # getting the parent tag of
        # the xml document
        #baseRoot=basetree.getroot()
        toproot = topTree.getroot()
        
        # printing the root (parent) tag
        # of the xml document, along with
        # its memory location
        namespace=toproot.tag.split('}')[0].strip('{')
        circleString=""
        for child in toproot:
            tagName=child.tag
            tagName=tagName.replace(namespace, "")
            tagName=tagName.replace("{}", "")

            if(tagName=="path"):
                #child.attrib["stroke"]="#F00"
                #print(child.attrib["stroke"])

                # for every coordinate from the top layer, we only want circular spots on the base layer.
                # Every Path that we have, the first is a move command
                # all the co ordinates are comma seperated, with the form X0, Y0, X1, Y1, X2, Y2
                pathCoordinates=child.attrib["d"]
                pathArray=pathCoordinates.split(",")
                pathArray[-1]=pathArray[-1][0:-1] # Remove the trailing Z

                # if(len(pathArray)<100):
                #     continue

                

                for index in range(2,len(pathArray),skipCount):
                    point = geometry.Point(pathArray[index],pathArray[index+1])    
                    if(polygon.contains(point)):
                        pointDistance=polygon.exterior.distance(point)
                        if(pointDistance>10):
                            circle=makeCircleElement(pathArray[index],pathArray[index+1])  
                            circleString=circleString+circle
                    #print(circle)
                    #baseRoot.append(circle)

                
            

        baseFileContent=baseFileContent+circleString+"</svg>"
        #print(baseFileContent)

        

        newFileName=processedFolderName+"/"+'layer_'+str(baseLayerNumber)+'.svg'
        newLayerFile=open(newFileName, 'w')
        newLayerFile.write(baseFileContent)
        newLayerFile.close()
        #basetree.write(newFileName)



# #Copy the last layer without any change

# src=folderName+"/"+'layer_'+str(layerCount-1)+'.svg'
# dst=processedFolderName+"/"+'layer_'+str(layerCount-1)+'.svg'
# shutil.copyfile(src, dst)



    

    

 
