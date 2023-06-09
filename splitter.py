import re

import svgwrite
import os
import math

import numpy as np

from shapely import geometry

filename="LionLarge" # just add the name of the file, not including the extension

#scaleFactor=3.543307 # see https://svgwrite.readthedocs.io/en/latest/overview.html#units
scaleFactor=3.831070 # see https://svgwrite.readthedocs.io/en/latest/overview.html#units
largeAreaThreshold=1500 # if the enclosed area of the layer is less than this value, then no layer number is printed. 
smallAreaThreshold=100
dwg=None
boundingboxPath=None
splitPathSwitch=False

addBoundary=False

lastX=200
lastY=100

xsum=0
ysum=0
pointcount=0

layerStarted=False
patharray=[]

maxY=297
maxX=210

shapeMaxX=0
shapeMinX=10000

shapeMaxY=0
shapeMinY=1000

maxAreaLayer=0
maxArea=0
metaDataFile=None

lastLayerAreas=[0]
currentLayerAreas=[0]

LayersWithCentroidOutside=[]

xOffset=0
yOffset=0

manualXOffset=14.32
manualYOffset=43.143




instructionPattern = r'(G\d)\s(X[-?\d.]+)?\s(Y[-?\d.]+)?(\sE[\d.]+)?'
layerMatchPattern = r";LAYER:(\d+)"
printEndedPattern=r'M140 S0'

speedReplacePattern=r'(F\d+)\s?' #F6000 for example

def removeSpeedParameter(linstruction):

    newInstruction = re.sub(speedReplacePattern, '', linstruction)
    #print(newInstruction)

    return newInstruction



def scaleandShiftCoordinate(co, axis):
    global xOffset, yOffset

    scaled=float(co)*scaleFactor

    if(axis=="x"):

        shifted=scaled+xOffset

    if(axis=="y"):

        shifted=scaled+yOffset

    return str(shifted)

# using the coordinates of the layer, determine its weighted center. The layer number would be added there. 
def findCentroid(lPathArray):
    #in the path array x and Y cocordinates come one after the other as such [x0,y0,x1,y1,x2,y2,x3,y3...]
    # lxsum=0
    # lysum=0
    # lpointcount=0
    # areaCoordinates=[]
    # for i in range (2, len(lPathArray)-1, 2):
    #     lxsum=lxsum+float(lPathArray[i])
    #     lysum=lysum+float(lPathArray[i+1])
    #     areaCoordinates.append((float(lPathArray[i]),float(lPathArray[i+1])))
    #     lpointcount=lpointcount+1
    moveDistance=20
    spokes=[]
    spokes.append((moveDistance,0))
    spokes.append((moveDistance*1.44, moveDistance*1.44))
    spokes.append((0,moveDistance))
    spokes.append((-moveDistance*1.44, moveDistance*1.44))

    spokes.append((-moveDistance,0))
    spokes.append((-moveDistance*1.44, -moveDistance*1.44))
    spokes.append((0,-moveDistance))
    spokes.append((moveDistance*1.44, -moveDistance*1.44))

    areaCoordinates=[]
    for i in range (2, len(lPathArray)-1, 2):        
        areaCoordinates.append((float(lPathArray[i]),float(lPathArray[i+1])))
        
    

    line = geometry.LineString(areaCoordinates)    
    polygon = geometry.Polygon(line)
    

    centroid=polygon.centroid
    point = geometry.Point(centroid)
    pointStatus=polygon.contains(point)  and polygon.exterior.distance(point) > 30

    if(not pointStatus):
        for transformPoint in spokes:
            newpoint=geometry.Point(transformPoint[0] + centroid.x,transformPoint[1] + centroid.y) 
            pointStatus=polygon.contains(newpoint)  and polygon.exterior.distance(newpoint) > 30
            if(pointStatus):
                return newpoint.x, newpoint.y, pointStatus
            else:
                newpoint=None

    return centroid.x, centroid.y, pointStatus


     


    




