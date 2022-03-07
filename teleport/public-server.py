from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor

if __name__ == '__main__':
    reactor.listenTCP(80, Site(File("./public")))
    reactor.run()
