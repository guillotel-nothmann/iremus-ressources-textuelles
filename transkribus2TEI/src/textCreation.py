'''
Created on Feb 3, 2024

@author: christophe
'''

import json, os 
from urllib.request import urlretrieve 
from lxml import etree as ET  
from openpyxl.chartsheet import custom 
import numpy as np
import cv2
import urllib.request

class Text(object):
    '''
    classdocs
    '''

    def __init__(self, metsRoot, importPath, exportPath):
        '''
        Constructor
        '''
        self.manifestPath = "temp/manifest.json" 
        with open(self.manifestPath, encoding='utf-8') as manifest:
            self.manifestJS = json.load(manifest)
        
        self.toolBox = ToolBox()
        self.metsRoot = metsRoot 
        self.pageList = []
        self.importPath = importPath
        self.exportPath = exportPath
        self.createPages()
        self.createFigures()
        
        
    def createPages(self):
        for ns3File in self.metsRoot.xpath("//ns3:fileGrp/ns3:file", namespaces={'ns3': 'http://www.loc.gov/METS/'}): 
            self.pageList.append(Page(self.importPath, self.metsRoot, ns3File, self.manifestJS))
            
    def getTitlePageURL (self): 
        for page in self.pageList: 
            for region in page.regionList:
                if region.customDic["structure"]["type"] == "titlePage":   
                    return page.imageIdJpg 
                
    def createFigures(self):  
        for figure in self.getRegions(["staff-notation", "ornament", "table", "tablature_notation", "diagram"]):
            try:    
                req = urllib.request.urlopen(figure.imageIdJpg)
                arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, -1) # 'Load it as it is'
                
               
                coordList = self.toolBox.coordPointsToCoordList(figure.coordPoints)               
                pts = np.array(coordList)
                
                ## (1) Crop the bounding rect
                rect = cv2.boundingRect(pts)
                x,y,w,h = rect
                croped = img[y:y+h, x:x+w].copy()
                
                ## (2) make mask
                pts = pts - pts.min(axis=0)
                
                mask = np.zeros(croped.shape[:2], np.uint8)
                cv2.drawContours(mask, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)
                
                ## (3) do bit-op
                dst = cv2.bitwise_and(croped, croped, mask=mask)
                
                ## (4) add the white background
                bg = np.ones_like(croped, np.uint8)*255
                cv2.bitwise_not(bg,bg, mask=mask)
                dst2 = bg+ dst
                
                figure.fileName = figure.id + ".jpg"
                figure.width = w
                figure.height = h
                
                os.makedirs(os.path.dirname(self.exportPath + "/figures/" + figure.id + ".jpg"), exist_ok=True)
                 
                #cv2.imwrite("croped.png", croped)
                #cv2.imwrite("mask.png", mask)
                #cv2.imwrite("dst.png", dst)
                cv2.imwrite(self.exportPath + "/figures/" + figure.id + ".jpg", dst2)
            
            except:
                print("Cannot create file for following figure: " + str(figure))
                
                
                       
    
    
    def getRegions(self, tagList= ["staff-notation"]):
        regionList = []
        for page in self.pageList:
            for tag in tagList:
                regionSubList = page.getRegion(tag)
                if regionSubList != None:
                    regionList = regionList + regionSubList
        return regionList
        
