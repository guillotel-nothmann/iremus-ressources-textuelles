'''
Created on Jan 24, 2024

@author: christophe
'''

import json, requests 
from lxml import etree as ET 
from urllib.request import urlretrieve 
from bs4 import BeautifulSoup
from builtins import isinstance
class metadata(object):
    '''
    classdocs
    '''
    
    def __init__(self, importPath, metsRoot, teiRoot, tmgMetaDataURL, githubURL):
        self.importPath = importPath
        self.metsRoot = metsRoot
        self.teiRoot = teiRoot
        self.manifestPath = "temp/manifest.json" 
        self.tmgMetaDataURL = tmgMetaDataURL
        self.tmgMetaDataDic = self.getTMGMetadata()
        self.gitHubPage2Tei = githubURL
        
        
        ''' use manifest '''
        for externalID in metsRoot.xpath("//externalId"):
            idURL = externalID.text
        
        if "manifest" in idURL:
            urlretrieve(idURL, self.manifestPath)
            
            with open(self.manifestPath, encoding='utf-8') as manifest:
                self.manifestJS = json.load(manifest)
                
        
                
        self.setTitleStmt() 
        self.setEditionStmt() 
        self.setPublicationStmt()
        self.setSourceDesc()
        
    
    def setSourceDesc (self):
        ''' create tags '''
        sourceDesc = ET.Element("sourceDesc")
        p = ET.Element("p")     
        listWit = ET.Element("listWit")   
        witness = ET.Element("witness")
        bibl = ET.Element("bibl")
        author = ET.Element("author")
        title = ET.Element("title")
        pubPlace = ET.Element("pubPlace")
        publisher = ET.Element("publisher")
        date = ET.Element("date")
        extent = ET.Element ("extent")
        idno = ET.Element ("idno")
        dim = ET.Element ("dim") 
        msDesc = ET.Element ("msDesc")
        msIdentifier = ET.Element ("msIdentifier")
        institution = ET.Element ("institution")
        idnoInst = ET.Element ("idno")
        relatedItem = ET.Element("relatedItem")
        relatedBibl = ET.Element("bibl")
        relatedBiblIdent = ET.Element("ident")
         
        
        # <location>
        
        ''' add the data '''
        author.text = self.tmgMetaDataDic["author"]
        title.text =   self.tmgMetaDataDic["title"]   
        pubPlace.text =  self.tmgMetaDataDic["place"]   
        publisher.text = self.tmgMetaDataDic["publisher"] 
        date.attrib["when"] = self.tmgMetaDataDic["date"]
        extent.text = self.tmgMetaDataDic["pages"] + " pages"   
        idno.attrib["type"] = "VD16/17"
        idno.text = self.tmgMetaDataDic["vd"]    
        
        for fileDesc in self.teiRoot.xpath("//tei:fileDesc", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            fileDesc.append(sourceDesc) 
            
        sourceDesc.append(p)
        p.append(listWit)
        listWit.append(witness)
        witness.append(bibl)
        bibl.append(author)
        bibl.append(title)
        bibl.append(pubPlace)
        bibl.append(publisher)
        bibl.append(date)
        bibl.append(extent)
        bibl.append(idno) 
        bibl.append(relatedItem)
        relatedItem.append(relatedBibl)
        relatedBibl.append(relatedBiblIdent)
        relatedBiblIdent.text =  self.getURLFromHtmlA ( self.getManifestMetaData("PURL"))
        relatedBiblIdent.attrib["type"] = "url"
        
        
        
        for manifestIdent in self.getManifestIdnos():
            manifestIdno = ET.Element ("idno")
            manifestIdno.attrib["type"] = manifestIdent[0]
            manifestIdno.text = manifestIdent[1] 
            bibl.append(manifestIdno)
        
        witness.append(msDesc)
        msDesc.append(msIdentifier)
        msIdentifier.append(institution)
        msIdentifier.append(idnoInst)
        
        institution.text = self.getManifestMetaData("Eigentümer")
        idnoInst.text = self.getManifestMetaData("Signatur")
        
        
        
        self.dcDic = {
            
            "title": title.text,
            "creator" : author.text,
            "date": date.attrib["when"],
            "description": "TMG transcription",
            "subject": ["Music theory", str((int(date.attrib["when"])) // 100 + 1) + "th century"] ,
            "type" : "TEI"
        }
    
    
    def getTMGMetadata(self):
        
        tmgMetaDataDic = {
            "author": "",
            "title": "",
            "place": "",
            "publisher":"",
            "date": "",
            "vd": "",
            "pages":"",
            "pagesLeaves": ""
            }
        
        classList = [
            ["field field-name-field-autor field-type-text field-label-inline clearfix", "author"],
            ["field field-name-field-title field-type-text field-label-inline clearfix", "title"],
            ["field field-name-field-place field-type-text field-label-inline clearfix", "place"],
            ["field field-name-field-publisher field-type-text field-label-inline clearfix", "publisher"],
            ["field field-name-field-field-date-2 field-type-text field-label-inline clearfix", "date"],
            ["field field-name-field-vd field-type-text field-label-inline clearfix", "vd"],
            ["field field-name-field-pages-integer field-type-text field-label-inline clearfix", "pages"],
            ["field field-name-field-leaves-pages field-type-text field-label-inline clearfix", "pagesLeaves"]
            ]

        page = requests.get(self.tmgMetaDataURL) 
        soup = BeautifulSoup(page.content, "html.parser")
        
        for metaDataClass in classList:
            results = soup.find_all("div", class_ =metaDataClass[0])
            for element in results:
                items = element.find_all("div", class_="field-item even")
                for item in items:
                    tmgMetaDataDic[metaDataClass[1]] = item.text
                
        
        
        return tmgMetaDataDic

        
    
    def setPublicationStmt(self):
        publicationStmt = ET.Element("publicationStmt")
        authority = ET.Element("authority")
        authority.text = "Institut de Recherche en Musicologie (UMR 8223)" 
        
        publisher = ET.Element("publisher")
        publisher.text = "Thesaurus Musicarum Germanicarum" 
        
        
        publicationStmt.append (authority)
        publicationStmt.append (publisher)
        publicationStmt.append (self.setPublicationDate())
        
        for fileDesc in self.teiRoot.xpath("//tei:fileDesc", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            fileDesc.append(publicationStmt)
        
        
        
    def setEditionStmt(self, source="tmgMeta"):
        editionStmt =  ET.Element("editionStmt")
        edition = ET.Element("edition")
        if source == "tmgMeta":
            edition.text = "Electronic edition of " + self.tmgMetaDataDic["publisher"] + ", " + self.tmgMetaDataDic["date"]
        else:
            edition.text = "Electronic edition of " + self.getManifestMetaData("Creation")
        
        editionStmt.append(edition)
        editionStmt.append(self.setTranscriptionResp())
        editionStmt.append(self.setAuthorResp())
        editionStmt.append(self.setTransformationResp())
        for fileDesc in self.teiRoot.xpath("//tei:fileDesc", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            fileDesc.append(editionStmt)   
    
    def setTitleStmt(self):  
        titleStmt =  ET.Element("titleStmt")
        titleStmt.append(self.setTitle())
        titleStmt.append(self.setAuthor())
        
        for fileDesc in self.teiRoot.xpath("//tei:fileDesc", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            fileDesc.append(titleStmt) 
    
    def setAuthor (self, source="tmgMeta"):   
        author = ET.Element("author")
        if source == "tmgMeta":
            author.text = self.tmgMetaDataDic["author"]
        else:
            author.text = str(self.getManifestMetaData("Creator")) 
        return author
        
    def setTitle (self, source="tmgMeta"):
        title =  ET.Element("title")
        if source == "tmgMeta":
            title.text = self.tmgMetaDataDic["title"]
        else:
            title.text = self.getManifestMetaData("Title")
        
        return title
    
            
    def setPublicationDate(self):
        dateElement = ET.Element("date") 
        dateElement.attrib["when"] = self.getMetsLastModDate ()
        return dateElement 
    
    def setAuthorResp(self, source="tmgMeta"):
        respStmt = ET.Element("respStmt")
        resp = ET.Element("resp")
        resp.text="Author"
        
        name = ET.Element("name")
        
        if source =="tmgMeta":
            name.text=self.tmgMetaDataDic["author"]
        else:
            name.text=self.getManifestMetaData("Creator") 
        
        
        respStmt.append(resp)
        respStmt.append(name)
        return respStmt
    
    def setTransformationResp (self):
        respStmt = ET.Element("respStmt")
        resp = ET.Element("resp")
        resp.text="Page to TEI transformation based on the python script transkribus2TEI"
        name = ET.Element("name")
        name.attrib["{http://www.w3.org/XML/1998/namespace}id"] = "transkribus2Tei"
        ref = ET.Element("ref")
        ref.attrib["type"] = "ext"
        ref.attrib["target"] = self.gitHubPage2Tei
        name.append(ref)
        
        respStmt.append(resp)
        respStmt.append(name)
        
        return respStmt
        
        
        
    def setTranscriptionResp(self):
        creatorList = self.getMetsCreator()  
        respStmt = ET.Element("respStmt")
        resp = ET.Element("resp")
        resp.text="OCR-algorithm"
        respStmt.append(resp)
        for creator in creatorList:
            nameElement = ET.Element("name")
            nameElement.text = creator
            respStmt.append(nameElement) 
        return respStmt
        
    
    def getManifestMetaData(self, label):
        for element in self.manifestJS["metadata"]:
            if isinstance (element["label"], list):        
                for labelElement in element["label"]:
                    if labelElement["@value"] == label:
                        return element["value"]
            else:
                if element["label"] == label:
                        return element["value"]
                
        return None
    
    def getManifestIdnos (self):
        idnoList = []
        
        for element in self.manifestJS["metadata"]:
            if isinstance (element["label"], str): # D-Gs
                if element["label"] == "PURL":
                    idnoList.append(["identifier", element["value"][0]])
                    
            else: # D-Bs
            
                for labelElement in element["label"]:
                    if labelElement["@value"] == "Location":
                        idnoList.append( ["location", element["value"]])
                    if labelElement["@value"] == "Identifier":
                        idnoList.append( ["identifier", element["value"]]) 
                    
        return idnoList
                
                
        
    
    def getMetsCreator(self):
        creatorList  = []
        for fileLoc in self.metsRoot.xpath("//ns3:fileGrp[@ID='PAGEXML']/ns3:file/ns3:FLocat", namespaces={'ns3': 'http://www.loc.gov/METS/'}):
            href = fileLoc.attrib["{http://www.w3.org/1999/xlink}href"]
            fileTree = ET.parse(self.importPath + href)
            fileRoot = fileTree.getroot()
            for creator in fileRoot.xpath("//PcGts:Metadata/PcGts:Creator", namespaces={'PcGts': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}):
                creatorList.append(creator.text)
        
        return creatorList
    
    def getMetsLastModDate(self):
        for date in self.metsRoot.xpath("//ns3:metsHdr/@LASTMODDATE", namespaces={'ns3': 'http://www.loc.gov/METS/'}):
            return date
        
    
    def getURLFromHtmlA(self, tagString):
        ''' remove opening tag'''
        tagWithoutOpening = tagString.split(">")[1]
        tagWithoutClosing = tagWithoutOpening.split("<")[0]
        
        return tagWithoutClosing
        
        ''' remove closing tag '''
        
                 
                 
                
            
        