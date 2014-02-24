#!/usr/bin/env python

import ConfigParser
from os import listdir
from os.path import isfile, join, expanduser, getsize
import humanize # from: https://pypi.python.org/pypi/humanize
import web # from: http://webpy.org/

urls = (
    '/', '_Index',
    '/about', '_About',
    '/upload', '_Upload',
    '/system/([a-zA-Z\d]+)/', '_System'
)

app = web.application(urls, globals())
render = web.template.render('templates', base='base')

class System:
    def __init__(self,id,name,enabled):
        self.Id = id
        self.Name = name
        self.Enabled = enabled

    def eq(self,id):
        return self.Id==id

    def romPath(self,systems):
        return systems.BasePath+'/'+self.Id+'/'

    def games(self):
        html = ""
        for game in [ f for f in listdir(self.romPath(systems)) if isfile(join(self.romPath(systems),f)) ]:
            html += "<tr><td>"+game+"</td><td><code>"+humanize.naturalsize(getsize(self.romPath(systems)+game), binary=True)+"</code></td></tr>"
        return html
    def row(self):
        return "<tr><td><a href='/system/"+self.Id+"/' class='btn btn-primary btn-xs'>view</a></td><td>"+self.Name+"</td></tr>"

class Systems:
    def __init__(self,systems,basePath):
        self.Systems = systems
        self.BasePath = expanduser(basePath)

    def append(self,system):
        self.Systems.append(system)

    def find(self,systemId):
        for system in self.Systems:
            if system.eq(systemId):
                return system
        return None

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

systems = Systems(*readConfig())

class _Index:
    def GET(self):
        return render.index(systems.table())
class _About:
    def GET(self):
        return render.about()
class _Upload:
    def POST(self):
        post = web.input(file={})
        if 'file' in post: # to check if the file-object is created
            system = systems.find(post.system)
            if system is None:
                raise web.notfound('Cannot find system')
            else:
                filepath=post.file.filename.replace('\\','/') # replaces the windows-style slashes with linux ones.
                filename=filepath.split('/')[-1] # splits the and chooses the last part (the filename with extension)
                fout = open(system.romPath(systems) + filename,'w') # creates the file where the uploaded file should be stored
                fout.write(post.file.file.read()) # writes the uploaded file to the newly created file.
                fout.close() # closes the file, upload complete.
                raise web.seeother('/system/' + system.Id + '/')
class _System:
    def GET(self,systemId):
        if systems.find(systemId) is None:
            return web.notfound('Cannot find system')
        else:
            return render.system(systems.find(systemId))

if __name__ == "__main__":
    app.run()