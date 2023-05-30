import re

import svgwrite

filename="dragon"
#scaleFactor=3.543307 # see https://svgwrite.readthedocs.io/en/latest/overview.html#units
scaleFactor=3.81 # see https://svgwrite.readthedocs.io/en/latest/overview.html#units
areaThreshold=4000
dwg=None

lastX=200
lastY=100

xsum=0
ysum=0
pointcount=0;

layerStarted=False
patharray=[]



def scaleCoordinate(co):
    return str(float(co)*scaleFactor)


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
        areaDelta=areaDelta+float(lpathArray[i]) *float(lpathArray[i+3])-float(lpathArray[i+1]) *float(lpathArray[i+2])

    # do the same for second ( First corodinate is just a positioning G0) and last corodinates combination
    areaDelta=areaDelta + float(lpathArray[3]) * float(lpathArray[-2])-float(lpathArray[2]) *float(lpathArray[-1])

    totalArea=areaDelta/2

    return totalArea


def saveCurrentPath(lpathArray):
                # We need to computer the area enclosed by the path, 
                # because if the area is too small, no point writing the layer number in it
                #print(patharray)
                area=computerArea(lpathArray)
                if(area>0):
                    print ("Area is {} sq.mm .".format(area))
                lpathArray[0]="M"+lpathArray[0] # the first corodinate is always a move and comes from a G0 command.
                
                pathcoordinates=",".join(lpathArray) # create a comma seperated path string
                pathcoordinates=pathcoordinates+" Z" #Adding a Z makes the path closed with the first point in the path
                dwg.add(dwg.path( d=pathcoordinates, stroke="#000", fill="none", stroke_width=1))
                
                if(pointcount>0 and area> areaThreshold): # only add text if area is above the threashold. 
                    centroidx, centroidy=findCentroid(lpathArray) # computer the weighted center of the enclosed path

                    dwg.add(dwg.text(layerNumber,insert=(centroidx,centroidy), # add the text at the weighted center
                            stroke='#F00',
                            fill='#FFF',
                            font_size='30px',
                            font_weight="bold")
                        )
                

                dwg.save() # save the path



#PosCheck = re.compile('(?i)^[gG0-3]{1,3}(?:\s+x-?(?P<x>[0-9.]{1,15})|\s+y-?(?P<y>[0-9.]{1,15})|\s+z-?(?P<z>[0-9.]{1,15}))*$')


instructionPattern = r'(G\d)\s(X[\d.]+)?\s(Y[\d.]+)?(\sE[\d.]+)?'
layerMatchPattern = r";LAYER:(\d+)"
printEndedPattern=r'M140 S0'

GcodeFile= open(filename+'.gcode', 'r')
instructions = GcodeFile.readlines()
count = 0
for instruction in instructions:

    layerMatch=re.match(layerMatchPattern, instruction)
    if layerMatch:
        layerNumber=layerMatch.group(1)
        print ("Layer {} starts.".format(layerNumber))

        #print(patharray)
        if dwg:
            if len(patharray)>0:
                # Draw an irregular polygon

             saveCurrentPath(patharray)   
              
        dwg = svgwrite.Drawing(filename+layerNumber+'.svg')
        patharray=[]
        layerStarted=True  
        p=input()  
        continue     

    #start a new file to write to.

    #print(instruction)
    printEndedMatch=re.match(printEndedPattern, instruction)

    if printEndedMatch: # This is the Exit conditiopn, as the end of the print has been reached

        # Draw an irregular polygon
        saveCurrentPath(patharray)
        dwg = svgwrite.Drawing(filename+layerNumber+'.svg')
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
            patharray=[]
            

        if( command=="G1" and layerStarted):
            #print("Adding")
           # print("G1 X:{}, y:{}, ".format(xVal, yVal ))
            xsum=xsum+float(xVal)
            ysum=ysum+float(yVal)
            pointcount=pointcount+1

            patharray.append(xVal)
            patharray.append(yVal)
            
            
        
    else:
        continue

  














   
    