def computerArea(lpathArray):
    #in the path array x and Y cocordinates come one after the other as such [x0,y0,x1,y1,x2,y2,x3,y3...]
    areaDelta=0
    if len(lpathArray)<6:
        return 0
    for i in range (2, len(lpathArray)-3, 2): # ignore the first x and y combination
        # see https://www.mathopenref.com/coordpolygonarea.html
        areaDelta=areaDelta+float(lpathArray[i]) * float(lpathArray[i+3])-float(lpathArray[i+1]) * float(lpathArray[i+2])

    # do the same for second ( First corodinate is just a positioning G0) and last corodinates combination
    areaDelta=areaDelta + float(lpathArray[3]) * float(lpathArray[-2])-float(lpathArray[2]) *float(lpathArray[-1])

    totalArea=areaDelta/2

    return totalArea


def computeOffsetFromOrigin(linstructions):

    lshapeMaxX=0
    lshapeMinX=1000
    lshapeMaxY=0
    lshapeMinY=1000

    for linstruction in linstructions:

        linstruction=removeSpeedParameter(linstruction)
        #print(linstruction)
        instructionMatch = re.match(instructionPattern, linstruction)
        #print(instructionMatch)
        if instructionMatch:
            command=instructionMatch.group(1)
            xVal=instructionMatch.group(2)[1:]
            yVal=instructionMatch.group(3)[1:]
            eVal=instructionMatch.group(4)

            xVal=float(xVal)
            yVal=float(yVal)

            

            

            if( command=="G1"):

                if(xVal>lshapeMaxX):
                    lshapeMaxX=xVal;
                if(xVal<lshapeMinX):
                    lshapeMinX=xVal
                if(yVal>lshapeMaxY):
                    lshapeMaxY=yVal;
                if(yVal<lshapeMinY):
                    lshapeMinY=yVal;
        
            


        boundingBoxWidthmm=math.ceil(lshapeMaxX-lshapeMinX)
        boundingBoxHeightmm=math.ceil(lshapeMaxY-lshapeMinY)

        boundingBoxWidthin=math.ceil(boundingBoxWidthmm/25.4)
        boundingBoxHeightin=math.ceil(boundingBoxHeightmm/25.4)

        # boundingBoxWidthmm=lshapeMaxX-lshapeMinX
        # boundingBoxHeightmm=lshapeMaxY-lshapeMinY

        # boundingBoxWidthin=boundingBoxWidthmm/25.4
        # boundingBoxHeightin=boundingBoxHeightmm/25.4


        
        
        printEndedMatch=re.match(printEndedPattern, linstruction)

        if printEndedMatch: # This is the Exit condition, as the end of the print has been reached
            global xOffset, yOffset, manualXOffset, manualYOffset

            xOffset=(lshapeMinX*scaleFactor * -1)+ manualXOffset
            yOffset=(lshapeMinY*scaleFactor * -1)+ manualYOffset


            #print("{},{},{},{}".format(lshapeMinX*scaleFactor,lshapeMinY*scaleFactor,lshapeMaxX*scaleFactor,lshapeMaxY*scaleFactor))

           





    

    


