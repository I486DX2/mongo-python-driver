# Copyright 2009-2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the Binary wrapper."""

import base64
import copy
import pickle
import sys
import unittest
try:
    import uuid
    should_test_uuid = True
except ImportError:
    should_test_uuid = False

sys.path[0:0] = [""]

import bson

from bson.binary import *
from bson.py3compat import b, binary_type
from bson.son import SON
from nose.plugins.skip import SkipTest
from test.test_client import get_client


class TestBinary(unittest.TestCase):

    def setUp(self):
        pass

    def test_binary(self):
        a_string = "hello world"
        a_binary = Binary(b("hello world"))
        self.assertTrue(a_binary.startswith(b("hello")))
        self.assertTrue(a_binary.endswith(b("world")))
        self.assertTrue(isinstance(a_binary, Binary))
        self.assertFalse(isinstance(a_string, Binary))

    def test_exceptions(self):
        self.assertRaises(TypeError, Binary, None)
        self.assertRaises(TypeError, Binary, u"hello")
        self.assertRaises(TypeError, Binary, 5)
        self.assertRaises(TypeError, Binary, 10.2)
        self.assertRaises(TypeError, Binary, b("hello"), None)
        self.assertRaises(TypeError, Binary, b("hello"), "100")
        self.assertRaises(ValueError, Binary, b("hello"), -1)
        self.assertRaises(ValueError, Binary, b("hello"), 256)
        self.assertTrue(Binary(b("hello"), 0))
        self.assertTrue(Binary(b("hello"), 255))

    def test_subtype(self):
        one = Binary(b("hello"))
        self.assertEqual(one.subtype, 0)
        two = Binary(b("hello"), 2)
        self.assertEqual(two.subtype, 2)
        three = Binary(b("hello"), 100)
        self.assertEqual(three.subtype, 100)

    def test_equality(self):
        two = Binary(b("hello"))
        three = Binary(b("hello"), 100)
        self.assertNotEqual(two, three)
        self.assertEqual(three, Binary(b("hello"), 100))
        self.assertEqual(two, Binary(b("hello")))
        self.assertNotEqual(two, Binary(b("hello ")))
        self.assertNotEqual(b("hello"), Binary(b("hello")))

        # Explicitly test inequality
        self.assertFalse(three != Binary(b("hello"), 100))
        self.assertFalse(two != Binary(b("hello")))

    def test_repr(self):
        one = Binary(b("hello world"))
        self.assertEqual(repr(one),
                         "Binary(%s, 0)" % (repr(b("hello world")),))
        two = Binary(b("hello world"), 2)
        self.assertEqual(repr(two),
                         "Binary(%s, 2)" % (repr(b("hello world")),))
        three = Binary(b("\x08\xFF"))
        self.assertEqual(repr(three),
                         "Binary(%s, 0)" % (repr(b("\x08\xFF")),))
        four = Binary(b("\x08\xFF"), 2)
        self.assertEqual(repr(four),
                         "Binary(%s, 2)" % (repr(b("\x08\xFF")),))
        five = Binary(b("test"), 100)
        self.assertEqual(repr(five),
                         "Binary(%s, 100)" % (repr(b("test")),))

    def test_legacy_java_uuid(self):
        if not should_test_uuid:
            raise SkipTest("No uuid module")

        # Generated by the Java driver
        from_java = b('bAAAAAdfaWQAUCBQxkVm+XdxJ9tOBW5ld2d1aWQAEAAAAAMIQkfACFu'
                      'Z/0RustLOU/G6Am5ld2d1aWRzdHJpbmcAJQAAAGZmOTk1YjA4LWMwND'
                      'ctNDIwOC1iYWYxLTUzY2VkMmIyNmU0NAAAbAAAAAdfaWQAUCBQxkVm+'
                      'XdxJ9tPBW5ld2d1aWQAEAAAAANgS/xhRXXv8kfIec+dYdyCAm5ld2d1'
                      'aWRzdHJpbmcAJQAAAGYyZWY3NTQ1LTYxZmMtNGI2MC04MmRjLTYxOWR'
                      'jZjc5Yzg0NwAAbAAAAAdfaWQAUCBQxkVm+XdxJ9tQBW5ld2d1aWQAEA'
                      'AAAAPqREIbhZPUJOSdHCJIgaqNAm5ld2d1aWRzdHJpbmcAJQAAADI0Z'
                      'DQ5Mzg1LTFiNDItNDRlYS04ZGFhLTgxNDgyMjFjOWRlNAAAbAAAAAdf'
                      'aWQAUCBQxkVm+XdxJ9tRBW5ld2d1aWQAEAAAAANjQBn/aQuNfRyfNyx'
                      '29COkAm5ld2d1aWRzdHJpbmcAJQAAADdkOGQwYjY5LWZmMTktNDA2My'
                      '1hNDIzLWY0NzYyYzM3OWYxYwAAbAAAAAdfaWQAUCBQxkVm+XdxJ9tSB'
                      'W5ld2d1aWQAEAAAAAMtSv/Et1cAQUFHUYevqxaLAm5ld2d1aWRzdHJp'
                      'bmcAJQAAADQxMDA1N2I3LWM0ZmYtNGEyZC04YjE2LWFiYWY4NzUxNDc'
                      '0MQAA')

        data = base64.b64decode(from_java)

        # Test decoding
        docs = bson.decode_all(data, SON, False, OLD_UUID_SUBTYPE)
        for d in docs:
            self.assertNotEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        docs = bson.decode_all(data, SON, False, UUID_SUBTYPE)
        for d in docs:
            self.assertNotEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        docs = bson.decode_all(data, SON, False, CSHARP_LEGACY)
        for d in docs:
            self.assertNotEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        docs = bson.decode_all(data, SON, False, JAVA_LEGACY)
        for d in docs:
            self.assertEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        # Test encoding
        encoded = b('').join([bson.BSON.encode(doc,
                                               uuid_subtype=OLD_UUID_SUBTYPE)
                              for doc in docs])
        self.assertNotEqual(data, encoded)

        encoded = b('').join([bson.BSON.encode(doc, uuid_subtype=UUID_SUBTYPE)
                              for doc in docs])
        self.assertNotEqual(data, encoded)

        encoded = b('').join([bson.BSON.encode(doc, uuid_subtype=CSHARP_LEGACY)
                              for doc in docs])
        self.assertNotEqual(data, encoded)

        encoded = b('').join([bson.BSON.encode(doc, uuid_subtype=JAVA_LEGACY)
                              for doc in docs])
        self.assertEqual(data, encoded)

        # Test insert and find
        client = get_client()
        client.pymongo_test.drop_collection('java_uuid')
        coll = client.pymongo_test.java_uuid
        coll.uuid_subtype = JAVA_LEGACY

        coll.insert(docs)
        self.assertEqual(5, coll.count())
        for d in coll.find():
            self.assertEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        coll.uuid_subtype = OLD_UUID_SUBTYPE
        for d in coll.find():
            self.assertNotEqual(d['newguid'], d['newguidstring'])
        client.pymongo_test.drop_collection('java_uuid')

    def test_legacy_csharp_uuid(self):
        if not should_test_uuid:
            raise SkipTest("No uuid module")

        # Generated by the .net driver
        from_csharp = b('ZAAAABBfaWQAAAAAAAVuZXdndWlkABAAAAAD+MkoCd/Jy0iYJ7Vhl'
                        'iF3BAJuZXdndWlkc3RyaW5nACUAAAAwOTI4YzlmOC1jOWRmLTQ4Y2'
                        'ItOTgyNy1iNTYxOTYyMTc3MDQAAGQAAAAQX2lkAAEAAAAFbmV3Z3V'
                        'pZAAQAAAAA9MD0oXQe6VOp7mK4jkttWUCbmV3Z3VpZHN0cmluZwAl'
                        'AAAAODVkMjAzZDMtN2JkMC00ZWE1LWE3YjktOGFlMjM5MmRiNTY1A'
                        'ABkAAAAEF9pZAACAAAABW5ld2d1aWQAEAAAAAPRmIO2auc/Tprq1Z'
                        'oQ1oNYAm5ld2d1aWRzdHJpbmcAJQAAAGI2ODM5OGQxLWU3NmEtNGU'
                        'zZi05YWVhLWQ1OWExMGQ2ODM1OAAAZAAAABBfaWQAAwAAAAVuZXdn'
                        'dWlkABAAAAADISpriopuTEaXIa7arYOCFAJuZXdndWlkc3RyaW5nA'
                        'CUAAAA4YTZiMmEyMS02ZThhLTQ2NGMtOTcyMS1hZWRhYWQ4MzgyMT'
                        'QAAGQAAAAQX2lkAAQAAAAFbmV3Z3VpZAAQAAAAA98eg0CFpGlPihP'
                        'MwOmYGOMCbmV3Z3VpZHN0cmluZwAlAAAANDA4MzFlZGYtYTQ4NS00'
                        'ZjY5LThhMTMtY2NjMGU5OTgxOGUzAAA=')

        data = base64.b64decode(from_csharp)

        # Test decoding
        docs = bson.decode_all(data, SON, False, OLD_UUID_SUBTYPE)
        for d in docs:
            self.assertNotEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        docs = bson.decode_all(data, SON, False, UUID_SUBTYPE)
        for d in docs:
            self.assertNotEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        docs = bson.decode_all(data, SON, False, JAVA_LEGACY)
        for d in docs:
            self.assertNotEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        docs = bson.decode_all(data, SON, False, CSHARP_LEGACY)
        for d in docs:
            self.assertEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        # Test encoding
        encoded = b('').join([bson.BSON.encode(doc,
                                               uuid_subtype=OLD_UUID_SUBTYPE)
                              for doc in docs])
        self.assertNotEqual(data, encoded)

        encoded = b('').join([bson.BSON.encode(doc, uuid_subtype=UUID_SUBTYPE)
                              for doc in docs])
        self.assertNotEqual(data, encoded)

        encoded = b('').join([bson.BSON.encode(doc, uuid_subtype=JAVA_LEGACY)
                              for doc in docs])
        self.assertNotEqual(data, encoded)

        encoded = b('').join([bson.BSON.encode(doc, uuid_subtype=CSHARP_LEGACY)
                              for doc in docs])
        self.assertEqual(data, encoded)

        # Test insert and find
        client = get_client()
        client.pymongo_test.drop_collection('csharp_uuid')
        coll = client.pymongo_test.csharp_uuid
        coll.uuid_subtype = CSHARP_LEGACY

        coll.insert(docs)
        self.assertEqual(5, coll.count())
        for d in coll.find():
            self.assertEqual(d['newguid'], uuid.UUID(d['newguidstring']))

        coll.uuid_subtype = OLD_UUID_SUBTYPE
        for d in coll.find():
            self.assertNotEqual(d['newguid'], d['newguidstring'])
        client.pymongo_test.drop_collection('csharp_uuid')

    def test_uuid_queries(self):
        if not should_test_uuid:
            raise SkipTest("No uuid module")

        c = get_client()
        coll = c.pymongo_test.test
        coll.drop()

        uu = uuid.uuid4()
        # Wrap uu.bytes in binary_type to work
        # around http://bugs.python.org/issue7380.
        coll.insert({'uuid': Binary(binary_type(uu.bytes), 3)})
        self.assertEqual(1, coll.count())

        # Test UUIDLegacy queries.
        coll.uuid_subtype = 4
        self.assertEqual(0, coll.find({'uuid': uu}).count())
        cur = coll.find({'uuid': UUIDLegacy(uu)})
        self.assertEqual(1, cur.count())
        retrieved = cur.next()
        self.assertEqual(uu, retrieved['uuid'])

        # Test regular UUID queries (using subtype 4).
        coll.insert({'uuid': uu})
        self.assertEqual(2, coll.count())
        cur = coll.find({'uuid': uu})
        self.assertEqual(1, cur.count())
        retrieved = cur.next()
        self.assertEqual(uu, retrieved['uuid'])

        # Test both.
        cur = coll.find({'uuid': {'$in': [uu, UUIDLegacy(uu)]}})
        self.assertEqual(2, cur.count())
        coll.drop()

    def test_pickle(self):
        b1 = Binary(b('123'), 2)

        # For testing backwards compatibility with pre-2.4 pymongo
        if PY3:
            p = b("\x80\x03cbson.binary\nBinary\nq\x00C\x03123q\x01\x85q"
                  "\x02\x81q\x03}q\x04X\x10\x00\x00\x00_Binary__subtypeq"
                  "\x05K\x02sb.")
        else:
            p = b("ccopy_reg\n_reconstructor\np0\n(cbson.binary\nBinary\np1\nc"
                  "__builtin__\nstr\np2\nS'123'\np3\ntp4\nRp5\n(dp6\nS'_Binary"
                  "__subtype'\np7\nI2\nsb.")

        if not sys.version.startswith('3.0'):
            self.assertEqual(b1, pickle.loads(p))

        for proto in xrange(pickle.HIGHEST_PROTOCOL + 1):
            self.assertEqual(b1, pickle.loads(pickle.dumps(b1, proto)))

        if should_test_uuid:
            uu = uuid.uuid4()
            uul = UUIDLegacy(uu)

            self.assertEqual(uul, copy.copy(uul))
            self.assertEqual(uul, copy.deepcopy(uul))

            for proto in xrange(pickle.HIGHEST_PROTOCOL + 1):
                self.assertEqual(uul, pickle.loads(pickle.dumps(uul, proto)))


if __name__ == "__main__":
    unittest.main()
