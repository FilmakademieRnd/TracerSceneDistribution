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
from mathutils import Vector, Quaternion

from ..AbstractParameter import Parameter, Key, KeyList, KeyType
from ..serverAdapter import send_parameter_update

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
        # self.parameter_object_id = SceneObject.start_id
        # self.scene_object_id = tracer_data.objectsToTransfer.index(self.blender_object)
        self.object_id = SceneObject.start_id
        SceneObject.start_id += 1
        self.tracer_type: NodeTypes = NodeTypes.GROUP

        self.parameter_list: list[Parameter] = []
        self.network_lock: bool = False
        self.blender_object: Object = bl_obj

        # If the object is TRACER-Editable, initialise the Parameters 
        if self.blender_object.get("TRACER-Editable", False):
            # Populating with TRS (Translation-Rotation-Scale) the list of TRACER parameters of the Scene Object. They will be parameters 0, 1 and 2 in the list
            tracer_pos = Parameter(bl_obj.location.copy(), bl_obj.name+"-location", self)
            self.parameter_list.append(tracer_pos)
            tracer_rot = Parameter(bl_obj.rotation_quaternion.copy(), bl_obj.name+"-rotation_euler", self)
            self.parameter_list.append(tracer_rot)
            tracer_scl = Parameter(bl_obj.scale.copy(), bl_obj.name+"-scale", self)
            self.parameter_list.append(tracer_scl)

            # Bind functions to update parameters to the corresponding instance of the parameter using functools.partial
            tracer_pos.parameter_handler.append(functools.partial(self.update_position, tracer_pos))
            tracer_rot.parameter_handler.append(functools.partial(self.update_rotation, tracer_rot))
            tracer_scl.parameter_handler.append(functools.partial(self.update_scale,    tracer_scl))

        # If the Blender Object has the property Control Points, add the respective Animated Parameters for path locations and path rotations
        # These parameters are associated with the root object of the Control Path in the scene
        control_path = bl_obj.get("Control Points", None) 
        if control_path != None and len(control_path) > 0:
            first_point: Object = control_path[0]
            path_locations = Parameter(first_point.location, bl_obj.name+"-path_locations", self)
            path_locations.init_animation()
            self.parameter_list.append(path_locations)
            path_rotations = Parameter(first_point.rotation_quaternion, bl_obj.name+"-path_rotations", self)
            path_rotations.init_animation()
            self.parameter_list.append(path_rotations)

    #! This function is not being triggered when the value of the property changes (I've not been able to make it work)
    def is_control_path(self, context: bpy.types.Context) -> bool:
        return self.blender_object.get("Control Points", False)


    ### Function that updates the value of the position of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_pos  the instance of the parameter to update
    #   @param  new_value   the 3D vector describing the new position of this Scene Object  
    def update_position(self, tracer_pos: Parameter, new_value: Vector):
        # If the object is edited from another TRACER client (network_lock is True), update the value,
        # Otherwise send a Parameter Update to all other connected clients to notify them of the local edits
        if self.network_lock:
            self.blender_object.location = new_value
        else:
            send_parameter_update(tracer_pos)
        # Update the initial_value to the latest value
        tracer_pos.initial_value = new_value

    ### Function that updates the value of the roatation of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_rot  the instance of the parameter to update
    #   @param  new_value   the quaternion describing the new rotation of this Scene Object
    def update_rotation(self, tracer_rot: Parameter, new_value: Quaternion):
        # If the object is edited from another TRACER client (network_lock is True), update the value,
        # Otherwise send a Parameter Update to all other connected clients to notify them of the local edits
        if self.network_lock:
            self.blender_object.rotation_mode = 'QUATERNION'
            self.blender_object.rotation_quaternion = new_value
            self.blender_object.rotation_mode = 'XYZ'

            if self.blender_object.type == 'LIGHT' or self.blender_object.type == 'CAMERA' or self.blender_object.type == 'ARMATURE':
                self.blender_object.rotation_euler.rotate_axis("X", math.radians(90))
        else:
            send_parameter_update(tracer_rot)
        # Update the initial_value to the latest value
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
            send_parameter_update(tracer_scl)
        # Update the initial_value to the latest value
        tracer_scl.initial_value = new_value

    ### Function that toggles the network_lock of Scene Objects
    #   @param  lock_val    value of the network_lock to be set
    def lock_unlock(self, lock_val: int):
        self.network_lock = bool(lock_val)
        self.blender_object.hide_select = bool(lock_val)

    ### It updates the TRACER parameters describing the Control Path using the data from the the Control Path and Control Points geometrical data
    def update_control_points(self):
        if self.blender_object.get("Control Points", None) != None:
            rotations = self.parameter_list[-1]
            locations = self.parameter_list[-2]

            cp_list: list[bpy.types.Object] = self.blender_object.get("Control Points")
            cp_curve: bpy.types.SplineBezierPoints = self.blender_object.children[0].data.splines[0].bezier_points
            for i, cp in enumerate(cp_list):
                locations.key_list.set_key(Key( time                = cp.get("Frame"),
                                                value               = cp_curve[i].co,
                                                type                = KeyType.BEZIER,
                                                right_tangent_time  = cp.get("Ease Out"),
                                                right_tangent_value = cp_curve[i].handle_right,
                                                left_tangent_time   = cp.get("Ease In"),
                                                left_tangent_value  = cp_curve[i].handle_left ),
                                            i)
                original_rot_mode = cp.rotation_mode
                if original_rot_mode != 'QUATERNION':
                    cp.rotation_mode = 'QUATERNION'

                rotations.key_list.set_key(Key( time                = cp.get("Frame"),
                                                value               = cp.rotation_quaternion,
                                                type                = KeyType.LINEAR ),
                                            i)
                
                cp.rotation_mode = original_rot_mode

            self.parameter_list[-2] = locations
            self.parameter_list[-1] = rotations

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

        # if self.blender_object.type == 'MESH':
        #    process_mesh(self.editabe_object, object_byte_array)

        return object_byte_array