def calculateSmallestBoundingBoxExtents(linstructions):

    lshapeMaxX=0
    lshapeMinX=1000
    lshapeMaxY=0
    lshapeMinY=1000

    for linstruction in linstructions:

        linstruction=removeSpeedParameter(linstruction)
        #print(linstruction)
        instructionMatch = re.match(instructionPattern, linstruction)
        #print(instructionMatch)
        if instructionMatch:
            command=instructionMatch.group(1)
            xVal=instructionMatch.group(2)[1:]
            yVal=instructionMatch.group(3)[1:]
            eVal=instructionMatch.group(4)

            xVal=float(xVal)
            yVal=float(yVal)

            

            

            if( command=="G1"):

                if(xVal>lshapeMaxX):
                    lshapeMaxX=xVal;
                if(xVal<lshapeMinX):
                    lshapeMinX=xVal
                if(yVal>lshapeMaxY):
                    lshapeMaxY=yVal;
                if(yVal<lshapeMinY):
                    lshapeMinY=yVal;
        
            


        boundingBoxWidthmm=math.ceil(lshapeMaxX-lshapeMinX)
        boundingBoxHeightmm=math.ceil(lshapeMaxY-lshapeMinY)

        boundingBoxWidthin=math.ceil(boundingBoxWidthmm/25.4)
        boundingBoxHeightin=math.ceil(boundingBoxHeightmm/25.4)

        # boundingBoxWidthmm=lshapeMaxX-lshapeMinX
        # boundingBoxHeightmm=lshapeMaxY-lshapeMinY

        # boundingBoxWidthin=boundingBoxWidthmm/25.4
        # boundingBoxHeightin=boundingBoxHeightmm/25.4


        
        
        printEndedMatch=re.match(printEndedPattern, linstruction)

        if printEndedMatch: # This is the Exit conditiopn, as the end of the print has been reached

            #adjust and add margins to max and mins
            lshapeMinX=lshapeMinX-10
            lshapeMinY=lshapeMinY-10
            lshapeMaxX=lshapeMaxX+10
            lshapeMaxY=lshapeMaxY+10

            lpathArray=[]
            #Move Drawing point to left top corner
            lpathArray.append(str(lshapeMinX))
            lpathArray.append(str(lshapeMinY))



            #Draw a horizontal line to right top corner
            lpathArray.append(str(lshapeMaxX))
            lpathArray.append(str(lshapeMinY))


            #Draw a vertical line to left  bottom corner
            lpathArray.append(str(lshapeMaxX))
            lpathArray.append(str(lshapeMaxY))

            #Draw a horizontal line to right bottom corner
            lpathArray.append(str(lshapeMinX))
            lpathArray.append(str(lshapeMaxY))

            #Draw a vertical line to left top corner
            lpathArray.append(str(lshapeMinX))
            lpathArray.append(str(lshapeMinY))

            #print(lpathArray)
            #print(len(lpathArray))
            for i in range(0,len(lpathArray)):

                if(i%2==0):
                    lpathArray[i]=scaleandShiftCoordinate(lpathArray[i], "x")
                
                if(i%2==1):
                    lpathArray[i]=scaleandShiftCoordinate(lpathArray[i], "y")

            lpathArray[0]="M"+lpathArray[0] # the first corodinate is always a move and comes from a G0 command.

            lpathcoordinates=",".join(lpathArray) # create a comma seperated path string
            lpathcoordinates=lpathcoordinates+" Z" #Adding a Z makes the path closed with the first point in the path 
            metaDataFile.write ("Bounding Box Dimensions:\n")
            metaDataFile.write("{}mm Width X {}mm Height \n".format(boundingBoxWidthmm,boundingBoxHeightmm ))  
            metaDataFile.write("{}in Width X {}in Height \n".format(boundingBoxWidthin, boundingBoxHeightin ))  
            
            
            return lpathcoordinates   



           
        







