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
import functools
import math
import struct
from ..AbstractParameter import Parameter
from .SceneObject import SceneObject, NodeTypes
from ..serverAdapter import send_parameter_update;


class SceneObjectMesh(SceneObject):
   def __init__(self, obj):
      super().__init__(obj)
      self.tracer_type = NodeTypes.GEO

      if self.blender_object.get("TRACER-Editable", False):
         color = Parameter(obj.color, "Color", self)
         self.parameter_list.append(color)
         roughness = Parameter(0.5, "Roughness", self)
         self.parameter_list.append(roughness)
         material_id = Parameter(-1, "Material ID", self)
         self.parameter_list.append(material_id)
         
         color.parameter_handler.append(functools.partial(self.update_color, color))
         roughness.parameter_handler.append(functools.partial(self.update_roughness, roughness))
         material_id.parameter_handler.append(functools.partial(self.update_material_id, material_id))
   
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
         self.blender_object.active_material = bpy.context.window_manager.tracer_data.materialList[new_value]
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