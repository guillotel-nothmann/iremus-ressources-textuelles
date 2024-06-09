'''
Created on Feb 7, 2024

@author: christophe
'''
from lxml import etree as ET 
import uuid
from builtins import isinstance, list
import textCreation 
from textCreation import TextRegion



class TEIText(object):
    '''
    used to convert page structure in a tei document
    '''


    def __init__(self, textInstance, teiRoot):
        '''
        Constructor
        ''' 
        self.idList = []
        
        self.textInstance = textInstance
        #
        self.teiText = self.addXMLID(ET.Element("text"))
        self.teiBody = self.addXMLID(ET.Element("body"))
        self.teiFront = self.addXMLID(ET.Element("front"))
        
        self.teiRoot = teiRoot
        self.page2TEIDic = {
            textCreation.TextRegion: self.processTextRegion,
            textCreation.TextLine: self.lb
            }
        self.custom2TEIDic = {
            "heading": self.head, 
            "catch-word": self.fw,
            "titlePage": self.head, ### TODO
            "paragraph" : self.p,
            "paragraph_continued": self.p,
            "drop-capital" : self.c,
            "page-number": self.pb,
            "ornament": self.figure,
            "signature-mark": self.fw,
            "anonymous-block": self.ab,
            "staff-notation": self.figure,
            "tablature_notation": self.figure,
            "caption": self.head,
            "line_group": self.lg,
            "signature": self.signed,
            "list": self.list,
            "table": self.figure,
            "diagram": self.figure
            }
        
        self.regionDic = {
            textCreation.TextRegion: "TextRegion",
            textCreation.TextLine: "TextLine"
        
            }
    
        self.teiFacsimile = self.facsimile(textInstance, teiRoot) 
        self.teiText.append(self.teiFront)
        self.teiText.append(self.teiBody)
        
        
        ''' create semiFlatRepresentation, iterate and create tei objects accordingl ''' 
        self.flatList = self.getRegionList()
        self.sectionList = self.getNestedRegionList() 
        self.teiFront = self.createTitlePage(self.flatList, self.teiFront)
        
        self.processNodes(self.sectionList, self.teiBody, True)
        
        
        for text in self.teiRoot.xpath("//tei:text", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):  
            parent = text.getparent()
        parent.remove(text)
        parent.append(self.teiFacsimile)
        parent.append(self.teiText) 
        self.nestDropCapital()
        self.nestPb() 
        self.nestCaption()
    
   
    
    ''' tei objects '''
    
    def ab (self, textNode, teiNode):
        abInstance = ET.Element("ab")
        abInstance.attrib["facs"] = textNode.id
        abInstance.attrib["type"] = textNode.customDic["structure"]["type"]
        self.addXMLID(abInstance)  
        teiNode.append(abInstance)
        for element in textNode.textLineList:
            self.processNodes(element, abInstance) 
    
    def c (self, textNode, teiNode):
        cInstance = ET.Element("c")
        self.addXMLID(cInstance)  
        teiNode.append(cInstance)  
        
        if textNode.customDic["structure"]["type"] == "drop-capital":
            cInstance.attrib["type"] = "drop_capital"
            cInstance.attrib["facs"] = "#" + textNode.id 
            cInstance.text = self.extractText(textNode)   
    
    def div (self, pageNode, teiNode):
        divInstance = ET.Element("div")
        self.addXMLID(divInstance)
        teiNode.append(divInstance)
        for element in pageNode: 
            self.processNodes(element, divInstance)    
        
    def facsimile(self, pageNode, teiNode):
        facsimileInstance = ET.Element("facsimile")
        self.addXMLID(facsimileInstance)
        for page in pageNode.pageList:
            self.processNodes(page, facsimileInstance, False, True)
        return facsimileInstance
        
    def figure (self, pageNode, teiNode):
        figureInstance = ET.Element("figure") 
        figureInstance.attrib["type"] = pageNode.customDic["structure"]["type"]
        self.graphic(pageNode, figureInstance)
        teiNode.append(figureInstance) 
        
    def fw (self, pageNode, teiNode):
        fwInstance = ET.Element("fw")
        fwInstance.attrib["type"] = pageNode.customDic["structure"]["type"]
        fwInstance.attrib["facs"]= pageNode.id
        self.addXMLID(fwInstance)
        for element in pageNode.textLineList:
            self.processNodes(element, fwInstance)
            
        teiNode.append(fwInstance)
            
            
        
    def graphic (self, regionNode, teiNode):
        graphicinstance = ET.Element("graphic")
        
        if hasattr(regionNode, "fileName"):
            graphicinstance.attrib["url"] = regionNode.fileName
            graphicinstance.attrib["width"] = str(regionNode.width) + "px"
            graphicinstance.attrib["height"] = str(regionNode.height) + "px"
            
        else: 
            print ("Cannot create graphic url for the following region: " + regionNode.id + " of type: " + regionNode.customDic["structure"]["type"])
        teiNode.append(graphicinstance)
    
    def head (self, textRegion, teiNode):
        headInstance = ET.Element("head")
        self.addXMLID(headInstance)
        headInstance.attrib["type"] = textRegion.customDic["structure"]["type"] 
        teiNode.append(headInstance)
        self.title(textRegion, headInstance)
    
    def item (self, textLine, teiNode):
        itemInstance = ET.Element("item")
        self.processTextLine(textLine, itemInstance, False)
        teiNode.append(itemInstance) 
        
    def lb (self, textLineID):
        lbInstance = ET.Element("lb")
        lbInstance.attrib["facs"]= "#" + textLineID
        self.addXMLID(lbInstance)
        return lbInstance
    
    
    def l (self, textLine, teiNode):
        lInstance = ET.Element("l")
        self.processTextLine(textLine, lInstance, False)
        teiNode.append(lInstance)
        
    
    def lg (self, lgNode, teiNode):
        lgInstance = ET.Element("lg")
        self.addXMLID(lgInstance)
        
        for element in lgNode.textLineList:
            self.l(element, lgInstance) 
        teiNode.append(lgInstance)
    
    def list (self, listRegion, teiNode):
        listInstance = ET.Element("list")
        self.addXMLID(listInstance)
        
        for element in listRegion.textLineList:
            self.item(element, listInstance)
        teiNode.append(listInstance)
    
        
    def p (self, paragraphNode, teiNode):
        pInstance = ET.Element("p")
        pInstance.attrib["facs"] = "#" + paragraphNode.id
        self.addXMLID(pInstance)
        teiNode.append(pInstance)
        if paragraphNode.customDic["structure"]["type"] == "paragraph_continued":
            pInstance.attrib["style"] = "continued" 
        for element in paragraphNode.textLineList:
            self.processNodes(element, pInstance) 
    
    def pb (self, pageNode, teiNode): 
        if isinstance(pageNode, textCreation.Page):
            pbInstance = ET.Element("pb")
            self.addXMLID(pbInstance)
            teiNode.append(pbInstance)
            pbInstance.attrib["n"] = pageNode.pageNumber
            pbInstance.attrib["facs"] = "#" + pageNode.fileID #pageNode.facs
            return pbInstance
        None
    
    def signed (self, textNode, teiNode):
        abInstance = ET.Element("signed")
        abInstance.attrib["facs"] = textNode.id 
        self.addXMLID(abInstance)  
        teiNode.append(abInstance)
        for element in textNode.textLineList:
            self.processNodes(element, abInstance)
    
    
    def surface (self, pageNode, teiNode):
        surfaceInstance = ET.Element ("surface")
        self.addXMLID(surfaceInstance, pageNode.fileID)
        surfaceInstance.attrib["ulx"] = "0"
        surfaceInstance.attrib["uly"] = "0"
        surfaceInstance.attrib["lrx"] = pageNode.imageWidth
        surfaceInstance.attrib["lry"] = pageNode.imageHeight 
        
        graphicInstance = ET.Element ("graphic")
        graphicInstance.attrib["url"] = pageNode.imageIdJpg
        graphicInstance.attrib["width"] = pageNode.imageWidth + "px"
        graphicInstance.attrib["height"] = pageNode.imageHeight + "px"
        surfaceInstance.append(graphicInstance)
        teiNode.append(surfaceInstance)
        for element in pageNode.regionList: 
            self.processNodes(element, surfaceInstance, False, True)
            
    
    def title (self, textRegion, teiNode):
        titleInstance = ET.Element("title")
        self.addXMLID(titleInstance)
        teiNode.append(titleInstance)
        
        for element in textRegion.textLineList:
            self.processNodes(element, titleInstance)
        
    
    def titlePage (self, pageNode, teiNode):
        titlePageInstance = ET.Element("titlePage")
        self.addXMLID(titlePageInstance)
        teiNode.append(titlePageInstance)
        self.titlePart(pageNode, titlePageInstance)
        
        return titlePageInstance
    

    
    def titlePart (self, pageNode, teiNode):
        docTitleInstance = ET.Element("titlePart")
        self.addXMLID(docTitleInstance)
        for element in pageNode.textLineList:
            self.processNodes(element, docTitleInstance)
        teiNode.append(docTitleInstance)

    
        
    
            
            
    def zone (self, textNode, teiNode):
        zoneInstance = ET.Element("zone")
        if textNode.id == "r_9_tl_1":
            print ()
        
        self.addXMLID(zoneInstance, textNode.id)
        zoneInstance.attrib["points"] = textNode.coordPoints
        zoneInstance.attrib["rendition"] = self.regionDic[type(textNode)]
        if "structre" in textNode.customDic:
            zoneInstance.attrib["subtype"] = textNode.customDic["structure"]["type"]
        teiNode.append(zoneInstance)
        if hasattr(textNode, "textLineList"):
            for textLine in textNode.textLineList:
                self.processNodes(textLine, zoneInstance, False, True)
        
    
  
        
    ''' transformation functions '''
    def getRegionList (self): 
        ''' this returns all page regions''' 
        flatList = []
        for page in self.textInstance.pageList: 
            flatList.append(page) 
            for element in page.regionList:
                flatList.append(element)
        return flatList
        
    def processTextRegion(self, pageNode, teiNode, facsimile=False):
        if facsimile == False:
            structuralTag = pageNode.customDic["structure"]["type"]
            if structuralTag in self.custom2TEIDic:
                self.custom2TEIDic[structuralTag](pageNode, teiNode)
            else: 
                print ("Cannot process structural tag : " + structuralTag + " in node :" + str(pageNode.id) + "index: " + str(pageNode.customDic["readingOrder"]["index"]))
        else:
            self.zone(pageNode, teiNode) 
            
    
    def extractText(self, textNode):
        textString = ""
        for textLine in textNode.textLineList:
            textString = textString + textLine.textEquiv
        return textString
            
            
        
    
    def processTextLine (self, textLine, teiNode, facsimile):
        
        if facsimile == True:
            self.zone(textLine, teiNode)
        
        else:
            if textLine.textEquiv == None: return
            correctedString = textLine.textEquiv
            if correctedString [-1] in ["-", "–", "¬", "="]:
                correctedString = correctedString[:-1]
            else:
                correctedString = correctedString + " "
            
            if teiNode.tag== "l" or teiNode.tag=="item":
                teiNode.text = correctedString
            
            else: 
                lbInstance = self.lb(textLine.id)
                lbInstance.tail = correctedString
                teiNode.append(lbInstance)
            
           
    def getNestedRegionList (self):
        ''' this returns the page regions in a hierarchical list according to the heading hierarchy '''
        sectionList = []
        section = []
        sectionList.append(section)
        for  item in self.flatList:
            if isinstance(item, textCreation.TextRegion):
                if not "structure" in item.customDic: continue
                if "heading" in item.customDic["structure"]["type"]=="heading":
                    if len(section) != 0:  # if the current section is not empty (i.e. if this is not the initial section, create new one)
                        section = []
                        sectionList.append(section)
            section.append(item)   
        return sectionList  
    
    def createTitlePage (self, sectionList, teiNode):
        for node in sectionList :
            if isinstance(node, textCreation.Page): continue
            if node.customDic["structure"]["type"] == "titlePage":
                return self.titlePage(node, teiNode) 
    
    def processNodes(self, pageNode, teiNode, rootNode = False, facsimile=False):
        if rootNode == True:
            for element in pageNode:
                self.processNodes(element, teiNode)
        elif isinstance(pageNode, textCreation.Page):
            if facsimile == False:
                self.pb(pageNode, teiNode)
            else:
                self.surface(pageNode, teiNode)
        elif isinstance(pageNode, list): ### align with div 
            if len(pageNode) == 1 and isinstance(pageNode[0], textCreation.Page):
                self.pb(pageNode[0], teiNode)
            else:
                self.div(pageNode, teiNode)
        elif isinstance (pageNode, textCreation.TextRegion): 
            self.processTextRegion(pageNode, teiNode, facsimile)
        elif isinstance (pageNode, textCreation.TextLine):
            self.processTextLine(pageNode, teiNode, facsimile)
        else:
            print("Cannot process node: " + str(pageNode))
            
                 
    ''' post correction '''
    def nestDropCapital (self):
        for dropCapital in self.teiRoot.xpath("//c", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            nextSyb = dropCapital.getnext()
            dropCapital.getparent().remove(dropCapital)
            if nextSyb != None: 
                firstChild = nextSyb[0]
                if firstChild.tag == "lb":
                    dropCapital.tail = firstChild.tail
                    firstChild.tail = None
                    nextSyb.insert(1, dropCapital)
                else:
                
                    nextSyb.insert(1, dropCapital)
            else: 
                print ("Cannot find sybling for drop capital: " + str(dropCapital.attrib["facs"]))
            
            
    
    def nestPb (self):
        for pageBreak in self.teiRoot.xpath("//pb", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            precedingSibling = pageBreak.getprevious() 
            nextSibling =  pageBreak.getnext()  
            
            ''' continued paragraphs '''
            if hasattr(nextSibling, "style"): 
                if nextSibling.attrib["style"] == "continued":
                    if nextSibling.tag == "p" and precedingSibling.tag == "p":
                        pageBreak.getparent().remove(precedingSibling)
                        pageBreak.getparent().remove(nextSibling)
                        
                        mergedP = ET.Element("p")
                        mergedP.attrib["type"]="merged"
                        pageBreak.addnext(mergedP)
                        
                        for element in  precedingSibling:
                            mergedP.append (element)
                        mergedP.append (pageBreak)
                        for element in  nextSibling:
                            mergedP.append (element) 
                        #pageBreak.getparent().remove(pageBreak)
                    print ("Cannot nest pb: " + str (pageBreak))
                    
    
    def nestCaption (self):
        for caption in self.teiRoot.xpath("//head[@type='caption']", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            precedingSibling = caption.getprevious() 
            nextSibling =  caption.getnext()  
            
            try: 
                if precedingSibling.tag == "figure":
                    caption.getparent().remove(caption)
                    precedingSibling.append(caption)
                elif nextSibling.tag == "figure":
                    caption.getparent().remove(caption)
                    nextSibling.insert(0, caption)
                    
            except:
                print ("Cannot nest caption: " + str (caption))
                pass  
    
    
    ''' helper functions '''
    def addXMLID(self, node, xmlID = None): 
        if xmlID == None: 
            node.attrib["{http://www.w3.org/XML/1998/namespace}id"] = self.generatedID()
        else:
            node.attrib["{http://www.w3.org/XML/1998/namespace}id"] = xmlID 
            self.idList.append(xmlID)
        return node 
    
    def generatedID (self):
        idBool = False
        while idBool == False: 
            idString = "a"+str(uuid.uuid4().fields[-1])[:5]  
            if idString not in self.idList:
                self.idList.append(idString)
                return idString
                
        
        
 
    def listToString (self, listInstance):
        listString = ""
        if isinstance(listInstance, textCreation.TextLine):
            for element in listInstance.textLineList:
                listString = listString + element.textEquiv + " " 
        for element in listInstance:
            if isinstance(element, textCreation.TextLine):
                listString = listString + element.textEquiv + " "
            elif isinstance (element, str):
                listString = listString + element + " " 
        listString = listString[:-1] 
        return listString
    
   
        
                
                
        