def saveCurrentPath(lpathArray):
    # We need to computer the area enclosed by the path, 
    # because if the area is too small, no point writing the layer number in it
    #print(patharray)
    area=computerArea(lpathArray)
    global maxArea, maxAreaLayer, currentLayerAreas, lastLayerAreas, xOffset, yOffset

    if(area>0):
        currentLayerAreas.append(math.floor(area))
    if(area>maxArea):
        maxArea=area
        maxAreaLayer=layerNumber
    # if(area>0):
    #     print ("Area is {} sq.mm .".format(area))
    #print (lpathArray)
    paths=len(lpathArray)

    


    if (splitPathSwitch):
        # the first corodinate is always a move and comes from a G0 command.
        split=True
        if(paths==2): # just a G0 command, we can dopuble the array in size to allow splitting it ahead in two parts
            lpathArray=lpathArray*2
            paths=len(lpathArray)
            split=False
            #print(paths)
        
        
        splitArray=[] 
            

    
        splitArray=np.array_split(lpathArray, 2)
        #print("**Printing Path Arrays")     
        #print(lpathArray)
        #print("**Printing Split Arrays")
        #print(splitArray)

        # when the array is split in two halves, if the number of elements in the parts is 
        # odd, the XY combinations have to be even. Check if the number of elements in the split is odd.
        #print("The Length of the Path Array is  {}".format(len(patharray)))
        traceArray0=[]
        traceArray1=[]
        if(split):

            #If they are odd, just remove the first element from second part, and add it at the end of the first part. 
            # To make a wider gap in the path, also ignore the first couple of XY coordinates in the second half. 
            
            
            if(len(splitArray[0])%2==1):           

                splitArray[0]=np.append(splitArray[0], splitArray[1][0]) # take the first element from second part and put at end of first
                splitArray[1]=splitArray[1][1:] # 

                



            
            #print(splitArray)

            if(len(splitArray[0])>2):
                traceArray0.append(splitArray[0][-4])
                traceArray0.append(splitArray[0][-3]) 

            traceArray0.append(splitArray[0][-2])
            traceArray0.append(splitArray[0][-1])   
            traceArray0.append(splitArray[1][0]) 
            traceArray0.append(splitArray[1][1])  

            if(len(splitArray[1])>2):          
                traceArray0.append(splitArray[1][2]) 
                traceArray0.append(splitArray[1][3]) 

            if(len(splitArray[1])>2):   
                traceArray1.append(splitArray[1][-4])
                traceArray1.append(splitArray[1][-3]) 
                    
            traceArray1.append(splitArray[1][-2])
            traceArray1.append(splitArray[1][-1])   
            traceArray1.append(splitArray[0][0]) 
            traceArray1.append(splitArray[0][1])         
            



            splitArray[0]=splitArray[0][:-2] # take the first element from second part and put at end of first
            splitArray[1]=splitArray[1][2:] # 

            #print("Printing Split Arrays after Manipulation")
            #print("First Part of the split is {} elements long".format(len(splitArray[0])))
            #print("Second Part of the split is {} elements long".format(len(splitArray[1])))
            #print(splitArray[1])
            #print("Printing Trace Arrays")
            #print(traceArray)

        
        for subArray in splitArray:

            if(len(subArray)>0):
                subArray[0]="M"+subArray[0]
                pathcoordinates=",".join(subArray) # create a comma seperated path string
                pathcoordinates=pathcoordinates + 'Z'  #Adding a Z makes the path closed with the first point in the path
                dwg.add(dwg.path( d=pathcoordinates, stroke="#000", fill="none", stroke_width=1))

    


    """ # Added Red lines for just tracing with a laser, no cut required. 
    if(len(traceArray0)>0):
        traceArray0[0]="M"+traceArray0[0]
        pathcoordinates=",".join(traceArray0) # create a comma seperated path string
        pathcoordinates=pathcoordinates  #Adding a Z makes the path closed with the first point in the path
        dwg.add(dwg.path( d=pathcoordinates, stroke="#F00", fill="none", stroke_width=1))
    
    if(len(traceArray1)>0):
        traceArray1[0]="M"+traceArray1[0]
        pathcoordinates=",".join(traceArray1) # create a comma seperated path string
        pathcoordinates=pathcoordinates  #Adding a Z makes the path closed with the first point in the path
        dwg.add(dwg.path( d=pathcoordinates, stroke="#F00", fill="none", stroke_width=1)) """

    if (not splitPathSwitch): 
        lpathArray[0]="M"+lpathArray[0]
        pathcoordinates=",".join(lpathArray) # create a comma seperated path string
        pathcoordinates=pathcoordinates + 'Z'  #Adding a Z makes the path closed with the first point in the path
        dwg.add(dwg.path( d=pathcoordinates, stroke="#000", fill="none", stroke_width=1))
    
    
    if(area > largeAreaThreshold): # only add text if area is above the threashold. 
        centroidx, centroidy, positionStatus=findCentroid(lpathArray) # compute the weighted center of the enclosed path

        if(not positionStatus):
            LayersWithCentroidOutside.append(layerNumber)

        dwg.add(dwg.text(layerNumber,insert=(centroidx,centroidy), # add the text at the weighted center
                stroke='#F00',
                fill='#FFF',
                font_size='20px',
                font_weight="bold")
            )
        
    
    

    dwg.save() # save the path



#PosCheck = re.compile('(?i)^[gG0-3]{1,3}(?:\s+x-?(?P<x>[0-9.]{1,15})|\s+y-?(?P<y>[0-9.]{1,15})|\s+z-?(?P<z>[0-9.]{1,15}))*$')




GcodeFile= open(filename+'.gcode', 'r')





instructions = GcodeFile.readlines()
count = 0

isExists=os.path.exists(filename)

if not isExists:

   # Create a new directory because it does not exist
   os.makedirs(filename)

 
metaDataFile=open(filename+"/"+filename+'.txt', 'w')

boxPathString=calculateSmallestBoundingBoxExtents(instructions)


#print("{},{}".format(xOffset, yOffset))

computeOffsetFromOrigin(instructions)