class TextLine (object):
    def __init__(self, textLineTag, fileID):
        self.id = fileID + "_" + textLineTag.attrib["id"]
        self.customDic = ToolBox().createCustomDic(textLineTag.attrib["custom"])
        
        for coord in textLineTag.xpath("page:Coords", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
            self.coordPoints = coord.attrib["points"]
        for baseline in textLineTag.xpath("page:Baseline", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
            self.baseLineCoords = baseline.attrib["points"]
        for textEquiv in textLineTag.xpath("page:TextEquiv/page:Unicode", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
            self.textEquiv = textEquiv.text    

class TextRegion (object):
    def __init__(self, regionRef, fileID):
        self.id = fileID + "_" + regionRef.attrib["id"]
        self.customDic = ToolBox().createCustomDic(regionRef.attrib["custom"])
        self.textLineList = []
        
        for coords in regionRef.xpath("page:Coords", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
            self.coordPoints = coords.attrib["points"]
        for line in regionRef.xpath("page:TextLine", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
            self.textLineList.append(TextLine(line, fileID))
        
    
class Page (object):
    def __init__(self, importPath, metsRoot, ns3File, manifestJs):
        self.importPath = importPath
        self.metsRoot = metsRoot
        self.fileID = ""
        self.fileSeq = ""
        self.fileMimeType = ""
        self.fileCreated = ""
        self.fileCheckSum = ""
        self.fileCheckSumType = ""
        self.fLocatLocType = ""
        self.fLocatOtherLocType = ""
        self.fLocatNs2Type = ""
        self.fLocatNs2Href = ""
        self.ns3DivID = ""
        self.ns3DivOrder = ""
        self.ns3DivType = ""
        self.imageWidth=None
        self.imageHeight = None
        self.regionRefDic = {}
        self.regionList = []
        
        
        
         
        self.fileID = ns3File.attrib["ID"]
        self.fileSeq = ns3File.attrib["SEQ"]
        self.fileMimeType = ns3File.attrib["MIMETYPE"]
        self.fileCreated = ns3File.attrib["CREATED"]
        self.fileCheckSum = ns3File.attrib["CHECKSUM"]
        self.fileCheckSumType = ns3File.attrib["CHECKSUMTYPE"]
        self.facs = "#"+ self.fileID 
        
        
        self.imageIdJpg = manifestJs["sequences"][0]["canvases"][int(self.fileSeq)-1]["images"][0]["resource"]["@id"]
        if not "/full/full/0/default.jpg" in self.imageIdJpg: self.imageIdJpg = self.imageIdJpg + "/full/full/0/default.jpg"
        
        for element in ns3File:
            if element.tag == "{http://www.loc.gov/METS/}FLocat":
                self.fLocatLocType = element.attrib["LOCTYPE"]
                self.fLocatOtherLocType = element.attrib["OTHERLOCTYPE"]
                self.fLocatNs2Type = element.attrib["{http://www.w3.org/1999/xlink}type"]
                self.fLocatNs2Href = element.attrib["{http://www.w3.org/1999/xlink}href"]
                
                areaFound = False
                for ns3Div in self.metsRoot.xpath("//ns3:structMap/ns3:div/ns3:div", namespaces={'ns3': 'http://www.loc.gov/METS/'}): 
                    if areaFound == True: break
                    for element in ns3Div:
                        if element.tag == "{http://www.loc.gov/METS/}fptr":
                            for element2 in element:
                                if element2.tag == "{http://www.loc.gov/METS/}area":
                                    if element2.attrib["FILEID"] == self.fileID:
                                        self.ns3DivID = ns3Div.attrib["ID"]
                                        self.ns3DivOrder = int(ns3Div.attrib["ORDER"])
                                        self.ns3DivType = ns3Div.attrib["TYPE"]
                                        areaFound = True
            
   
            pageTree = ET.parse(self.importPath + self.fLocatNs2Href)
            pageRoot = pageTree.getroot()
            
            for transkribusMetaData in pageRoot.xpath("//page:TranskribusMetadata", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
                self.pageNumber = "[" + transkribusMetaData.attrib["pageNr"] + "]"
            
            for page in pageRoot.xpath("//page:Page", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}): 
                self.imageWidth=page.attrib["imageWidth"]
                self.imageHeight = page.attrib["imageHeight"]
                self.imageFilename = page.attrib["imageFilename"]
            
            for regionRef in pageRoot.xpath("//page:ReadingOrder/page:OrderedGroup/page:RegionRefIndexed", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
                self.regionRefDic[regionRef.attrib["index"]]=regionRef.attrib["regionRef"]
            
            ''' region info '''
            for regionRef in pageRoot.xpath("//page:TextRegion", namespaces={'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
                self.regionList.append(TextRegion(regionRef, self.fileID))
        self.setPbInformation()
            
    def setPbInformation (self):
        for region in self.getRegion("page-number"):
            self.pageNumber = self.regionToString(region)
            
    
    
    def getRegion(self, regionTag):
        regionList = []
        for region in self.regionList:
            if "structure" in region.customDic:
                if regionTag in region.customDic["structure"]["type"]:
                    region.imageIdJpg = self.imageIdJpg
                    regionList.append(region)
            else: 
                print("Region tag missing for: " + str(self.fileID) +" index: " + str(int(region.customDic["readingOrder"]["index"])+1))
        return regionList
        
    
    
    def regionToString(self, region):
        listString = ""
        if isinstance(region, TextRegion):
            for element in region.textLineList:
                if element.textEquiv !=None:
                    listString = listString + element.textEquiv + " "
                else:
                    listString = listString
        return listString
            
                
        
          
class ToolBox (object):
    
    def createCustomDic (self, customString): 
        customDic = {}
                
        customList = customString.split("}")
        customListClean = []
        for element in customList: 
            customListClean.append(element.replace(";", "}")) 
        customListClean = customListClean[:-1]
        for item in customListClean:
            valueList = item.split("{")
            itemKey = valueList[0].strip()
            itemValue =  valueList[1].replace ("}", "")
            itemValueList = itemValue.split(";")
            itemValueDic = {}
            for valuePair in itemValueList:
                valuePairSplit = valuePair.split (":")
                if len(valuePairSplit) == 2:
                    itemValueDic[valuePairSplit[0]] = valuePairSplit[1]
            
            customDic[itemKey] = itemValueDic
        return customDic  
    
    def coordPointsToCoordList(self, coordsPoints):
        coordList = []
        for pairString in coordsPoints.split(" "):
            pairInt = []
            for element in pairString.split(","):
                pairInt.append(int(element))
            coordList.append(pairInt)
        return coordList
                
            
     
            
            