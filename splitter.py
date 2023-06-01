import re

import svgwrite
import os

import numpy as np

filename="dragon" # just add the name of the file, not including the gcode extension

#scaleFactor=3.543307 # see https://svgwrite.readthedocs.io/en/latest/overview.html#units
scaleFactor=3.81 # see https://svgwrite.readthedocs.io/en/latest/overview.html#units
largeAreaThreshold=1500 # if the enclosed area of the layer is less than this value, then no layer number is printed. 
smallAreaThreshold=100
dwg=None
boundingboxPath=None

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





instructionPattern = r'(G\d)\s(X[\d.]+)?\s(Y[\d.]+)?(\sE[\d.]+)?'
layerMatchPattern = r";LAYER:(\d+)"
printEndedPattern=r'M140 S0'

speedReplacePattern=r'(F\d+)\s?' #F6000 for example

def removeSpeedParameter(linstruction):

    newInstruction = re.sub(speedReplacePattern, '', linstruction)
    #print(newInstruction)

    return newInstruction



def scaleCoordinate(co):
    return str(float(co)*scaleFactor)

# using the coordinates of the layer, determine its weighted center. The layer number would be added there. 
def findCentroid(lPathArray):
    #in the path array x and Y cocordinates come one after the other as such [x0,y0,x1,y1,x2,y2,x3,y3...]
    lxsum=0
    lysum=0
    lpointcount=0
    for i in range (2, len(lPathArray)-1, 2):
        lxsum=lxsum+float(lPathArray[i])
        lysum=lysum+float(lPathArray[i+1])
        lpointcount=lpointcount+1


    return lxsum/lpointcount, lysum/lpointcount




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



    

    


def calculateSmallestBoundingBoxExtents(linstructions):

    lshapeMaxX=0
    lshapeMinX=1000
    lshapeMaxY=0
    lshapeMinY=1000

    for linstruction in linstructions:

        linstruction=removeSpeedParameter(linstruction)

        instructionMatch = re.match(instructionPattern, linstruction)

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
        
                #print("{},{},{},{}".format(lshapeMinX,lshapeMaxX,lshapeMinY,lshapeMaxY))


        


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
                lpathArray[i]=scaleCoordinate(lpathArray[i])
            lpathArray[0]="M"+lpathArray[0] # the first corodinate is always a move and comes from a G0 command.

            lpathcoordinates=",".join(lpathArray) # create a comma seperated path string
            lpathcoordinates=lpathcoordinates+" Z" #Adding a Z makes the path closed with the first point in the path       
            return lpathcoordinates   



           
        







def saveCurrentPath(lpathArray):
    # We need to computer the area enclosed by the path, 
    # because if the area is too small, no point writing the layer number in it
    #print(patharray)
    area=computerArea(lpathArray)
    # if(area>0):
    #     print ("Area is {} sq.mm .".format(area))
    #print (lpathArray)
    paths=len(lpathArray)
     # the first corodinate is always a move and comes from a G0 command.
    
    if(paths==2): # just a G0 command, we can dopuble the array in size to allow splitting it ahead in two parts
        lpathArray=lpathArray*2
        paths=len(lpathArray)
       # print(paths)
    
    
    splitArray=[] 
        

   
    splitArray=np.array_split(lpathArray, 2)
        
    #print(lpathArray)
    #print(splitArray)

    # when the array is split in two halves, if the number of elements in the parts is 
    # odd, the XY combinations have to be even. Check if the number of elements in the split is odd.

    #If they are odd, just remove the first element from second part, and add it at the end of the first part. 
    # To make a wider gap in the path, also ignore the first couple of XY coordinates in the second half. 

    if(len(splitArray[0])%2==1):

        splitArray[0]=np.append(splitArray[0], splitArray[1][0]) # take the first element from second part and put at end of first
        splitArray[1]=splitArray[1][3:] # 

    #print(len(splitArray[0]))
    #print(len(splitArray[1]))
    
    for subArray in splitArray:
        
        subArray[0]="M"+subArray[0]
        pathcoordinates=",".join(subArray) # create a comma seperated path string
        pathcoordinates=pathcoordinates #Adding a Z makes the path closed with the first point in the path
        dwg.add(dwg.path( d=pathcoordinates, stroke="#000", fill="none", stroke_width=1))
    
    if(area > largeAreaThreshold): # only add text if area is above the threashold. 
        centroidx, centroidy=findCentroid(lpathArray) # computer the weighted center of the enclosed path

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

boxPathString=calculateSmallestBoundingBoxExtents(instructions)
#print(boxPathString)






for instruction in instructions:

    layerMatch=re.match(layerMatchPattern, instruction)
    if layerMatch:
        layerNumber=layerMatch.group(1)
        print ("Layer {} starts.".format(layerNumber))

       # print(patharray)
        if dwg:
            if len(patharray)>0:
                # Draw an irregular polygon

             saveCurrentPath(patharray) 
             #print(boxPathString)             
             dwg.add(dwg.path( d=boxPathString, stroke="#000", fill="none", stroke_width=1))
             dwg.save()  
               
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
            dwg.add(dwg.path( d=boxPathString, stroke="#000", fill="none", stroke_width=1))
            dwg.save() 
            
            dwg = svgwrite.Drawing(filename+"/layer_"+layerNumber+'.svg') 
        patharray=[]
        exit()


    instructionMatch = re.match(instructionPattern, instruction)
    if instructionMatch:
        command=instructionMatch.group(1)
        xVal=instructionMatch.group(2)[1:]
        yVal=instructionMatch.group(3)[1:]
        eVal=instructionMatch.group(4)

        xVal=scaleCoordinate(xVal)
        yVal=scaleCoordinate(yVal)

        if(command=="G0" and  layerStarted):
            #print("Adding")
            #print("G0 X:{}, y:{},".format(xVal, yVal))

            patharray.append(xVal)
            patharray.append(yVal)  

            saveCurrentPath(patharray)
            dwg.add(dwg.path( d=boxPathString, stroke="#000", fill="none", stroke_width=1))
            dwg.save() 
            patharray=[]
            

        if( command=="G1" and layerStarted):   
            #print("G1 X:{}, y:{},".format(xVal, yVal))

            patharray.append(xVal)
            patharray.append(yVal)
            
            
        
    else:
        continue

  














   
    
