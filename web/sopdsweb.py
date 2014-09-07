#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
#from urllib import parse
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler
#import sopdscfg
from wsgiref.util import setup_testing_defaults
import traceback

import os
import sys
import functools
import mimetypes
import urllib.request
import xml.sax
import re
import jinja2

from pprint import pprint

mime = mimetypes.MimeTypes()

class OpdsDocument:
    def __init__(self, url):
        """
        A simple function to converts XML data into native Python object.
        """

        non_id_char = re.compile('[^_0-9a-zA-Z]')
        def _name_mangle(name):
            return non_id_char.sub('_', name)

        class DataNode(object):
            def __init__(self):
                self._attrs = {}    # XML attributes and child elements
                self.data = None    # child text data

            def __len__(self):
                # treat single element as a list of 1
                return 1

            def __getitem__(self, key):
                if isinstance(key, str):
                    return self._attrs.get(key,None)
                else:
                    return [self][key]

                def __contains__(self, name):
                    return self._attrs.has_key(name)

                def __nonzero__(self):
                    return bool(self._attrs or self.data)

            def __getattr__(self, name):
                if name.startswith('__'):
                    # need to do this for Python special methods???
                    raise AttributeError(name)
                return self._attrs.get(name,None)

            def _add_xml_attr(self, name, value):
                if name in self._attrs:
                    # multiple attribute of the same name are represented by a list
                    children = self._attrs[name]
                    if not isinstance(children, list):
                        children = [children]
                        self._attrs[name] = children
                    children.append(value)
                else:
                    self._attrs[name] = value

            def __str__(self):
                return self.data or ''

            def __repr__(self):
                items = sorted(self._attrs.items())
                if self.data:
                    items.append(('data', self.data))
                return '{%s}' % ', '.join(['%s:%s' % (k,repr(v)) for k,v in items])

        class TreeBuilder(xml.sax.handler.ContentHandler):
            def __init__(self):
                self.stack = []
                self.root = DataNode()
                self.current = self.root
                self.text_parts = []

            def startElement(self, name, attrs):
                self.stack.append((self.current, self.text_parts))
                self.current = DataNode()
                self.text_parts = []
                # xml attributes --> python attributes
                for k, v in attrs.items():
                    self.current._add_xml_attr(_name_mangle(k), v)

            def endElement(self, name):
                text = ''.join(self.text_parts).strip()
                if text:
                    self.current.data = text
                if self.current._attrs:
                    obj = self.current
                else:
                    # a text only node is simply represented by the string
                    obj = text or ''
                self.current, self.text_parts = self.stack.pop()
                self.current._add_xml_attr(_name_mangle(name), obj)

            def characters(self, content):
                self.text_parts.append(content)

        resp = urllib.request.urlopen(url)
        builder = TreeBuilder()

        xml.sax.parseString(resp.read(), builder)
        self.variables = builder.root._attrs


        self.variables['feed_kind'] = self._getFeedKind()

    def _getFeedKind(self):
        for link in self.variables['feed']['link']:
            if link['rel'] != 'self':
                continue

            type = "%s" % link['type'].lower()
            b = type.rfind("kind=");
            if b < 0:
                continue
            b += 5

            e = type.find(";", b)
            if e < 0:
                return type[b:]
            else:
                return type[b:e]



