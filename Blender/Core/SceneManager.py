import bpy
import math
import mathutils
import bmesh
import struct
import logging

from mathutils import Vector, Quaternion
from ..settings import TracerData, TracerProperties
from ..AbstractParameter import Parameter
from ..SceneObjects.SceneObject import SceneObject
from ..SceneObjects.SceneObjectBone import SceneObjectBone
from ..SceneObjects.SceneObjectCamera import SceneObjectCamera
from ..SceneObjects.SceneObjectLight import SceneObjectLight
from ..SceneObjects.SceneObjectSpotLight import SceneObjectSpotLight
from ..SceneObjects.SceneObjectCharacter import SceneObjectCharacter
from ..SceneObjects.SceneObjectMesh import SceneObjectMesh
from ..SceneObjects.SceneObjectPath import SceneObjectPath

class SceneManager:

    def __init__(self) -> None:
        self.logger = logging.getLogger("TRACER_LOGGER.SCENE_MANAGER")
        self.logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(console_handler)

        self.tracer_data : TracerData = None
        self.tracer_properties : TracerProperties = None
        self.scene_object_id_counter = 0 # Probably not necessary
        

    def initialize_manager(self):
        self.tracer_data = bpy.context.window_manager.tracer_data
        self.tracer_properties = bpy.context.scene.tracer_properties

    def get_header_byte_data(self):
        header_byte_array = bytearray([])
    
        light_intensity_factor = 1.0
        sender_id = int(self.tracer_data.cID)

        header_byte_array.extend(struct.pack('f', light_intensity_factor))
        header_byte_array.extend(struct.pack('i', sender_id))
        header_byte_array.extend(struct.pack('i', 60))  # frame rate that should be modified later

        self.tracer_data.header_byte_data = header_byte_array

    def gather_scene_data(self):
        self.tracer_data.clear_tracer_data()
        raw_bl_objects: list[bpy.types.Object] = self.get_object_list()

        for bl_obj in raw_bl_objects:
            self.logger.debug("Processing object: %s", bl_obj.name)

            if bl_obj.type == 'ARMATURE':
                #TODO process armature and bones as SceneObjectCharacter and SceneObjectBones
                self.logger.debug("TODO Processing character: %s", bl_obj.name)
                self.tracer_data.scene_objects.append(SceneObjectCharacter(bl_obj))
                self.process_bones(bl_obj)
            elif bl_obj.type == 'CAMERA':
                #TODO process camera as SceneObjectCamera
                self.logger.debug("TODO Processing camera: %s", bl_obj.name)
                self.tracer_data.scene_objects.append(SceneObjectCamera(bl_obj))
            elif bl_obj.type == 'LIGHT':
                #TODO process spot light as SceneObjectLight
                if bl_obj.data.type == 'SPOT':
                    #TODO process spot light as SceneObjectSpotLight
                    self.logger.debug("TODO Processing spot light: %s", bl_obj.name)
                    self.tracer_data.scene_objects.append(SceneObjectSpotLight(bl_obj))
                else:
                    self.logger.debug("TODO Processing light: %s", bl_obj.name)
                    self.tracer_data.scene_objects.append(SceneObjectLight(bl_obj))
            elif bl_obj.get("Control Points", False):
                self.logger.debug("TODO Processing path: %s", bl_obj.name)
                self.tracer_data.scene_objects.append(SceneObjectPath(bl_obj))
            else:
                #TODO process generic obj in scene as SceneObject
                self.logger.debug("TODO Processing generic object: %s", bl_obj.name)
                self.tracer_data.scene_objects.append(SceneObject(bl_obj))
                
    def get_object_list(self) -> list[bpy.types.Object]:
        parent_object_name = "TRACER Scene Root"
        parent_object: bpy.types.Object = bpy.data.objects.get(parent_object_name)
        if parent_object:
            return parent_object.children_recursive
        else:
            return []

    def process_bones(self, armature_obj : bpy.types.Object):
        for bone in armature_obj.pose.bones:
            #print(type(bone))
            _bone: bpy.types.PoseBone = bone
            self.tracer_data.scene_objects.append(SceneObjectBone(_bone, armature_obj))


