'''
Created on Feb 13, 2024

@author: christophe
'''

from lxml import etree as ET 

class DC(object): 

    def __init__(self, dcDic):
        '''
        Constructor
        ''' 
        self.dcDic = dcDic
        
        self.dc = ET.Element("dc")
        title = ET.Element("title")
        creator = ET.Element("creator")
        date = ET.Element("date")
        description = ET.Element("description")
        dcType = ET.Element("type")
        
        title.text = dcDic["title"]
        creator.text = dcDic["creator"]
        date.text = dcDic["date"]
        description.text = dcDic["description"]
        dcType.text = dcDic["type"]
        
        self.dc.append(title)
        self.dc.append(creator)
        self.dc.append(date)
        self.dc.append(description)
        
        for element in dcDic["subject"]:
            subject = ET.Element("subject")
            subject.text = element
            self.dc.append(subject)
            
        self.dc.append(dcType)
    
    def getDcRoot(self):
        return self.dc
        