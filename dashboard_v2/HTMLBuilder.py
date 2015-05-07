import time,os
from xml.etree import ElementTree as ET
from xml.dom import minidom

import random, string

def rand():
   return ''.join(random.choice(string.lowercase) for i in range(10))


class HTMLBuilder:
    
    def __init__(self):
        self.doc = ""
    
    def createDocument(self, pages):
        element = """\
        <html lang="en">
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <meta name="author" content="meric.taze@cern.ch" />
            <link href="res/css/bootstrap.min.css" rel="stylesheet" /> 
            <link href="res/css/bootstrap-table.min.css" rel="stylesheet" />  
            <link href="res/css/base.css" rel="stylesheet" /> 
          </head>
          <body>
            <div class="container" id="container">
              <div class="header">
                <ul class="nav nav-pills pull-right">
                    {0}
                </ul>
                <h3 class="text-muted">CMS CompOps Transfer Team</h3>
              </div>
            </div>
            <script src="res/js/jquery-latest.js">-</script>
            <script src="res/js/bootstrap.min.js">-</script>
            <script src="res/js/base.js">-</script>
            <script src="res/js/bootstrap-table.min.js">-</script>
            <script src="res/js/bootstrap-table-en-US.min.js">-</script>   
          </body>
        </html>
        """
        pageStr = []
        for page in pages:
            if 'active' in page and page['active'] == True:
                pageStr.append('<li class="active"><a href="%s">%s</a></li>' % (page['link'], page['text']))
            else:
                pageStr.append('<li><a href="%s">%s</a></li>' % (page['link'], page['text']))
                
        self.doc = ET.fromstring(element.format(''.join(pageStr)));
        return self.doc.find('body/div')
    

    
    def createTabPanelItem(self,id):
        element = """\
        <div role="tabpanel" class="tab-pane active" id="{0}">
        </div>
        """
        return ET.fromstring(element.format(id))
    
    def createPanelContainer(self):
        element = """\
        <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
        </div>
        """
        return ET.fromstring(element)
        
        
    def addPanelItem(self, text,content, clazz=""):
        id1 = rand()
        id2 = rand()
        element = """\
        <div style="cursor: pointer; width:100%;" data-toggle="collapse" data-parent="#accordion" data-target="#{1}" aria-expanded="true" aria-controls="{1}" class="panel panel-primary {4}">
          <div class="panel-heading" role="tab" id="{0}">
            <h4 class="panel-title">
                {2}
            </h4>
          </div>
          <div id="{1}" class="panel-collapse collapse" role="tabpanel" aria-labelledby="{0}">
            <div class="panel-body">
              {3}
            </div>
          </div>
        </div>
        """
        return ET.fromstring(element.format(id1,id2, text, ET.tostring(content), clazz))

    
    def createTable(self, cols = []):
        if cols:
            element = """\
            <table class="table">
              {0}
            </table>
            """
        if cols:
            header = "<tr><th>%s</th></tr>" % "</th><th>".join(cols)
        else:
            header = ""
            
        return ET.fromstring(element.format(header))

    def createTableWith2Col(self, data, fontSize = 0):
        table = ET.Element('table')
        table.set("class", "table table-striped table-twocols")
        if(fontSize>0):
            table.set("style", "font-size:%spt;" % fontSize)
        for d in data:
            try:
                table.append(ET.fromstring("<tr><th>%s</th><td>%s</td></tr>" % (d, data[d])))
            except:
                table.append(ET.fromstring("<tr><th>%s</th><td>%s</td></tr>" % (d, ET.tostring(data[d]))))
        return table


    def createJSONTable(self,file,cols = []):
        element = []
        element.append('<table data-toggle="table" data-sort-name="source" data-sort-order="asc" data-show-refresh="true" data-show-toggle="true" data-show-columns="true" data-search="true" data-select-item-name="toolbar1" data-url="%s">' % file)
        element.append('  <thead>')
        element.append('    <tr>')
        for col in cols:
            element.append('      <th data-sortable="true" data-field="%s">%s</th>' % (col,col))
        element.append('    </tr>')
        element.append('  </thead>')
        element.append('</table>')
        return ET.fromstring(''.join(element))

    def createLink(self,text,href):
        link = ET.Element('a')
        link.text = str(text)
        link.set("href",href)
        return link
    
    def createDiv(self):
        element = """\
        <div></div>
        """
        return ET.fromstring(element)
        
    def createRow(self, data, clazz=""):
        tr = ET.Element('tr')
        if clazz:
            tr.set("class", clazz)
        for d in data:
            td = ET.Element('td')
            addContent(td, d)
            tr.append(td)
        return tr
    
    def createCollapsible(self, parent, content):
        id = rand()
        element = """\
        <tr>
          <td colspan="10">
            <div class="collapse" id="{0}">
              {1}
            </div>
          </td>
        </tr>
        """
        # set parent's attributes
        parent.set("data-toggle","collapse")
        self.addAttr(parent,"style","cursor: pointer;")
        parent.set("data-target","#"+id)
        return ET.fromstring(element.format(id,ET.tostring(content)))
    
   
    def createLabel(self, content, clazz = "default"):
        element = """\
        <span class="label label-{0}">{1}</span>
        """
        try:
            return ET.fromstring(element.format(clazz,content))
        except:
            return ET.fromstring(element.format(clazz,ET.tostring(content)))


    def createSearchBox(self):
        element = """\
        <div class="form-group has-feedback">
          <label class="control-label" for="search_textbox">Type Subscription, Dataset, Site, etc.</label>
          <input id="filter_data" type="text" class="form-control"/>
          <span class="glyphicon glyphicon-search form-control-feedback"></span>
        </div>
        """
        return ET.fromstring(element)

    def addChild(self, parent,child):
        parent.append(child)
    
    def addAttr(self,element, attr, val):
        oldVal = element.get(attr, "")
        element.set(attr,val+" "+oldVal)
    
    
    def save(self, fileName):
        fp = open(fileName, "w")
        fp.write(ET.tostring(self.doc));
        fp.close()
    
    
    def toString(self, element):
        return ET.tostring(element, 'utf-8')
    
    MB = 1000.0 ** 2
    GB = 1000.0 ** 3
    TB = 1000.0 ** 4
    # size to human-readible string
    def getSizeString(self, size, ext = True):
        size = float(size)
        if size < self.GB:
            return ("%.3f MB" if ext else "%.3f") % (size/self.MB)
        elif size < 10*self.TB:
            return ("%.3f GB" if ext else "%.3f") % (size/self.GB)
        else:
            return ("%.3f TB" if ext else "%.3f") % (size/self.TB)
    
    # seconds to human-readible string
    def getTimeString(self,seconds):
        #try:
            seconds = long(float(seconds))
            seconds = abs(time.time() - seconds)
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
         
            minutes = long(minutes)
            hours = long(hours)
            days = long(days)
            
            duration = []
            if days > 100:
                duration.append('>100 days')
            else:
                if days > 0:
                    duration.append('%d day' % days + 's'*(days != 1))
                if hours > 0:
                    duration.append('%d hour' % hours + 's'*(hours != 1))
                if minutes > 0:
                    duration.append('%d minute' % minutes + 's'*(minutes != 1))
                #if seconds > 0:
                #    duration.append('%d second' % seconds + 's'*(seconds != 1))
            return ' '.join(duration)
        #except:
        #    return "NA"
        
def addContent(parent, content):
    if ET.iselement(parent):
        if ET.iselement(content):
            parent.append(content)
        else:
            parent.text = content
    else:
        if ET.iselement(content):
            parent.text = ET.tostring(content)
        else:
            parent.text = content
            