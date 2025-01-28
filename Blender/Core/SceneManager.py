import bpy
#import math
#import mathutils
#import bmesh
import struct
import logging

#from mathutils import Vector, Quaternion
from ..settings import TracerData, TracerProperties
#from ..SceneObjects.AbstractParameter import Parameter
from ..SceneObjects.SceneObject import SceneObject
from ..SceneObjects.SceneObjectBone import SceneObjectBone
from ..SceneObjects.SceneObjectCamera import SceneObjectCamera
from ..SceneObjects.SceneObjectLight import SceneObjectLight
from ..SceneObjects.SceneObjectSpotLight import SceneObjectSpotLight
from ..SceneObjects.SceneObjectCharacter import SceneObjectCharacter
from ..SceneObjects.SceneObjectMesh import SceneObjectMesh
from ..SceneObjects.SceneObjectMeshSkinned import SceneObjectMeshSkinned
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
        self.is_distributed: bool = False
        self.scene_object_id_counter = 0 # Probably not necessary
        
    def initialize_manager(self):
        self.tracer_data = bpy.context.window_manager.tracer_data
        self.tracer_properties = bpy.context.scene.tracer_properties

    ### Collect all the data from the Scene into a list of objects (scene_objects) and a list of *editable* objects (editable-objects) 
    def gather_scene_data(self) -> int:
        self.tracer_data.clear_tracer_data()
        raw_bl_objects: list[bpy.types.Object] = self.get_object_list()

        for bl_obj in raw_bl_objects:
            self.logger.debug("Processing object: %s", bl_obj.name)

            if bl_obj.type == 'ARMATURE':
                #TODO process armature and bones as SceneObjectCharacter and SceneObjectBones
                self.logger.debug("TODO Processing character: %s", bl_obj.name)
                self.tracer_data.scene_objects.append(SceneObjectCharacter(bl_obj))
                self.process_bones(bl_obj)
                #self.tracer_data.character_package.append(CharacterPackageData(bl_obj, raw_bl_objects))
            elif bl_obj.type == 'MESH':
                if bl_obj.parent == 'ARMATURE':
                    self.logger.debug("TODO Processing Skinned Mesh: %s", bl_obj.name)
                    self.tracer_data.scene_objects.append(SceneObjectMeshSkinned(bl_obj))
                else:
                    self.logger.debug("TODO Processing Mesh: %s", bl_obj.name)
                    self.tracer_data.scene_objects.append(SceneObjectMesh(bl_obj))
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

        self.populate_header_byte_data()
        self.populate_nodes_byte_array()
        self.populate_meshes_byte_array()
        self.populate_materials_byte_array()
        self.populate_textures_byte_array()
        self.populate_characters_byte_array()

        return len(self.tracer_data.scene_objects)

                
    def get_object_list(self) -> list[bpy.types.Object]:
        parent_object_name = "TRACER Scene Root"
        parent_object: bpy.types.Object = bpy.data.objects.get(parent_object_name)
        if parent_object:
            return parent_object.children_recursive
        else:
            return []
        
    def get_scene_object(self, object_name: str) -> SceneObject:
        for scene_object in self.tracer_data.scene_objects:
            if scene_object.name == object_name:
                return scene_object
        return None

    def process_bones(self, armature_obj : bpy.types.Object):
        for pose_bone in armature_obj.pose.bones:
            self.tracer_data.scene_objects.append(SceneObjectBone(pose_bone, armature_obj))

    ### Generate the Byte Array describing the Header of the Scene
    def populate_header_byte_data(self):
        header_byte_array = bytearray([])
    
        light_intensity_factor = 1.0
        sender_id = int(self.tracer_data.cID)

        header_byte_array.extend(struct.pack('f', light_intensity_factor))
        header_byte_array.extend(struct.pack('i', sender_id))
        header_byte_array.extend(struct.pack('i', 60))  # frame rate that should be modified later

        self.tracer_data.header_byte_data = header_byte_array

    def populate_nodes_byte_array(self):
        self.tracer_data.nodes_byte_data = bytearray([])
        for node in self.tracer_data.scene_objects:
            self.tracer_data.nodes_byte_data.extend(node.serialise())
    
    def populate_meshes_byte_array(self):
        self.tracer_data.mesh_byte_data = bytearray([])
        for mesh in self.tracer_data.mesh_list:
            self.tracer_data.nodes_byte_data.extend(mesh.serialise())

    def populate_materials_byte_array(self):
        self.tracer_data.materials_byte_data = bytearray([])
        for material in self.tracer_data.material_list:
            self.tracer_data.nodes_byte_data.extend(material.serialise())

    def populate_textures_byte_array(self):
        self.tracer_data.textures_byte_data = bytearray([])
        for tex in self.tracer_data.texture_list:
            self.tracer_data.nodes_byte_data.extend(tex.serialise())

    def populate_characters_byte_array(self):
        self.tracer_data.characters_byte_data = bytearray([])
        for char in self.tracer_data.character_list:
            self.tracer_data.nodes_byte_data.extend(char.serialise())

    def clear_scene_data(self, level: int):
        if level > 0:
            self.tracer_data.scene_objects.clear()  #list of all objects
            self.tracer_data.mesh_list.clear()      #list of geometry data
            self.tracer_data.material_list.clear()  # list of materials
            self.tracer_data.texture_list.clear()   #list of textures

        if level > 1:
            self.tracer_data.editable_objects.clear()
            self.tracer_data.header_byte_data.clear()       # header data as bytes
            self.tracer_data.nodes_byte_data.clear()        # nodes data as bytes
            self.tracer_data.mesh_byte_data.clear()         # geo data as bytes
            self.tracer_data.textures_byte_data.clear()     # texture data as bytes
            self.tracer_data.materials_byte_data.clear()    # materials data as bytes
            self.tracer_data.ping_byte_msg.clear()          # ping msg as bytes

    def check_for_updates(self):
        for obj in self.tracer_data.editable_objects:
            obj.check_for_updates()