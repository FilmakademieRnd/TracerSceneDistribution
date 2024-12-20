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
from dataclasses import dataclass

from ..AbstractParameter import Parameter
from .SceneObject import SceneObject, NodeTypes
from ..serverAdapter import send_parameter_update;

@dataclass
class SceneMeshData():
   #vertex_list_size: int
   #index_list_size: int
   #normal_list_size: int
   #uv_list_size: int
   #bone_weight_list_size: int

   vertices: list[mathutils.Vector] = []
   normals: list[mathutils.Vector] = []
   uvs: list [mathutils.Vector] = []
   indices: list[int] = []
   bone_weights: list[mathutils.Vector] = []
   bone_indices: list[mathutils.Vector] = []

class SceneObjectMesh(SceneObject):
   def __init__(self, obj):
      super().__init__(obj)

      self.logger = logging.getLogger("TRACER_LOGGER.SCENE_OBJECT_MESH")
      self.tracer_type = NodeTypes.GEO
      self._mesh_geometry_id = self.process_geometry_mesh()

      if self.blender_object.get("TRACER-Editable", False):

         # Private Variables, providing access to the value of the parameters without looking into the Parameter List
         self._color_param = Parameter(obj.color, "Color", self)
         self.parameter_list.append(self._color_param)
         self._roughness_param = Parameter(0.5, "Roughness", self)
         self.parameter_list.append(self._roughness_param)
         self._material_id_param = Parameter(-1, "Material ID", self)
         self.parameter_list.append(self._material_id_param)
         
         self._color_param.parameter_handler.append(functools.partial(self.update_color, self._color_param))
         self._roughness_param.parameter_handler.append(functools.partial(self.update_roughness, self._roughness_param))
         self._material_id_param.parameter_handler.append(functools.partial(self.update_material_id, self._material_id_param))

         # Public Variables (not TRACER Parameters)
   
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
      camera_byte_array = super().serialise()

      camera_data : bpy.types.Camera = self.blender_object.data
      # Field-Of-View
      camera_byte_array.extend(struct.pack('f', math.degrees(camera_data.angle)))
      # Aspect Ratio
      camera_byte_array.extend(struct.pack('f', camera_data.sensor_width/camera_data.sensor_height))
      # Near Plane
      camera_byte_array.extend(struct.pack('f', camera_data.clip_start))
      # Far Plane
      camera_byte_array.extend(struct.pack('f', camera_data.clip_end))
      # Focal Distance (fixed to 5)
      camera_byte_array.extend(struct.pack('f', 5))
      # Aperture (fixed to 2)
      camera_byte_array.extend(struct.pack('f', 2))
      
      return camera_byte_array
   
   def process_geometry_mesh(self) -> int:
      geo_mesh_name = self.generate_mesh_identifier()
      geo_mesh_data = SceneMeshData()

      # Check if mesh has already being processed (and therefore is in the dictionary)
      pos_idx = 0
      for name in self.tracer_data.geometry_dict.keys():
         if geo_mesh_name == name:
            return pos_idx, geo_mesh_name
         else:
            pos_idx =+ 1
      
      # Othrewise, process it and add it to the dictionary 

      # Ensuring that this mesh is NOT a Bone of an armature
      if self.blender_object.parent and self.blender_object.parent.type == 'ARMATURE':
         self.logger.error("Mesh %s cannot be processed correctly because part of the %s Armature", *[self.blender_object.data.name, self.blender_object.parent.name], exc_info=1)
         return -1, ""
      
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
            original_index = bm_loop.vert.index
            co = bm_loop.vert.co.copy().freeze()
            uv = bm_loop[uv_layer].uv.copy().freeze()

            if self.blender_object.data.polygons[0].use_smooth:
               normal = bm_loop.vert.normal.copy().freeze() if bm_loop.edge.smooth else bm_loop.face.normal.copy().freeze()
            else:
               normal = bm_loop.face.normal.copy().freeze()

            new_split_vert = (co, uv, normal)
            if new_split_vert not in processed_vertices:
               processed_vertices.append(new_split_vert)
               
               geo_mesh_data.indices.append(len(processed_vertices) - 1)
               geo_mesh_data.vertices.append(co)
               geo_mesh_data.normals.append(normal)
               geo_mesh_data.uvs.append(uv)

      mesh.free()
      self.tracer_data.geometry_dict[geo_mesh_name] = geo_mesh_data
      return len(self.tracer_data.geometry_dict)-1, geo_mesh_name

   def generate_mesh_identifier(self) -> str:
    if self.blender_object.type == 'MESH':
        return f"Mesh_{self.blender_object.data.name}_{len(self.blender_object.data.vertices)}"
    elif self.blender_object.type == 'ARMATURE':
        return f"Armature_{self.blender_object.data.name}_{len(self.blender_object.data.bones)}"
    else:
        return f"{self.blender_object.type}_{self.blender_object.name}"