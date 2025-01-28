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
from .AbstractParameter import Parameter
from .SceneObject import SceneObject, NodeTypes
from ..Core.ServerAdapter import send_parameter_update;


class SceneObjectCamera(SceneObject):
   def __init__(self, obj: bpy.types.Object):
      super().__init__(obj)
      self.tracer_type = NodeTypes.CAMERA
      self.camera_data: bpy.types.Camera = self.blender_object.data

      if self.blender_object.get("TRACER-Editable", False):
         fov = Parameter(obj.data.angle, "Fov", self)
         self.parameter_list.append(fov)
         aspect = Parameter(obj.data.sensor_width/obj.data.sensor_height, "Aspect", self)
         self.parameter_list.append(aspect)
         near = Parameter(obj.data.clip_start, "Near", self)
         self.parameter_list.append(near)
         far = Parameter(obj.data.clip_end, "Far", self)
         self.parameter_list.append(far)
         
         fov.parameter_handler.append(functools.partial(self.update_fov, fov))
         near.parameter_handler.append(functools.partial(self.update_near, near))
         far.parameter_handler.append(functools.partial(self.update_far, far))

   def check_for_updates(self):
      super().check_for_updates()
      if abs(self.parameter_list[3].value - self.camera_data.angle):
         self.update_fov(self.camera_data.angle)
      if abs(self.parameter_list[4].value - self.camera_data.clip_start):
         self.update_near(self.camera_data.clip_start)
      if abs(self.parameter_list[5].value - self.camera_data.clip_end):
         self.update_far(self.camera_data.clip_end)
   
   def update_fov(self, new_value: float):
      if self.network_lock == True:
         self.camera_data.angle = new_value
      else:
         send_parameter_update(self.parameter_list[3])
   
   def update_near(self, new_value: float):
      if self.network_lock == True:
         self.camera_data.clip_start = new_value
      else:
         send_parameter_update(self.parameter_list[4])
   
   def update_far(self, new_value: float):
      if self.network_lock == True:
         self.camera_data.clip_end = new_value
      else:
         send_parameter_update(self.parameter_list[4])

   def serialise(self):
      camera_byte_array = super().serialise()

      # Field-Of-View
      camera_byte_array.extend(struct.pack('f', math.degrees(self.camera_data.angle)))
      # Aspect Ratio
      camera_byte_array.extend(struct.pack('f', self.camera_data.sensor_width/self.camera_data.sensor_height))
      # Near Plane
      camera_byte_array.extend(struct.pack('f', self.camera_data.clip_start))
      # Far Plane
      camera_byte_array.extend(struct.pack('f', self.camera_data.clip_end))
      # Focal Distance (fixed to 5)
      camera_byte_array.extend(struct.pack('f', 5))
      # Aperture (fixed to 2)
      camera_byte_array.extend(struct.pack('f', 2))
      
      return camera_byte_array