import bpy
import math
import mathutils
import bmesh
import struct
import logging

from mathutils import Vector, Quaternion
from ..settings import TracerData, TracerProperties
from ..AbstractParameter import Parameter, NodeTypes
from ..SceneObjects.SceneObject import SceneObject
from ..SceneObjects.SceneBoneObject import SceneBoneObject
from ..SceneObjects.SceneObjectCamera import SceneObjectCamera
from ..SceneObjects.SceneObjectLight import SceneObjectLight
from ..SceneObjects.SceneObjectSpotLight import SceneObjectSpotLight
from ..SceneObjects.SceneCharacterObject import SceneCharacterObject

class SceneManager:

    def __init__(self) -> None:
        self.logger = logging.getLogger("TRACER_LOGGER.SCENE_MANAGER")
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(console_handler)

        self.tracer_data : TracerData = None
        self.tracer_properties : TracerProperties = None
        self.scene_object_id_counter = 0
        

    def initialize_manager(self):
        self.tracer_data= bpy.context.window_manager.tracer_data
        self.tracer_properties = bpy.context.scene.tracer_properties

    def gather_scene_data(self):
        self.tracer_data.clear_tracer_data()
        raw_bl_objects: list[bpy.types.Object] = self.get_object_list()

        for bl_obj in raw_bl_objects:
            self.logger.debug("Processing object: %s", bl_obj.name)

            if bl_obj.type == 'ARMATURE':
                self.gather_armature(bl_obj)
                #TODO process armature and bones as scene OBJ
            elif bl_obj.type == 'CAMERA':
                #TODO process camera as sceneCamera OBJ
                self.logger.debug("TODO Processing camera: %s", bl_obj.name)
            elif bl_obj.type == 'LIGHT':
                #TODO process light based on light or spot. OBJ
                self.logger.debug("TODO Processing light: %s", bl_obj.name)
            else:
                #TODO process generic obj in scene as scene OBJ
                self.tracer_data.SceneObjects.append(SceneObject(bl_obj))
                bl_obj.tracer_id = len(self.tracer_data.SceneObjects) -1
                self.logger.debug("TODO Processing generic object: %s", bl_obj.name)


    def get_object_list(self):
        parent_object_name = "TRACER Scene Root"
        parent_object = bpy.data.objects.get(parent_object_name)
        return parent_object.children_recursive

    def gather_armature(self, armature : bpy.types.Object):
        
        self.tracer_data.SceneObjects.append(SceneCharacterObject(armature))
        
        armature.tracer_id = len(self.tracer_data.SceneObjects) -1

        for bone in armature.pose.bones:
            #print(type(bone))
            _bone: bpy.types.PoseBone = bone
            self.tracer_data.SceneObjects.append(SceneBoneObject(_bone, armature))
            #bone.tracer_id = len(self.tracer_data.SceneObjects) -1 


