'''
TRACER Scene Distribution Plugin Blender
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Blender is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Blender development.
 
The TRACER Scene Distribution Plugin Blender is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Blender is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Blender may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Blender Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Blender by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Blender in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
import bpy
import bmesh
import logging
import functools
import math
import mathutils
import struct

from .AbstractParameter import Parameter
from .SceneObject import SceneObject, NodeTypes
from SceneDataMesh import SceneDataMesh
from SceneDataMaterial import SceneDataMaterial
from SceneDataTexture import SceneDataTexture
from ..Core.ServerAdapter import send_parameter_update;

class SceneObjectMesh(SceneObject):

   mesh_geometry_id: int
   material_id: int
   color: list[float]
   roughness: float
   specular: float

   def __init__(self, obj: bpy.types.Object):
      super().__init__(obj)

      # Public Variables (not TRACER Parameters)
      self.logger = logging.getLogger("TRACER_LOGGER.SCENE_OBJECT_MESH")
      self.tracer_type = NodeTypes.GEO

      # Precess mesh and material only if this SceneObjectMesh is NOT supposed to be a SceneObjectSkinnedMesh
      #if obj.parent.type != 'ARMATURE':
      self.mesh_geometry_id   = self.process_geometry_mesh()
      self.material_id        = SceneDataMaterial.process_material(self)

      if self.material_id > -1:
         self.color        = self.tracer_data.material_list[self.material_id].color
         self.roughness    = self.tracer_data.material_list[self.material_id].roughness
         self.specular     = self.tracer_data.material_list[self.material_id].specular
      else:
         self.color        = obj.color
         self.roughness    = 0.5
         self.specular     = 0

      if self.is_editable:
         # Private Variables, providing access to the value of the parameters without looking into the Parameter List
         self._color_param = Parameter(self.color, "Color", self)
         self.parameter_list.append(self._color_param)
         self._roughness_param = Parameter(self.roughness, "Roughness", self)
         self.parameter_list.append(self._roughness_param)
         self._material_id_param = Parameter(self.material_id, "Material ID", self)
         self.parameter_list.append(self._material_id_param)
         
         self._color_param.parameter_handler.append(functools.partial(self.update_color, self.color))
         self._roughness_param.parameter_handler.append(functools.partial(self.update_roughness, self.roughness))
         self._material_id_param.parameter_handler.append(functools.partial(self.update_material_id, self.material_id))

   
   def update_color(self, parameter, new_value):
      if self.network_lock == True:
         self.blender_object.color = new_value
      else:
         send_parameter_update(parameter)
   
   def update_roughness(self, parameter, new_value):
      if self.network_lock == True:
         self.blender_object.active_material.roughness = new_value
      else:
         send_parameter_update(parameter)
   
   def update_material_id(self, parameter, new_value):
      if self.network_lock == True:
         # TODO: Investigate also active_material_index
         self.blender_object.active_material = bpy.context.window_manager.tracer_data.material_list[new_value]
      else:
         send_parameter_update(parameter)

   def serialise(self):
      pass
   
   def process_geometry_mesh(self) -> int:
      geo_mesh_name = self.generate_mesh_identifier()
      geo_mesh_data = SceneDataMesh()

      # Check if mesh has already being processed (and therefore is in the dictionary)
      pos_idx = 0
      for geo in self.tracer_data.geometry_list:
         if geo_mesh_name == geo.name:
            return pos_idx
         else:
            pos_idx =+ 1
      
      # Othrewise, process it and add it to the dictionary 

      # Ensuring that this mesh is NOT a Bone of an armature
      if self.blender_object.parent and self.blender_object.parent.type == 'ARMATURE':
         self.logger.error("Mesh %s cannot be processed correctly because part of the %s Armature", *[self.blender_object.data.name, self.blender_object.parent.name], exc_info=1)
         return -1
      
      # flipping faces because the following axis swap inverts them
      mesh: bmesh.types.BMesh = bmesh.from_edit_mesh(self.blender_object.data)
      for face in mesh.faces:
         bmesh.utils.face_flip(face)
      mesh.normal_update()

      mesh.verts.ensure_lookup_table()
      uv_layer = mesh.loops.layers.uv.active
      loop_triangles: list[tuple[bmesh.types.BMLoop, bmesh.types.BMLoop, bmesh.types.BMLoop]] = mesh.calc_loop_triangles()

      processed_vertices = []
      for triangle in loop_triangles:
         for bm_loop in triangle:
            og_idx = bm_loop.vert.index
            co = bm_loop.vert.co.copy().freeze()
            uv = bm_loop[uv_layer].uv.copy().freeze()

            if self.blender_object.data.polygons[0].use_smooth:
               normal = bm_loop.vert.normal.copy().freeze() if bm_loop.edge.smooth else bm_loop.face.normal.copy().freeze()
            else:
               normal = bm_loop.face.normal.copy().freeze()

            new_split_vert = (co, uv, normal)
            if new_split_vert not in processed_vertices:
               processed_vertices.append(new_split_vert)
               
               geo_mesh_data.original_indices.append(og_idx)
               geo_mesh_data.indices.append(len(processed_vertices) - 1)
               geo_mesh_data.vertices.append(co)
               geo_mesh_data.normals.append(normal)
               geo_mesh_data.uvs.append(uv)

      mesh.free()
      self.tracer_data.geometry_list.append(geo_mesh_data)
      return len(self.tracer_data.geometry_list)-1

   def generate_mesh_identifier(self) -> str:
      if self.blender_object.type == 'MESH':
         return f"Mesh_{self.blender_object.data.name}_{len(self.blender_object.data.vertices)}"
      elif self.blender_object.type == 'ARMATURE':
         return f"Armature_{self.blender_object.data.name}_{len(self.blender_object.data.bones)}"
      else:
         return f"{self.blender_object.type}_{self.blender_object.name}"
      
   def process_material(self) -> int:
      # If a the mesh has no material return -1 (empty index)
      if self.blender_object.active_material == None:
         return -1
      else:
         # If the material has already been processed, return its index
         material_idx = SceneObject.find_name_in_list(self.blender_object.active_material.name, self.tracer_data.material_list)
         if material_idx > -1:
             return material_idx
         
         # Otherwise, process and append it to the list of materials
         material_data = SceneDataMaterial()
         for i, n in enumerate(self.blender_object.active_material.name.encode()):
            material_data.name[i] = n
         for i, n in enumerate(("Standard").encode()):
            material_data.src[i] = n
         
         material_data.color     = self.blender_object.active_material.diffuse_color
         material_data.roughness = self.blender_object.active_material.roughness
         material_data.specular  = self.blender_object.active_material.specular_intensity
         
         if self.blender_object.active_material.use_nodes and\
            self.blender_object.active_material.node_tree.bl_rna_get_subclass_py() == bpy.types.ShaderNodeTree:
            # Looking for the Output Shader Material in a Shader Graph
            shader_tree: bpy.types.ShaderNodeTree = self.blender_object.active_material.node_tree        # get the Shader Node Tree 
            shader_out_node: bpy.types.ShaderNode = shader_tree.get_output_node()                        # get its Output Node
            shader_node: bpy.types.ShaderNode = shader_out_node.inputs[0].links[0].from_node             # get the first Node connected to its first input (Shader) - assuming it is a ShaderNode
            
            if shader_node != None:
               material_data.color = shader_node.inputs[0].default_value
               if shader_node.bl_rna_get_subclass_py() == bpy.types.ShaderNodeBsdfPrincipled:
                  material_data.roughness = shader_node.inputs[7].default_value
                  material_data.specular  = shader_node.inputs[5].default_value
               
               texture_node = None
               if len(shader_node.inputs[0].links) > 0:
                  node: bpy.types.ShaderNode = shader_node.inputs[0].links[0].from_node
               if node and node.bl_rna_get_subclass_py() == bpy.types.ShaderNodeTexImage:
                  texture_node: bpy.types.ShaderNodeTexImage = node
               if texture_node.image != None:
                  material_data.texture_id = self.process_texture(texture_node.image)
      
      self.tracer_data.material_list.append(material_data)
      return len(self.tracer_data.material_list)-1
      
   def process_texture(self, img: bpy.types.Image) -> int:
      # If the texture has already been processed return its index
      texture_idx =  SceneObject.find_name_in_list(img.name, self.tracer_data.texture_list)
      if texture_idx > -1:
         return texture_idx
        
      try:
         texture_file = open(img.filepath_from_user(), 'rb')
      except FileNotFoundError:
         bpy.context.window.modal_operators[-1].report({'ERROR'}, f"Error: Texture file not found at {img.filepath_from_user()}")
         return -1
        
      # Otherwise, process and append it to the list of textures
      texture_data = SceneDataTexture()

      texture_data.color_map_data = texture_file.read()
      texture_data.color_map_data_size = len(texture_data.color_map_data)
      texture_data.width = img.size[0]
      texture_data.height = img.size[1]
      texture_data.name = img.name_full

      texture_file.close()

      self.tracer_data.texture_list.append(texture_data)
      return len(self.tracer_data.texture_list) - 1