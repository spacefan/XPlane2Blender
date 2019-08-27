import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestTextureAutodetectApplied(XPlaneTestCase):
    def test_OBJCustomLightTexSkip(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        self.assertTrue(root_object.xplane.autodetectTextures)
        self.assertEqual(root_object.xplane.texture,"")
        self.assertEqual(root_object.xplane.texture_lit,"")
        self.assertEqual(root_object.xplane.texture_normal,"")
        self.assertEqual(root_object.xplane.texture_draped,"")
        self.assertEqual(root_object.xplane.texture_draped_normal,"")

    def test_OBJFindTextures(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\texture"
        self.assertFalse(root_object.xplane.autodetectTextures)
        self.assertEqual(root_object.xplane.texture,        tex_used + ".png")
        self.assertEqual(root_object.xplane.texture_lit,    tex_used + "_NML.png")
        self.assertEqual(root_object.xplane.texture_normal, tex_used + "_LIT.png")
        self.assertEqual(root_object.xplane.texture_draped,"")
        self.assertEqual(root_object.xplane.texture_draped_normal,"")

    def test_OBJFindTexturesDDS(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\textureB"
        self.assertFalse(root_object.xplane.autodetectTextures)
        self.assertEqual(root_object.xplane.texture,        tex_used + ".dds")
        self.assertEqual(root_object.xplane.texture_normal, tex_used + "_NML.dds")
        self.assertEqual(root_object.xplane.texture_draped,"")
        self.assertEqual(root_object.xplane.texture_draped_normal,"")

    def test_OBJFindTexturesDraped(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        self.assertFalse(root_object.xplane.autodetectTextures)
        tex_used = r"//tex\texture"
        self.assertEqual(root_object.xplane.texture,        tex_used + ".png")
        self.assertEqual(root_object.xplane.texture_normal, tex_used + "_NML.png")
        self.assertEqual(root_object.xplane.texture_lit,    tex_used + "_LIT.png")

        tex_used_draped = r"//tex/draped.png"
        self.assertEqual(root_object.xplane.texture_draped,        tex_used_draped + ".png")
        self.assertEqual(root_object.xplane.texture_draped_normal, tex_used_draped + "_NML.png")

    def test_OBJNoPanelTexture(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        root_object = bpy.data.objects[inspect.stack()[0].function[5:]]
        tex_used = r"//tex\texture"
        self.assertFalse(root_object.xplane.autodetectTextures)
        self.assertEqual(root_object.xplane.texture,        tex_used + ".png")
        self.assertEqual(root_object.xplane.texture_lit,    tex_used + "_NML.png")
        self.assertEqual(root_object.xplane.texture_normal, tex_used + "_LIT.png")
        self.assertEqual(root_object.xplane.texture_draped,"")
        self.assertEqual(root_object.xplane.texture_draped_normal,"")


runTestCases([TestTextureAutodetectApplied])
