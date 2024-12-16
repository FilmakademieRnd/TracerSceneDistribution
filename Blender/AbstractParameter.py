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

import struct
import bpy
from mathutils import Vector, Quaternion, Color
from enum import Enum
import math

class TRACERParamType(Enum):
    NONE        = 0
    ACTION      = 1
    BOOL        = 2
    INT         = 3
    FLOAT       = 4
    VECTOR2     = 5
    VECTOR3     = 6
    VECTOR4     = 7
    QUATERNION  = 8
    COLOR       = 9
    STRING      = 10 
    LIST        = 11
    UNKNOWN     = 100

class KeyType(Enum):
    STEP    = 1
    LINEAR  = 2
    BEZIER  = 3

class AnimHostRPC(Enum):
    STOP        = 0
    STREAM      = 1
    STREAM_LOOP = 2
    BLOCK       = 3

## Abstract Class AbstractParameter (necessary to declare copy method in the AbstractParameter class)
class AbstractParameter:
    pass

class Key:
    ## Class attributes ##
    # frame timestamp of the current key
    time:   float

    right_tangent_time : float
    left_tangent_time : float
    # value of the keyframe - type of the value depends on the parameter that is being keyed
    value:          bool | int | float | Vector | Quaternion | Color | str | list #? type Action?
    right_tangent_value:  bool | int | float | Vector | Quaternion | Color | str | list #? type Action?
    left_tangent_value:  bool | int | float | Vector | Quaternion | Color | str | list #? type Action?
    # type of keyframe - KeyType (STEP, LINEAR, BEZIER)
    key_type:   KeyType

    def __init__(self, time, value, type = KeyType.LINEAR, right_tangent_time = None, right_tangent_value = None, left_tangent_time = None, left_tangent_value = None):
        self.time = time
        self.key_type = type
        self.right_tangent_time = right_tangent_time if right_tangent_time != None else time
        self.left_tangent_time = left_tangent_time if left_tangent_time != None else time

        self.value = value
        self.right_tangent_value = right_tangent_value if right_tangent_value != None else value
        self.left_tangent_value = left_tangent_value if left_tangent_value != None else value

    def __sizeof__(self) -> int:
        return self.get_key_size()

    def get_data_size(self):
        if isinstance(self.value, bool):
            return struct.calcsize('?') # = 1
        elif isinstance(self.value, int) or isinstance(self.value, float):
            return struct.calcsize('i') # = 4
        elif isinstance(self.value, Vector) and len(self.value) == 2:
            return struct.calcsize('f') * 2 # = 8
        elif isinstance(self.value, Vector) and len(self.value) == 3:
            return struct.calcsize('f') * 3 # = 12
        elif isinstance(self.value, Vector) and len(self.value) == 4 or isinstance(self.value, Quaternion) or isinstance(self.value, Color):
            return struct.calcsize('f') * 4 # = 16
        elif isinstance(self.value, str):
            return struct.calcsize('c') * len(self.value) # len_of_string * size_of_char

    def get_key_size(self):
        # byte (key_type) +           float (time) +           float (tangent_time) +   size_of_param (value) +    size_of_param (tangentvalue)
        return          1 + self.time.__sizeof__() + self.right_tangent_time.__sizeof__() + self.value.__sizeof__() + self.right_tangent_value.__sizeof__() # TODO: Add left tangent
    
    def is_equal(self, other):
        return (self.key_type               == other.key_type               and\
                self.time                   == other.time                   and\
                self.value                  == other.value                  and\
                self.right_tangent_time     == other.right_tangent_time     and\
                self.left_tangent_time      == other.left_tangent_time      and\
                self.right_tangent_value    == other.right_tangent_value    and\
                self.left_tangent_value     == other.left_tangent_value     )
    
class KeyList:
    __data: list[Key]
    has_changed: bool

    def __init__(self) -> None:
        self.__data = []
        self.has_changed = False

    def __len__(self) -> int:
        return len(self.__data)

    def clear(self) -> None:
        self.__data.clear()

    def size(self) -> int:
        return len(self.__data)
    
    def get_key(self, index: int) -> Key:
        if index < len(self):
            return self.__data[index]
        else:
            raise LookupError("Key not found in Parameter Key List")
    
    def set_key(self, key: Key, index: int):
        if index > self.size():
            raise IndexError("Setting Key Out Of Bounds for KeyList")
        elif index == self.size() or index == -1:
            self.__data.append(key)
            self.has_changed = True
        else:
            if not key.is_equal(self.__data[index]):
                self.__data[index] = key
                self.has_changed = True

    def add_key(self, key: Key):
        self.__data.append(key)
        self.has_changed = True

    def remove_key(self, key: Key) -> Key:
        flagged_index = -1
        for k, i in enumerate(self.__data):
            # Look for the key to be removed based on its timestamp
            # Stop updating the index at the first found instance 
            if k.time == key.time and flagged_index < 0:
                flagged_index = i

        if flagged_index > 0:
            return self.remove_key_at_index(flagged_index)
        else:
            raise LookupError("Key not found in Parameter Key List")
                
    def remove_key_at_index(self, index: int) -> Key:
        if index < len(self):
            removed_key = self.__data[index]
            self.__data.remove(index)
            self.has_changed = True
            return removed_key
        else:
            raise LookupError("Key not found in Parameter Key List")
    
    def get_list(self) -> list[Key]:
        return self.__data

