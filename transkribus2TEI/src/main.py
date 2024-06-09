'''
Created on Jan 23, 2024

This takes a Transkribus Page export and converts it into TEI

@author: christophe
'''

import json, codecs, os, requests
from lxml import etree as ET 
from urllib.request import urlretrieve
from metadataCreation import metadata
from textCreation import Text
from teiText import TEIText
import dcMetaData


            


if __name__ == '__main__':
    pass

''' paths '''
importPath = "/Users/christophe/Documents/GitHub/TMG_Sources/transcribusExports/Werckmeister,_Musicalische_Temperatur/"
tmgMetaDataURL = "http://tmg.huma-num.fr/fr/content/werckmeister-andreas-musicalische-temperatur-1691"


githubURL = "https://github.com/guillotel-nothmann"
teiModelPath = "teiModel.xml"
metsPath = importPath + "mets.xml" 
fileName = tmgMetaDataURL.split("/")[-1]
exportPath = "/Users/christophe/Documents/GitHub/TMG_XTF/tomcat/webapps/xtf/data/tei/" + fileName + "/"


''' trees''' 
teiTree = ET.parse(teiModelPath)
teiRoot = teiTree.getroot()
metsTree = ET.parse(metsPath)
metsRoot = metsTree.getroot()


md = metadata(importPath, metsRoot, teiRoot, tmgMetaDataURL, githubURL)
textInst = Text(metsRoot, importPath, exportPath)
teiInst = TEIText(textInst, teiRoot)
dcInstance = dcMetaData.DC(md.dcDic)
dcRoot = dcInstance.getDcRoot()

titlePageURL = textInst.getTitlePageURL()

img_data = requests.get(titlePageURL).content
os.makedirs(os.path.dirname(exportPath + "/figures/" + fileName + "_cover.jpg"), exist_ok=True)
with open(exportPath + "/figures/" + fileName + "_cover.jpg", "wb") as handler:
    handler.write(img_data)

os.makedirs(os.path.dirname(exportPath + fileName + ".dc.xml"), exist_ok=True)
with open(exportPath + fileName + ".dc.xml", 'w', encoding='utf-8') as the_file: 
    ET.ElementTree(dcRoot).write(exportPath + fileName + ".dc.xml", pretty_print=True, encoding='utf-8', xml_declaration=True)
 
 
with open(exportPath + fileName + ".xml", 'w', encoding='utf-8') as the_file: 
    ET.ElementTree(teiRoot).write(exportPath + fileName + ".xml", pretty_print=True, encoding='utf-8', xml_declaration=True)
    
    

#print (md)
        
        
         
    
    
