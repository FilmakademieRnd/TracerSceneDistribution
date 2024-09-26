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
from bpy.types import Object, SplineBezierPoints
import bpy
import functools
import math
from mathutils import Vector, Quaternion

from ..AbstractParameter import Parameter, Key, KeyList, KeyType
from ..serverAdapter import send_parameter_update

class SceneObject:

    s_id = 1
    _sceneID = 254
    _parameterList: list[Parameter]
    network_lock: bool
    editableObject: Object
    
    def __init__(self, bl_obj: Object):
        self._id = SceneObject.s_id
        SceneObject.s_id += 1
        self._sceneID = SceneObject._sceneID
        self._parameterList = []
        self.network_lock = False
        self.editableObject = bl_obj 
        tracer_pos = Parameter(bl_obj.location, bl_obj.name+"-location", self)
        self._parameterList.append(tracer_pos)
        tracer_rot = Parameter(bl_obj.rotation_quaternion, bl_obj.name+"-rotation_euler", self)
        self._parameterList.append(tracer_rot)
        tracer_scl = Parameter(bl_obj.scale, bl_obj.name+"-scale", self)
        self._parameterList.append(tracer_scl)
        # Bind UpdatePosition to the instance using functools.partial
        tracer_pos.parameter_handler.append(functools.partial(self.UpdatePosition, tracer_pos))
        tracer_rot.parameter_handler.append(functools.partial(self.UpdateRotation, tracer_rot))
        tracer_scl.parameter_handler.append(functools.partial(self.UpdateScale,    tracer_scl))

        # If the Blender Object has the property Control Points, add the respective Animated Parameters for path locations and path rotations
        # These parameters are associated with the root object of the Control Path in the scene
        control_path = bl_obj.get("Control Points", None) 
        if control_path != None and len(control_path) > 0:
            first_point: Object = control_path[0]
            path_locations = Parameter(first_point.location, bl_obj.name+"-path_locations", self)
            path_locations.init_animation()
            self._parameterList.append(path_locations)
            path_rotations = Parameter(first_point.rotation_quaternion, bl_obj.name+"-path_rotations", self)
            path_rotations.init_animation()
            self._parameterList.append(path_rotations)



    def UpdatePosition(self, tracer_pos: Parameter, new_value: Vector):
        if self.network_lock:
            self.editableObject.location = new_value
            if tracer_pos.key_list.has_changed:
                for key in tracer_pos.get_key_list():
                    self.editableObject.location = key.value
                    self.editableObject.keyframe_insert("location", key.time)
        else:
            send_parameter_update(tracer_pos)

    def UpdateRotation(self, tracer_rot: Parameter, new_value: Quaternion):
        if self.network_lock:
            self.editableObject.rotation_mode = 'QUATERNION'
            self.editableObject.rotation_quaternion = new_value
            self.editableObject.rotation_mode = 'XYZ'

            if self.editableObject.type == 'LIGHT' or self.editableObject.type == 'CAMERA' or self.editableObject.type == 'ARMATURE':
                self.editableObject.rotation_euler.rotate_axis("X", math.radians(90))
        else:
            send_parameter_update(tracer_rot)

    def UpdateScale(self, tracer_scl: Parameter, new_value: Vector):
        if self.network_lock:
            self.editableObject.scale = new_value
        else:
            send_parameter_update(tracer_scl)

    def LockUnlock(self, value: int):
        if value == 1:
            self.network_lock = True
            self.editableObject.hide_select = True
        else:
            self.network_lock = False
            self.editableObject.hide_select = False
        
    def update_parameter(self, param_id: int):
        parameter = self._parameterList[param_id]
        obj_name, param_type = parameter.name.split("-")

        if self.editableObject.get("Control Points", None) != None and param_type == "path_rotations":
            rotations = parameter
            locations = self._parameterList[param_id - 1]

            cp_list: list[Object] = self.editableObject.get("Control Points")
            cp_curve: SplineBezierPoints = self.editableObject.children[0].data.splines[0].bezier_points
            print(self.editableObject.name)
            for i, cp in enumerate(cp_list):
                print(cp.name)
                for i, cp in enumerate(cp_list):
                    locations.key_list.set_key(Key( time                = cp.get("Frame"),
                                                    value               = cp_curve[i].co,
                                                    type                = KeyType.BEZIER,
                                                    right_tangent_time  = cp.get("Ease Out"),
                                                    right_tangent_value = cp_curve[i].handle_right,
                                                    left_tangent_time   = cp.get("Ease In"),
                                                    left_tangent_value  = cp_curve[i].handle_left ),
                                                i)
                    
                    rotations.key_list.set_key(Key( time                = cp.get("Frame"),
                                                    value               = cp.rotation_quaternion,
                                                    type                = KeyType.LINEAR ),
                                                i)

                self._parameterList[param_id - 1]   = locations
                self._parameterList[param_id]       = rotations

        elif self.editableObject.get("Control Path", None) != None and param_type == "control_path":
            path_ID = -1
            for i, obj in enumerate(bpy.data.collections["TRACER_Collection"].objects):
                if obj == self.editableObject.get("Control Path"):
                    path_ID = i
                    break

            if path_ID >= 0:
                self._parameterList[-1] = Parameter(value=path_ID, name=self.editableObject.name+"-control_path", parent_object=self)
