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
from bpy.types import Object
import functools
import math
import struct
from enum import Enum
import copy
from mathutils import Vector, Quaternion,Matrix

from ..AbstractParameter import Parameter, Key, KeyList, KeyType
from ..settings import TracerData

class NodeTypes(Enum):
    GROUP       = 0
    GEO         = 1
    LIGHT       = 2
    CAMERA      = 3
    SKINNEDMESH = 4
    CHARACTER   = 5


### Class defining the properties and exposed functionalities of any object in a TRACER scene
#   
class SceneObject:

    # PUBLIC STATIC variables
    start_id: int = 1
    scene_ID: int = 254
    
    def __init__(self, bl_obj: Object):
        # PUBLIC NON-STATIC variables declaration
        self.tracer_data: TracerData = bpy.context.window_manager.tracer_data
        self.object_id = SceneObject.start_id
        SceneObject.start_id += 1
        self.tracer_type: NodeTypes = NodeTypes.GROUP

        self.parameter_list: list[Parameter] = []
        self.network_lock: bool = False
        self.blender_object: Object = bl_obj
        
        local_mat = bl_obj.matrix_local.copy()

        # If the object is TRACER-Editable, initialise the Parameters 
        if self.blender_object.get("TRACER-Editable", False):
            # Populating with TRS (Translation-Rotation-Scale) the list of TRACER parameters of the Scene Object. They will be parameters 0, 1 and 2 in the list

            tracer_pos = Parameter(local_mat.to_translation(), bl_obj.name+"-location", self)
            self.parameter_list.append(tracer_pos)
            tracer_rot = Parameter(local_mat.to_quaternion(), bl_obj.name+"-rotation_quaternion", self)
            self.parameter_list.append(tracer_rot)
            tracer_scl = Parameter(local_mat.to_scale(), bl_obj.name+"-scale", self)
            self.parameter_list.append(tracer_scl)

            # Bind functions to update parameters to the corresponding instance of the parameter using functools.partial
            tracer_pos.parameter_handler.append(functools.partial(self.update_position, tracer_pos))
            tracer_rot.parameter_handler.append(functools.partial(self.update_rotation, tracer_rot))
            tracer_scl.parameter_handler.append(functools.partial(self.update_scale,    tracer_scl))


    ### Function that updates the value of the position of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_pos  the instance of the parameter to update
    #   @param  new_value   the 3D vector describing the new position of this Scene Object  
    def update_position(self, tracer_pos: Parameter, new_value: Vector):
        # If the object is edited from another TRACER client (network_lock is True), update the value,
        # Otherwise send a Parameter Update to all other connected clients to notify them of the local edits
        if self.network_lock:
            (_, old_local_rot, old_local_scl) = self.blender_object.matrix_local.decompose()
            self.blender_object.matrix_local = Matrix.LocRotScale(new_value, old_local_rot, old_local_scl)
        else:
            # Instead of sending the parameter update, place the updated parameter into a list with other updated parameters 
            # send_parameter_update(tracer_pos)
            self.tracer_data.modified_parameters.append(tracer_pos)
        # Update the initial_value to the latest value
        bpy.context.view_layer.update()
        tracer_pos.initial_value = new_value

    ### Function that updates the value of the roatation of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_rot  the instance of the parameter to update
    #   @param  new_value   the quaternion describing the new rotation of this Scene Object
    def update_rotation(self, tracer_rot: Parameter, new_value: Quaternion):
        # If the object is edited from another TRACER client (network_lock is True), update the value,
        # Otherwise send a Parameter Update to all other connected clients to notify them of the local edits
        if self.network_lock:
            new_value = new_value.normalized()
            (old_local_pos, _, old_local_scl) = self.blender_object.matrix_local.decompose()
            self.blender_object.matrix_local = Matrix.LocRotScale(old_local_pos, new_value, old_local_scl)

            if self.blender_object.type == 'LIGHT' or self.blender_object.type == 'CAMERA': # or self.blender_object.type == 'ARMATURE':
                self.blender_object.rotation_euler.rotate_axis("Z", math.radians(180))
        else:
            #send_parameter_update(tracer_rot)
            self.tracer_data.modified_parameters.append(tracer_rot)
        # Update the initial_value to the latest value
        bpy.context.view_layer.update()
        tracer_rot.initial_value = new_value

    ### Function that updates the value of the scale of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_scl  the instance of the parameter to update
    #   @param  new_value   the 3D vector describing the new scale of this Scene Object
    def update_scale(self, tracer_scl: Parameter, new_value: Vector):
        # If the object is edited from another TRACER client (network_lock is True), update the value,
        # Otherwise send a Parameter Update to all other connected clients to notify them of the local edits
        if self.network_lock:
            self.blender_object.scale = new_value
        else:
            #send_parameter_update(tracer_scl)
            self.tracer_data.modified_parameters.append(tracer_scl)
        # Update the initial_value to the latest value
        tracer_scl.initial_value = new_value

    ### Writing the animation data received from TRACER -usually AnimHost- and replacing the previous animation data
    def populate_timeline_with_animation(self):
        # Clear the timeline from the old animation if there is one or initialise the data structure if there isn't one yet
        if self.blender_object.animation_data == None:
            self.blender_object.animation_data_create().action = bpy.data.actions.new("AnimHost Output")
        elif self.blender_object.animation_data.action:
            bpy.data.actions.remove(self.blender_object.animation_data.action)
            self.blender_object.animation_data.action = bpy.data.actions.new("AnimHost Output")

        # For every animated parameter that refers directly to the current object and doesn't describe a path
        for parameter in self.parameter_list:
            obj_name, param_type = parameter.name.split("-")
            if parameter.is_animated and obj_name == self.blender_object.name and "path" not in param_type:
                for key in parameter.get_key_list():
                    match param_type:
                        case 'location':
                            self.blender_object.location = key.value
                        case 'rotation_quaternion':
                            self.blender_object.rotation_mode = 'QUATERNION'
                            self.blender_object.rotation_quaternion = key.value
                        case 'scale':
                            self.blender_object.scale = key.value
                    self.blender_object.keyframe_insert(param_type, frame=key.time)

    ### Function that toggles the network_lock of Scene Objects
    #   @param  lock_val    value of the network_lock to be set
    def lock_unlock(self, lock_val: int):
        self.network_lock = bool(lock_val)
        self.blender_object.hide_select = bool(lock_val)

    def serialise(self) -> bytearray:
        object_byte_array = bytearray([])

        # Node Type
        object_byte_array.extend(struct.pack('i', self.tracer_type.value))
        # Is Editable
        object_byte_array.extend(struct.pack('i', int(self.blender_object.get("TRACER-Editable", False))))
        # Number of Children
        object_byte_array.extend(struct.pack('i', len(self.blender_object.children)))
        # Location
        object_byte_array.extend(struct.pack('3f', self.blender_object.location))
        # Scale
        object_byte_array.extend(struct.pack('3f', self.blender_object.scale))
        # Rotation
        object_byte_array.extend(struct.pack('4f', self.blender_object.rotation_quaternion))
        # Name (fixed length 64 bytes)
        fixed_length_name = bytearray(64)
        for i, n in enumerate(self.blender_object.name.encode()):
            fixed_length_name[i] = n
        object_byte_array.extend(struct.pack(fixed_length_name))

        return object_byte_array