#!/usr/bin/env python

import ConfigParser
import os
import json
import humanize # from: https://pypi.python.org/pypi/humanize
import web # from: http://webpy.org/

urls = (
    '/', '_Index',
    '/about', '_About',
    '/delete', '_Delete',
    '/rename', '_Rename',
    '/upload', '_Upload',
    '/system/([a-zA-Z\d]+)/', '_System'
)

app = web.application(urls, globals())
render = web.template.render('templates', base='base')

class System:
    def __init__(self,guid,name,enabled):
        self.Id = guid
        self.Name = name
        self.Enabled = enabled

    def eq(self,guid):
        return self.Id==guid
    
    def romPath(self,systems):
        return systems.BasePath+'/'+self.Id+'/'

    def games(self):
        html = ""
        try:
            for game in [ f for f in os.listdir(self.romPath(controller)) if os.path.isfile(os.path.join(self.romPath(controller),f)) ]:
                html += "<tr><td class='FileName'>"+game+"</td><td class='text-right'><code>"+humanize.naturalsize(os.path.getsize(self.romPath(controller)+game), binary=True)+"</code></td></tr>"
        except OSError:
            html = ""
        return html
    def row(self):
        return "<tr><td><a href='/system/"+self.Id+"/' class='btn btn-primary btn-xs'>view</a></td><td>"+self.Name+"</td></tr>"

class Controller:
    def __init__(self,systems,basePath):
        self.Systems = systems
        self.BasePath = os.path.expanduser(basePath)

    def append(self,system):
        self.Systems.append(system)

    def findSystem(self,systemId):
        for system in self.Systems:
            if system.eq(systemId):
                return system
        return None

    def getFreeSpace(self):
        """ Return folder/drive free space (humanized)
        """
        st = os.statvfs(self.BasePath)
        return humanize.naturalsize(st.f_bavail * st.f_frsize, binary=True)

    def table(self):
        html = ""
        for system in self.Systems:
            html += system.row()
        return html

def readConfig():
    config = ConfigParser.ConfigParser()
    config.read('RetroPage.cfg')
    data = []
    for system in config.get('RetroPage', 'Systems').split(','):
        data.append(System(system, config.get(system, 'Name'), config.getboolean(system, 'Enabled')))
    return data, config.get('RetroPage', 'BasePath')

controller = Controller(*readConfig())

class _Index:
    def GET(self):
        return render.index(controller)
class _About:
    def GET(self):
        return render.about(controller)
class _Delete:
    def POST(self):
        web.header('Content-Type', 'application/json')
        post = web.input()
        system = controller.findSystem(post.system)
        if system is None:
            return json.dumps({'Success': False, 'error': 'Cannot find system'})
        else:
            os.remove(system.romPath(controller)+post['name'])
            return json.dumps({'Success': True})
class _Rename:
    def POST(self):
        web.header('Content-Type', 'application/json')
        post = web.input()
        system = controller.findSystem(post.system)
        if system is None:
            return json.dumps({'Success': False, 'error': 'Cannot find system'})
        else:
            os.rename(system.romPath(controller)+post['from'], system.romPath(controller)+post['to'])
            return json.dumps({'Success': True})
class _Upload:
    def POST(self):
        web.header('Content-Type', 'application/json')
        post = web.input(file={})
        if 'file' in post: # to check if the file-object is created
            system = controller.findSystem(post.system)
            if system is None:
                return json.dumps({'Success': False, 'error': 'Cannot find system'})
            else:
                filepath=post.file.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
                filename=filepath.split('/')[-1] # splits the and chooses the last part (the filename with extension)
                fout = open(system.romPath(controller) + filename,'w') # creates the file where the uploaded file should be stored
                fout.write(post.file.file.read()) # writes the uploaded file to the newly created file.
                fout.close() # closes the file, upload complete.
                return json.dumps({'Success': True})
class _System:
    def GET(self,systemId):
        if controller.findSystem(systemId) is None:
            raise web.notfound('Cannot find system')
        else:
            return render.system(controller, controller.findSystem(systemId))

if __name__ == "__main__":
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", 1980))