#print("{},{}".format(xOffset, yOffset))
#exit()
#print(boxPathString)




printEnded=False

for instruction in instructions:

    layerMatch=re.match(layerMatchPattern, instruction)
    if layerMatch and not printEnded:
        layerNumber=layerMatch.group(1)
        print ("Layer {} starts.".format(layerNumber))

       # print(patharray)
        if dwg:
            if len(patharray)>0:
                # Draw an irregular polygon

             saveCurrentPath(patharray) 
             #print(boxPathString)             
             if(addBoundary):
                dwg.add(dwg.path( d=boxPathString, stroke="#000", fill="none", stroke_width=1))
                dwg.save() 
        
        
        currentLayerAreas.sort()
        if(int(layerNumber)>0):
            curr_largestArea=currentLayerAreas[-1]
            last_largestArea=lastLayerAreas[-1]
            if(curr_largestArea>last_largestArea): # The largest Area in current layer is larger than largest area in last layer
                # in the metadata file, write the layer number with larger area first, then smaller area.
                # The outline of the smaller area needs to be imprinted on the larger area.
                metaDataFile.write("#{},{}\n".format(int(layerNumber), int(layerNumber)-1))
            else:
                 metaDataFile.write("#{},{}\n".format(int(layerNumber)-1, int(layerNumber)))
            lastLayerAreas=currentLayerAreas
        currentLayerAreas=[]     
        dwg = svgwrite.Drawing(filename+"/layer_"+layerNumber+'.svg')        
        patharray=[]
        layerStarted=True  
        #p=input()  
        continue     

    #start a new file to write to.

    #print(instruction)
    instruction=removeSpeedParameter(instruction)
    #print(instruction)
    printEndedMatch=re.match(printEndedPattern, instruction)

    if printEndedMatch: # This is the Exit conditiopn, as the end of the print has been reached

        # Draw an irregular polygon
        if(len(patharray)>0):
            saveCurrentPath(patharray)
            #print(boxPathString)    
            # 
            if(addBoundary):
                dwg.add(dwg.path( d=boxPathString, stroke="#000", fill="none", stroke_width=1))
                dwg.save()


            currentLayerAreas.sort()
            if(int(layerNumber)>0):
                curr_largestArea=currentLayerAreas[-1]
                last_largestArea=lastLayerAreas[-1]
                if(curr_largestArea>last_largestArea): # The largest Area in current layer is larger than largest area in last layer
                    # in the metadata file, write the layer number with larger area first, then smaller area.
                    # The outline of the smaller area needs to be imprinted on the larger area.
                    metaDataFile.write("#{},{}\n".format(int(layerNumber), int(layerNumber)-1))
                else:
                        metaDataFile.write("#{},{}\n".format(int(layerNumber)-1, int(layerNumber)))
                lastLayerAreas=currentLayerAreas
                currentLayerAreas=[]               
           
            
            dwg = svgwrite.Drawing(filename+"/layer_"+layerNumber+'.svg') 
        patharray=[]
        printEnded=True
        break


    instructionMatch = re.match(instructionPattern, instruction)
    if instructionMatch:
        command=instructionMatch.group(1)
        xVal=instructionMatch.group(2)[1:]
        yVal=instructionMatch.group(3)[1:]
        eVal=instructionMatch.group(4)

        xVal=scaleandShiftCoordinate(xVal, "x")
        yVal=scaleandShiftCoordinate(yVal, "y")

        

        if(command=="G0" and  layerStarted):
            #print("Adding")
            #print("G0 X:{}, y:{},".format(xVal, yVal))

            patharray.append(xVal)
            patharray.append(yVal)  

            saveCurrentPath(patharray)

            if(addBoundary):
                dwg.add(dwg.path( d=boxPathString, stroke="#000", fill="none", stroke_width=1))
                dwg.save() 
            patharray=[]
            

        if( command=="G1" and layerStarted):   
            #print("G1 X:{}, y:{},".format(xVal, yVal))

            patharray.append(xVal)
            patharray.append(yVal)
            
            



#print(maxAreaLayer)
metaDataFile.write("The Layer with the Max Area is {}\n". format(maxAreaLayer))

metaDataFile.write("The following Layers {} Have their centroid outside the region".format(LayersWithCentroidOutside))
metaDataFile.close()







   
    