class AbstractParameter:

    # PUBLIC STATIC variables
    start_animhost_rpc_id = 0

    def __init__ (self, value, name: str, parent_object = None, distribute = True, is_RPC = False, is_animated = False):
        # Non-static class variables
        
        # Parameter value - type of the value depends on the parameter that is being keyed
        self.value: bool | int | float | Vector | Quaternion | Color | str | list = value   #? type Action?
        # Type of the Parameter according to Tracer' definition (private)
        self.__type: TRACERParamType = self.get_tracer_type()
        # Paramter ID (private)
        self.__id: int = -1
        if parent_object:
            self.__id = len(parent_object.parameter_list)
        elif is_RPC and parent_object == None:
            self.__id = AbstractParameter.start_animhost_rpc_id
            AbstractParameter.start_animhost_rpc_id += 1
            print("Creating new RPC Parameter with name " + name + " and id " + str(self.__id))
        else:
            self.__id = 0
        # Parameter name
        self.name: str = name
        # Parametrized TRACER Object (type SceneObject, not importable due to circular import)
        self.parent_object = parent_object # see SceneObject.py
        # Flag that determines whether a Parameter is going to be distributed
        self.distribute: bool = distribute
        # Flag that determines whether a Parameter is a RPC Parameter (private)
        self.__is_RPC: bool = is_RPC
        # Flag that determines whether a Parameter is animated
        self.is_animated: bool = is_animated
        # The value of the parameter before it gets modified
        self.initial_value: bool | int | float | Vector | Quaternion | Color | str | list = value
        # Flag that determines whether a Parameter has been recently changed
        self.has_changed: bool = False
        # List of handlers that broadcast parameters updates when a parameter is changed
        self.parameter_handler: list[function] = []

    def get_object_id(self):
        return self.parent_object.object_id

    def get_parameter_id(self):
        return self.__id

    def get_tracer_type(self):
        if isinstance(self.value, bool):
            return TRACERParamType.BOOL.value
        elif isinstance(self.value, int):
            return TRACERParamType.INT.value
        elif isinstance(self.value, float):
            return TRACERParamType.FLOAT.value
        elif isinstance(self.value, Vector) and len(self.value) == 2:
            return TRACERParamType.VECTOR2.value
        elif isinstance(self.value, Vector) and len(self.value) == 3:
            return TRACERParamType.VECTOR3.value
        elif isinstance(self.value, Vector) and len(self.value) == 4:
            return TRACERParamType.VECTOR4.value
        elif isinstance(self.value, Quaternion):
            return TRACERParamType.QUATERNION.value
        elif isinstance(self.value, Color):
            return TRACERParamType.COLOR.value
        elif isinstance(self.value, str):
            return TRACERParamType.STRING.value
        else:
            return TRACERParamType.UNKNOWN.value
    
    def get_data_size(self) -> int:
        match self.__type:
            case TRACERParamType.BOOL.value:
                return struct.calcsize('?') # = 1
            case TRACERParamType.INT.value | TRACERParamType.FLOAT.value:
                return struct.calcsize('i') # = 4
            case TRACERParamType.VECTOR2.value:
                return struct.calcsize('f') * 2 # = 8
            case TRACERParamType.VECTOR3.value:
                return struct.calcsize('f') * 3 # = 12
            case TRACERParamType.VECTOR4.value | TRACERParamType.QUATERNION.value | TRACERParamType.COLOR.value:
                return struct.calcsize('f') * 4 # = 16
            case TRACERParamType.STRING:
                return struct.calcsize('c') * len(self._value) # len_of_string * size_of_char
        
    def python_type(self):
        return type(self._value)
    
    def set_RPC(self, is_RPC: bool):
        self.__is_RPC = is_RPC

    def is_RPC(self) -> None:
        return self.__is_RPC

    
