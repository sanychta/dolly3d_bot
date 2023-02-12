###########################################################
#
# Copyright (c) 2005, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ["CommonTest"]

import tacticenv

import unittest, pickle

from pyasm.common import *


class CommonTest(unittest.TestCase):

    def test_all(self):
        self._test_keyword_extract()
        self._test_filesystem_name()
        self._test_container()
        self._test_counter()
        self._test_xpath()
        self._test_marshalling()
        self._test_relative_dir()


    def _test_filesystem_name(self):

        # remove -
        name = 'chr001_.jpg'
        exp  = 'chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # remove -_
        name = 'chr001-_.jpg'
        exp  = 'chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # remove double ..
        name = 'chr001..jpg'
        exp  = 'chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # remove triple ...
        name = 'chr001...jpg'
        exp  = 'chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # remove -
        name = 'chr001-_model.jpg'
        exp  = 'chr001_model.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # keep double --, keep double __
        name = 'chr001--model__v001.jpg'
        exp = 'chr001--model__v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # change space to underscore
        name = 'chr001 model_v001.jpg'
        exp = 'chr001_model_v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))


        # change space to underscore, but keep .
        name = 'chr001_model_v001 .jpg'
        exp = 'chr001_model_v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # remove bad characters
        name = 'ch%r001_model_v001?! .jpg'
        exp = 'chr001_model_v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # allow %0.4d convention 
        name = 'chr001_model.%0.4d.jpg'
        exp = 'chr001_model.%0.4d.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # start with a .
        name = '.chr001.jpg'
        exp = '.chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))
        
        # ends with a .
        name = 'chr001.jpg.'
        exp = 'chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))


        # start with a -
        name = '-!chr001.jpg'
        exp = '-chr001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # use a naming convention ! replacement
        name = 'chr001_!_v001.jpg'
        exp = 'chr001_v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # use a naming convention ! replacement
        name = 'chr001_!!_v001.jpg'
        exp = 'chr001_v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))

        # use a naming convention ! replacement
        name = 'chr001__!v001.jpg'
        exp = 'chr001__v001.jpg'
        self.assertEqual(exp, Common.clean_filesystem_name(name))



        # handle python special naming
        name = '__init__.py'
        exp = '__init__.py'
        self.assertEqual(exp, Common.clean_filesystem_name(name))






    def _test_container(self):
        value = "Hello World"
        key = "message"
        Container.put(key,value)

        value2 = Container.get(key)

        self.assertEqual(value,value2)

    def _test_counter(self):

        KEY = "CoreTest:counter"
        Container.start_counter(KEY)
        count = Container.get(KEY)
        self.assertEqual(count, 0)

        Container.increment(KEY)
        Container.increment(KEY)

        count = Container.get(KEY)
        self.assertEqual(count, 2)

        Container.decrement(KEY)

        count = Container.get(KEY)
        self.assertEqual(count, 1)




    def _test_xpath(self):
        xml_string = """
        <snapshot>
            <a>pig</a>
            <a>cow</a>
            <a>horse</a>
            <b>child</b>
            <c name="horse"/>
        </snapshot>
        """
        # build the xml object and find the values using xpath
        xml = Xml()
        xml.read_string(xml_string)


        # test get_node
        nodes = xml.get_nodes("snapshot/a")
        self.assertEqual(3, len(nodes) )
        node = xml.get_node("snapshot/b")
        self.assertEqual(1, node != None)


        xpath = "snapshot/a"
        values = xml.get_values(xpath)

        self.assertEqual("pig",values[0])
        self.assertEqual("cow",values[1])
        self.assertEqual("horse",values[2])

        # test single value
        value = xml.get_value("snapshot/b")
        self.assertEqual("child",value)

        # test getting an attribute
        value = xml.get_value("snapshot/c/@name")
        self.assertEqual("horse",value)

        #xml.dump()




    def _test_marshalling(self):
        seq_code = "434TTT"
        shot_code = "8324"

        class_name = "TestCommand"

        marshaller = Marshaller()
        marshaller.set_class( class_name )
        marshaller.set_option("asset_code", "chr102")
        marshaller.add_arg(seq_code)
        marshaller.add_arg(shot_code)

        pickle1 = pickle.dumps(marshaller)


        marshalled = marshaller.get_marshalled()

        # create a new marshaller
        marshaller2 = Marshaller()
        marshalled2 = marshaller2.get_from_marshalled(marshalled)

        pickle2 = pickle.dumps(marshaller)


        self.assertEqual(pickle1, pickle2)


    def _test_relative_dir(self):

        b = "/data/home/apache/assets/prod/textures"
        a = "/data/home/apache/assets/prod/textures"
        rel = Common.relative_dir(a,b)
        exp = "."
        self.assertEqual(exp,rel)


        a = "/data/home/apache/assets/prod/textures"
        b = "/data/home/apache/assets/prod/textures/prod/product100/final"
        rel = Common.relative_dir(a,b)
        exp = "prod/product100/final"
        self.assertEqual(exp,rel)

        a = "/data/home/apache/assets/prod/textures/prod/product100/final"
        b = "/data/home/apache/assets/prod/textures"
        rel = Common.relative_dir(a,b)
        exp = "../../.."
        self.assertEqual(exp,rel)

        a = "/data/home/apache/assets/prod/textures/prod/product100/final"
        b = "/data/home/apache/assets/prod/assets/product100/final"
        rel = Common.relative_dir(a,b)
        exp = "../../../../assets/product100/final"
        self.assertEqual(exp,rel)

        a = "/data/home/apache/assets/prod/"
        b = "/data/home/apache/assets/prod"
        rel = Common.relative_dir(a,b)
        exp = ""
        self.assertEqual(exp,rel)

        # real example
        a = "/home/apache/html/sthpw/assets/prod2/asset/product/product300/final"
        b = "/home/apache/html/sthpw/assets/prod2/asset/product/product300/texture/torus"
        rel = Common.relative_dir(a,b)
        exp = "../texture/torus"
        self.assertEqual(exp,rel)

        # real example
        a = "/home/apache/html/sthpw/assets/mainframe/asset/bar/bar0002/rig"
        b = "/home/apache/html/sthpw/assets/mainframe/asset/bar/bar0001/model"
        rel = Common.relative_dir(a,b)
        exp = "../../bar0001/model"
        self.assertEqual(exp,rel)



    def _test_keyword_extract(self):

        path = "/theLongAndWindingRoad.jpg"
        keywords = Common.extract_keywords_from_path(path)
        for item in ['the', 'long', 'and', 'winding', 'road', 'jpg']:
            self.assertEqual(True, item in keywords)


        path = "/bigUglyDog-dangerous_black.jpg"
        keywords = Common.extract_keywords_from_path(path)
        for item in ['big','ugly','dog','dangerous','black','jpg']:
            self.assertEqual(True, item in keywords)

        path = "/BOBtheMan.jpg"
        keywords = Common.extract_keywords_from_path(path)
        for item in ['bob', 'the', 'man']:
            self.assertEqual(True, item in keywords)


        path = "/BOB123.jpg"
        keywords = Common.extract_keywords_from_path(path)
        for item in ['bob', 'jpg']:
            self.assertEqual(True, item in keywords)


        path = "/testURLagain-main.txt"
        keywords = Common.extract_keywords_from_path(path)
        for item in ['test', 'url', 'again', 'main', 'txt']:
            self.assertEqual(True, item in keywords)


if __name__ == '__main__':
    unittest.main()



