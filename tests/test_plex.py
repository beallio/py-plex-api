import unittest
import plexapi
import json
from xml.etree.ElementTree import Element


class testPlexServer(unittest.TestCase):
    server_url, server_port = 'http://192.168.1.101', 32400
    server = None
    library = None

    @classmethod
    def setUpClass(cls):
        cls.server = plexapi.Server(testPlexServer.server_url,
                            testPlexServer.server_port)
        cls.library = cls.server.library

    def test_bad_connection(self):
        try:
            plexapi.Server('http://192.168.1.102', testPlexServer.server_port)
        except:
            pass

    def test_good_connection(self):
        testPlexServer.server = testPlexServer.server

    def test_print_server(self):
        plex = testPlexServer.server
        self.assertIsInstance(plex.__str__(), str)

    def test_server_info(self):
        plex = testPlexServer.server
        self.assertIsInstance(json.loads(plex.json), dict)
        self.assertIsInstance(plex.xml, Element)

    def test_server_servers(self):
        plex = testPlexServer.server
        self.assertIsInstance(json.loads(plex.servers.json), dict)
        self.assertIsInstance(plex.servers.xml, Element)

    def test_print_library(self):
        library = testPlexServer.library
        self.assertIsInstance(library.__str__(), str)

    def test_server_stuff(self):
        plex = testPlexServer.server
        library = testPlexServer.library
        tests = [plex.channels, plex.servers, plex.channels, plex.preferences,
                 library.recentlyadded, library.sections]
        for test in tests:
            json_output = test.json
            xml_output = test.xml
            self.assertIsInstance(json_output, str)
            self.assertIsInstance(json.loads(json_output), dict)
            self.assertIsInstance(xml_output, Element)

    def test_server_sections(self):
        library = testPlexServer.library
        tests = [library.recentlyadded.episodes,
                library.recentlyadded.movies]
        for test in tests:
            print test.__class__.__name__
            json_output = test.json
            xml_output = test.xml
            self.assertIsInstance(json_output, str)
            self.assertIsInstance(json.loads(json_output), list)
            self.assertIsInstance(xml_output, list)

    def test_server_items(self):
        plex = testPlexServer.server
        library = testPlexServer.library
        tests = [library.recentlyadded,
                plex.channels, library.sections]
        for test in tests:
            self.assertIsInstance(test.items, list)
            for item in test.items:
                json_output = item.json
                xml_output = item.xml
                self.assertIsInstance(json_output, str)
                self.assertIsInstance(json.loads(json_output), dict)
                self.assertIsInstance(xml_output, Element)