class Parameter(AbstractParameter):

    ## Class Attributes ##
    key_list: KeyList

    def __init__(self, value, name, parent_object = None, distribute = True, is_RPC = False, is_animated = False):
        super().__init__(value, name, parent_object, distribute, is_RPC, is_animated)
        self.key_list = KeyList()

    # resets value to initial value, why do we want to do that?
    def reset(self):
        pass

    def init_animation(self):
        self.is_animated = True
        key_zero = Key(0, self.value)
        self.key_list.set_key(key_zero, 0)

    def clear_animation(self):
        self.is_animated = False
        self.key_list.clear()
        self.parent_object.armature_obj_pose_bones[self.parent_object.name].animation_data_clear()

    def get_key_list(self) -> list[Key]:
        return self.key_list.get_list()

    def get_key(self, index: int) -> Key:
        return self.key_list.get_key(index)

    def get_size(self) -> int:
        data_size = self.get_data_size()
        if self.is_animated:
            # When animated, the size of the parameter increases. After the first payload, there will be the number of keys that the animated parameter will have and then the list of those keys. 
            #         size_of_param +  size_of_short (nr_keys) +             nr_keys *                      size_of_key (= 2* size_of_param (value + tangent_value) + 2 * size_of_float (time + tangent_time) + byte (key_type))
            return        data_size +                        2 + len(self.key_list) * self.get_key(0).get_key_size()
        else:
            return data_size

    def set_value(self, new_value):
        if not self.parent_object.network_lock:
            self.parent_object.network_lock = True
            if new_value != self.value:
                self.has_changed = True
                self.value = new_value.copy()
                self.emit_has_changed()
            self.parent_object.network_lock = False
    
    def emit_has_changed(self):
        for handler in self.parameter_handler:
            handler(self.value)
        self.has_changed = False

    def copy_value(self, other): # other: Parameter (returns Parameter)
        if not self.parent_object.network_lock:
            self.parent_object.network_lock = True
            self.has_changed = False
            if self.value != other.value:
                self.value = other.value
                self.has_changed = True
            if self.is_animated != other.is_animated:
                self.is_animated = other.is_animated
                if self.is_animated:
                    self.init_animation()
                    self.key_list = other.key_list
                else:
                    self.clear_animation()
                self.has_changed = True

            if self.has_changed:
                self.emit_has_changed()
            self.parent_object.network_lock = False

    #######################
    ###  Serialization  ###
    #######################

    def serialize(self) -> bytearray:
        payload = bytearray([])
        payload.extend(self.serialize_data(self.value))
        if self.is_animated:
            payload.extend(struct.pack('<H', len(self.key_list)))
            for key in self.key_list.get_list():
                key_payload = bytearray([])
                key_payload.extend(struct.pack(' B', key.key_type.value))   #  'B' represents the format of an unsigned char (1 byte) encoded as little endian
                key_payload.extend(struct.pack('<f', key.time))             # '<f' represents the format of a signed float (4 bytes) encoded as little endian
                key_payload.extend(struct.pack('<f', key.left_tangent_time))
                key_payload.extend(struct.pack('<f', key.right_tangent_time))
                key_payload.extend(self.serialize_data(key.value))
                key_payload.extend(self.serialize_data(key.left_tangent_value))
                key_payload.extend(self.serialize_data(key.right_tangent_value))
                payload.extend(key_payload)
        return payload

    def serialize_data(self, value = None) -> bytearray:
        # If the attribute value is not initialised, the internal self.value instance attribute is going to be serialised
        #? Vectors are swizzled (Y-Z swap) in order to comply with the different handidness between blender and unity
        #? Quanternion rotation is taken from the object's rotation and swizzled (from XYZW to WXYZ)
        if value == None:
            match self.get_tracer_type():
                case TRACERParamType.VECTOR3.value:
                    value = self.value
                case TRACERParamType.VECTOR4.value:
                    value = self.value
                case TRACERParamType.QUATERNION.value:
                    self.parent_object.blender_object.rotation_mode = 'QUATERNION'
                    quat: Quaternion = self.value
                    value = Quaternion((quat.w, quat.x, quat.y, quat.z))
                    self.parent_object.blender_object.rotation_mode = 'XYZ'
                case _:
                    value = self.value

        match self.get_tracer_type():
            case TRACERParamType.BOOL.value:
                return struct.pack('?', value)
            case TRACERParamType.INT.value:
                return struct.pack('<i', value)
            case TRACERParamType.FLOAT.value:
                return struct.pack('<f', value)
            case TRACERParamType.VECTOR2.value:
                return struct.pack('<2f', value.x, value.y)
            case TRACERParamType.VECTOR3.value:
                unity_vec3 = value.xzy
                return struct.pack('<3f', value.x, value.y, value.z)
            case TRACERParamType.VECTOR4.value:
                unity_vec4 = value.xzyw
                return struct.pack('<4f', value.x, value.y, value.z, value.w)
            case TRACERParamType.QUATERNION.value:
                return struct.pack('<4f', value.x, value.y, value.z, value.w)
            case TRACERParamType.COLOR.value:
                #! Color in mathutils is only RGB
                return struct.pack('<4f', value.r, value.b, value.g, 1)
            case TRACERParamType.STRING.value:
                string_length = str(len(value))
                format_string = string_length + "s"
                return struct.pack(format_string, value)
        
    #######################
    ##  Deserialization  ##
    #######################

    def deserialize(self, msg_payload: bytearray) -> None:
        data_size = self.get_data_size()
        msg_size  = len(msg_payload)
        value_bytes = msg_payload[0:data_size]
        self.set_value(self.deserialize_data(value_bytes))

        if self.is_animated:
            # Reset has_changed flag before deserializing the keyframes
            self.key_list.has_changed = False

        if self.is_animated and msg_size > data_size:
            self.key_list.clear()

            byte_count = data_size
            msg_n_keys = msg_payload[byte_count:byte_count+2]
            n_keys = struct.unpack('<H', msg_n_keys)[0]
            byte_count += 2
            key_count = 0
            while key_count < n_keys:
                # Read Key Type
                key_type = struct.unpack('B', msg_payload[byte_count:byte_count+1])[0]
                byte_count += 1
                # Read Key Timestamp
                time = struct.unpack('<f', msg_payload[byte_count:byte_count+4])[0]
                byte_count += 4
                # Read Key Tangent Times
                right_tangent_time = struct.unpack('<f', msg_payload[byte_count:byte_count+4])[0]
                byte_count += 4
                left_tangent_time = struct.unpack('<f', msg_payload[byte_count:byte_count+4])[0]
                byte_count += 4
                # Read Key Value
                value = self.deserialize_data(msg_payload[byte_count:byte_count+data_size])
                byte_count += data_size
                # Read Key Tangent Values
                right_tangent_value = self.deserialize_data(msg_payload[byte_count:byte_count+data_size])
                byte_count += data_size
                left_tangent_value = self.deserialize_data(msg_payload[byte_count:byte_count+data_size])
                byte_count += data_size
                
                deserialized_key = Key(time = time, value = value, type = key_type,
                                       right_tangent_time = right_tangent_time, right_tangent_value = right_tangent_value,
                                       left_tangent_time  = left_tangent_time,  left_tangent_value  = left_tangent_value )
                self.key_list.set_key(deserialized_key, key_count)
                
                key_count += 1
            
            bpy.context.window.modal_operators[-1].report({'INFO'}, "New Animation Received!")
        
        # If the received Parameter Update changed something in the value(s) of the Parameter and the object 
        if self.has_changed and not self.parent_object.network_lock:
            self.parent_object.network_lock = True
            self.emit_has_changed()
            self.parent_object.network_lock = False

    def deserialize_data(self, msg_payload: bytearray):
        match self.get_tracer_type():
            case TRACERParamType.BOOL.value:
                bool_val = struct.unpack('?', msg_payload)[0]
                return bool_val

            case TRACERParamType.INT.value:
                #? Signed or unsigned Integer?
                int_val = struct.unpack('<i', msg_payload)[0]
                return int_val

            case TRACERParamType.FLOAT.value:
                float_val = struct.unpack('<f', msg_payload)[0]
                return float_val

            case TRACERParamType.VECTOR2.value:
                vec2_val = Vector((struct.unpack('<2f', msg_payload)))
                return vec2_val

            case TRACERParamType.VECTOR3.value:
                vec3_val = Vector((struct.unpack('<3f', msg_payload)))
                # Swap Y and Z axis to adapt to blender's handidness
                return vec3_val.xyz

            case TRACERParamType.VECTOR4.value:
                vec3_val = Vector((struct.unpack('<4f', msg_payload)))
                # Swap Y and Z axis to adapt to blender's handidness
                return vec3_val.wxyz

            case TRACERParamType.QUATERNION.value:
                # The quaternion is passed in the order XYZW
                quat_val = Quaternion((struct.unpack('<4f', msg_payload)))
                return Quaternion((quat_val[3], quat_val[0], quat_val[1], quat_val[2]))

            case TRACERParamType.COLOR.value:
                color_val = Color((struct.unpack('<4f', msg_payload)))
                return color_val

            case TRACERParamType.STRING.value:
                # https://docs.python.org/3/library/stdtypes.html#bytearray.decode
                string_val = msg_payload.decode(encoding='ascii', errors='strict')
                return string_val

            case _:
                print("Unknown type")