class Response:
    #********************************************
    #
    #********************************************
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.url = self.environ['PATH_INFO']
        self.templatePath = "templates/" + config.WEB_THEME
        self.parseQueryString(environ['QUERY_STRING'])

        self.opdsHost = config.OPDS_HOST
        if ((self.opdsHost == 'localhost') or
            (self.opdsHost.startsWith("127."))):
            self.opdsHost = self.environ['HTTP_HOST'].replace(":%d" % config.WEB_PORT, '')

        self.opdsUrl= "%s://%s:%d" % (
                        config.OPDS_PROTO,
                        self.opdsHost,
                        config.OPDS_PORT)


    #********************************************
    #
    #********************************************
    def parseQueryString(self, quersString):
        self.query = urllib.parse.parse_qs(quersString, keep_blank_values=True)
        for key in self.query:
            self.query[key] = list(map(lambda x: urllib.parse.unquote(x), self.query[key]))


    #********************************************
    #
    #********************************************
    def send404(self):
        headers = [('Content-type', 'text/html; charset=utf-8')]

        self.start_response('404 Not Found', headers)

        return [(("<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n"
                 "<html><head>\n"
                 "<title>404 Not Found</title>\n"
                 "</head><body>\n"
                 "<h1>Not Found</h1>\n"
                 "<p>The requested URL %s was not found on this server.</p>\n"
                 "<hr>\n"
                 "<address>SimpleOPDS web server at %s</address>\n"
                 "</body></html>\n") % (self.environ['PATH_INFO'], self.environ['HTTP_HOST'])
                ).encode("utf-8")]


    #********************************************
    #
    #********************************************
    def sendError(self, title, message):
        headers = [('Content-type', 'text/html; charset=utf-8')]

        self.start_response('200 OK', headers)

        return [(("<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n"
                 "<html><head>\n"
                 "<title>%s</title>\n"
                 "</head><body>\n"
                 "<h1>%s</h1>\n"
                 "<p>%s.</p>\n"
                 "<hr>\n"
                 "<address>SimpleOPDS web server at %s</address>\n"
                 "</body></html>\n") % (
                    title,
                    title,
                    message.replace('\n', '<br>\n'),
                    self.environ['HTTP_HOST'])
                ).encode("utf-8")]


    #********************************************
    #
    #********************************************
    def process(self):

        if self.url == '/env.html':
            return self.sendEnv()

        url = self.url
        webRoot = config.WEB_ROOT_DIR + "/" + self.templatePath;

        if os.path.isdir(webRoot  + url):
            if url.endswith("/"):
                url += "index.html"
            else:
                url += "/index.html"

        if os.path.isfile(webRoot + url):
            if url.endswith(".html"):
                return self.sendTemplate(url)
            else:
                return self.sendStatic(url)

        return self.send404()


    #********************************************
    #
    #********************************************
    def sendEnv(self):
        setup_testing_defaults(self.environ)
        status = '200 OK'
        headers = [('Content-type', 'text/plain; charset=utf-8')]
        self.start_response(status, headers)

        ret = [("%s: %s\n" % (key, value)).encode("utf-8")
            for key, value in self.environ.items()]

        return ret


    #********************************************
    #
    #********************************************
    def sendStatic(self, url):
        fileName = config.WEB_ROOT_DIR + "/" + self.templatePath + url

        (mimeType, mimeEncoding)  = mime.guess_type(fileName)
        f = open(fileName, 'rb')

        headers = [('Content-type', mimeType),
                   ('Content-Length', "%d" % os.path.getsize(fileName))
                  ]

        lines = f.readlines()
        f.close()

        self.start_response('200 OK', headers)
        return lines;


    #********************************************
    #
    #********************************************
    def sendTemplate(self, url):
        variables = {}

        variables['env'] = {}
        variables['env']['query']=self.query
        variables['env']['query_string']=self.environ['QUERY_STRING']
        variables['env']['path_info']=self.environ['PATH_INFO']
        variables['env']['http_host']=self.environ['HTTP_HOST']

        variables['env']['opds'] = {}

        variables['env']['opds']['host']   = self.opdsHost
        variables['env']['opds']['port']   = "%d" % config.OPDS_PORT
        variables['env']['opds']['url']    = self.opdsUrl
        variables['env']['opds']['query']  = ("?" + self.environ['QUERY_STRING'], '') [self.environ['QUERY_STRING'] == ""]

        try:
            jinjaEnv = jinja2.Environment(
                loader=jinja2.PackageLoader('sopdsweb', self.templatePath),
                undefined = jinja2.DebugUndefined
                )

            jinjaEnv.globals['opdsRequest'] = self.opdsRequest
            jinjaEnv.globals['getEntryLink'] = self.jinja_GetEntryLink
            jinjaEnv.globals['getDownloadLinks'] = self.jinja_GetDownloadLinks
            jinjaEnv.globals['prepareSearchLink'] = self.jinjaPrepareSearchLink
            jinjaEnv.globals['parseSearchLink'] = self.jinjaParseSearchLink
            jinjaEnv.globals['urlQuote'] = urllib.parse.quote
            jinjaEnv.globals['urlUnquote'] = urllib.parse.unquote

            jinjaTemplate = jinjaEnv.get_template(url)

            res = jinjaTemplate.render(variables)

        except jinja2.TemplateNotFound as e:
            traceback.print_exc()
            self.templateError()
            return self.sendError("Template error", 'template "%s/%s" not found.' % (self.templatePath,  e))

        except (jinja2.TemplateSyntaxError,
                jinja2.UndefinedError,
                TypeError
               ) as e:
            traceback.print_exc()
            return self.sendError("Template error", "%s" % e)

        headers = [('Content-type', 'text/html; charset=utf-8')]
        self.start_response('200 OK', headers)

        return [res.encode('utf-8')]


    #********************************************
    #
    #********************************************
    def opdsRequest(self, request):
        url = "%s://%s:%d%s" % ( config.OPDS_PROTO,
                                  config.OPDS_HOST,
                                  config.OPDS_PORT,
                                  request)

        print(url)
        opds = OpdsDocument(url)
        return opds.variables


    #********************************************
    #
    #********************************************
    def jinjaPrepareSearchLink(self, template,
                          searchTerms,
                          count = '0',
                          startIndex = '0',
                          language = '*',
                          inputEncoding = 'UTF-8',
                          outputEncoding = 'UTF-8'
                          ):

        def repl(template, key, value):
            if isinstance(value, list):
                value = value[0]
            print("* %s (%s), %s (%s)" % (key, type(key), value, type(value)))
            template = template.replace('{%s}'  % key, urllib.parse.quote(value))
            template = template.replace('{%s?}' % key, urllib.parse.quote(value))
            return template

        if isinstance(template, list):
            template = template[0]

        res = template
        res = repl(res, 'count',          count)
        res = repl(res, 'startIndex',     startIndex)
        res = repl(res, 'language',       language)
        res = repl(res, 'inputEncoding',  inputEncoding)
        res = repl(res, 'outputEncoding', outputEncoding)
        res = repl(res, 'searchTerms',    searchTerms)

        return res


    #********************************************
    #
    #********************************************
    def jinjaParseSearchLink(self, link):


        href = urllib.parse.unquote(link['href'])
        if href.startswith('?'):
            href = href[1:]

        res = []
        fixedItems =[]
        notFixedItems =[]
        for h in href.split('&'):
            (key, val) = h.split('=')

            item = {}
            res.append(item)

            item['name']     = key
            item['fixed']    = not val.startswith('{')
            item['required'] = not val.endswith('?}')
            item['template'] = val

            if item['fixed']:
                item['value'] = val
                fixedItems.append(item)
            else:
                item['value'] = ''
                notFixedItems.append(item)

        def isQueryForItem(item):
            for f in fixedItems:
                if (not f['name'] in self.query or
                   self.query[f['name']][0] != f['value']):
                   return False
            return True

        for item in notFixedItems:
            if isQueryForItem(item):
                item['value'] = self.query[item['name']][0]

        return res


    #********************************************
    #
    #********************************************
    def jinja_GetEntryLink(self, entry):
        result = ""
        for link in entry['link']:
            result = link

        return result


    #********************************************
    #
    #********************************************
    def jinja_GetDownloadLinks(self, entry, types = ["application/fb2", "application/fb2+zip", "application/epub+zip", "application/mobi+zip"]):

        result = []

        for request in types:
            for link in entry['link']:
                if link['rel'] != "http://opds-spec.org/acquisition":
                    continue

                if link['type'] == request:
                    link.href = self.opdsUrl + link.href
                    result.append(link)

        return result




#************************************************
#
#************************************************
def serve(environ, start_response):
    response = Response(environ, start_response)
    return response.process();


#************************************************
#
#************************************************
def start_server(config):

    try:
       httpd = make_server(config.WEB_BIND_ADDRESS,
                           config.WEB_PORT,
                           serve)

       print('Started Simple OPDS WEB server on port ', config.WEB_PORT)
       httpd.serve_forever()

    except KeyboardInterrupt:
       print('^C received, shutting down the web server')
       httpd.socket.close()



#************************************************
#
#************************************************
class Config:
    def __init__(self):
        self.WEB_PORT = 8082
        self.WEB_BIND_ADDRESS=""
        self.WEB_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
        self.WEB_THEME = 'e-ink'
        self.WEB_INDEX_TEMPLATE = 'index.html'

        self.OPDS_PROTO     = 'http'
        self.OPDS_HOST      = 'localhost'
        self.OPDS_PORT      = 8081
        self.OPDS_ROOT_LINK = "?00"


config = Config()

#************************************************
#
#************************************************
if __name__ == "__main__":
    #config=sopdscfg.cfgreader()
    config = Config()
    start_server(config)
