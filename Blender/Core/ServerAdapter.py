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

import time 
import threading
import bpy
import struct
import mathutils
import math
from enum import Enum
from collections import deque
import numpy as np
from .timer import TimerModalOperator

from .SceneManager import SceneManager
from ..SceneObjects.SceneObject import SceneObject
from ..SceneObjects.AbstractParameter import AbstractParameter, Parameter
from ..settings import TracerData, TracerProperties

class MessageType(Enum):
    PARAMETERUPDATE = 0
    LOCK            = 1
    SYNC            = 2
    PING            = 3
    RESENDUPDATE    = 4
    UNDOREDOADD     = 5
    RESETOBJECT     = 6
    DATAHUB         = 7
    RPC             = 8

m_pingTimes = deque([0, 0, 0, 0, 0])
pingRTT = 0
## Setup ZMQ thread
def set_up_thread():
    try:
        import zmq
    except Exception as e:
        print('Could not import ZMQ\n' + str(e))
    global tracer_data, tracer_props
    tracer_data: TracerData = bpy.context.window_manager.tracer_data
    tracer_props: TracerProperties = bpy.context.scene.tracer_properties
    # Prepare ZMQ
    tracer_data.ctx = zmq.Context()

    # Prepare Subscriber
    tracer_data.socket_s = tracer_data.ctx.socket(zmq.SUB)
    tracer_data.socket_s.connect(f'tcp://{v_prop.server_ip}:{v_prop.sync_port}')
    tracer_data.socket_s.setsockopt_string(zmq.SUBSCRIBE, "")
    tracer_data.socket_s.setsockopt(zmq.RCVTIMEO,1)
    

    
    bpy.app.timers.register(listener)
    
    # Prepare Distributor
    tracer_data.socket_d = tracer_data.ctx.socket(zmq.REP)
    tracer_data.socket_d.bind(f'tcp://{v_prop.server_ip}:{v_prop.dist_port}')

    # Prepare poller
    tracer_data.poller = zmq.Poller()
    tracer_data.poller.register(tracer_data.socket_d, zmq.POLLIN)    

    bpy.app.timers.register(read_thread)
    
    if hasattr(bpy.types, 'WM_OT_timer_modal_operator'):
        print("Timer Modal Operator already registered")
    else:
        bpy.utils.register_class(TimerModalOperator)
    
    bpy.ops.wm.timer_modal_operator()

    tracer_data.socket_u = tracer_data.ctx.socket(zmq.PUB)
    tracer_data.socket_u.connect(f'tcp://{v_prop.server_ip}:{v_prop.update_sender_port}')

    #set_up_thread_socket_c()

    
def set_up_thread_socket_c():
    global tracer_data, tracer_props
    tracer_data = bpy.context.window_manager.tracer_data_data
    tracer_props = bpy.context.scene.tracer_properties

    tracer_data.socket_c.connect(f'tcp://{v_prop.server_ip}:{v_prop.Command_Module_port}')
   
    ping_thread = threading.Thread(target=ping_thread_function, daemon=True)
    ping_thread.start()
    print("Ping thread started")

## Read requests and send packages
def read_thread():
    global tracer_data, tracer_props
    tracer_data = bpy.context.window_manager.tracer_data
    tracer_props = bpy.context.scene.tracer_properties
    if tracer_data.socket_d:
        # Get sockets with messages (0: don't wait for msgs)
        sockets = dict(tracer_data.poller.poll(0))
        # Check if this socket has a message
        if tracer_data.socket_d in sockets:
            # Receive message
            msg = tracer_data.socket_d.recv_string()
            # Classify message
            if msg == "header":
                print("Header request! Sending...")
                tracer_data.socket_d.send(tracer_data.header_byte_data)
            elif msg == "nodes":
                print("Nodes request! Sending...")
                tracer_data.socket_d.send(tracer_data.nodes_byte_data)
            elif msg == "objects":
                print("Object request! Sending...")
                tracer_data.socket_d.send(tracer_data.mesh_byte_data)
            elif msg == "characters":
                print("Characters request! Sending...")
                if(len(tracer_data.character_list) > 0):
                    tracer_data.socket_d.send(tracer_data.characters_byte_data)
            elif msg == "textures":
                print("Texture request! Sending...")                
                if(len(tracer_data.texture_list) > 0):
                    tracer_data.socket_d.send(tracer_data.textures_byte_data)
            elif msg == "materials":
                print("Materials request! Sending...")
                if((tracer_data.material_list) > 0):
                    tracer_data.socket_d.send(tracer_data.materials_byte_data)
            #elif msg == "curve":
            #    print("curve request! Sending...")
            #    if(tracer_data.curvesByteData != None):
            #        tracer_data.socket_d.send(tracer_data.curvesByteData)
            else: # sent empty
                tracer_data.socket_d.send_string("")
    return 0.1 # repeat every .1 second

global last_sync_time
last_sync_time = None 

## process scene updates
def listener():
    global tracer_data, tracer_props, last_sync_time
    tracer_data = bpy.context.window_manager.tracer_data
    tracer_props = bpy.context.scene.tracer_properties
    msg = None
    
    try:
        msg = tracer_data.socket_s.recv()
    except Exception as e:
        msg = None


    ## Reading msg
    #   0   - clientID  - byte
    #   1   - time      - byte
    #   2   - msgType   - byte
    #   3+  - msgBody
    if msg != None:
        client_ID   = msg[0]
        msg_time    = msg[1]
        msg_type    = msg[2]
        
        if msg_type == MessageType.SYNC.value:
            process_sync_msg(msg)

        if client_ID != tracer_data.cID:
            start = 3

            while start < len(msg):
                if msg_type == MessageType.LOCK.value:
                    last_index = process_lock_msg(msg, start)
                    start = last_index
                elif msg_type == MessageType.PARAMETERUPDATE.value:
                    last_index = process_parameter_update(msg, start)
                    start = last_index
                elif msg_type == MessageType.RPC.value:
                    last_index = process_RPC_msg(msg, start)
                    start = last_index
                else:
                    start = len(msg)
    return 0.01 # repeat every .1 second
                
## Stopping the thread and closing the sockets

def create_ping_msg():
    tracer_data.ping_byte_msg = bytearray([])
    tracer_data.ping_byte_msg.extend(struct.pack('B', tracer_data.cID))
    tracer_data.ping_byte_msg.extend(struct.pack('B', tracer_data.time))
    tracer_data.ping_byte_msg.extend(struct.pack('B', 3))
    
def ping_thread_function():
    while True:
        ping()
        time.sleep(1)

def ping():
    global tracer_data, v_prop
    create_ping_msg()  # Ensure this updates tracer_data.ping_byte_msg appropriately
    if tracer_data.socket_c:
        try:
            tracer_data.socket_c.send(tracer_data.ping_byte_msg)
            tracer_data.pingStartTime = tracer_data.time
            msg = tracer_data.socket_c.recv()
            if msg and msg[0] != tracer_data.cID:
                decode_pong_msg(msg)
        except Exception as e:
            print(f"Failed to receive pong: {e}")
    
def decode_pong_msg(msg):
    rtt = delta_time(tracer_data.time, tracer_data.pingStartTime ,TimerModalOperator.my_instance.m_timesteps)
    pingCount = len(m_pingTimes)
    
    if(pingCount > 4):
        m_pingTimes.popleft()

    m_pingTimes.append(rtt)
    
    rtts = np.array(m_pingTimes)
    rttMax = rtts.max()
    rttSum = rtts.sum()

    if pingCount > 1:
        pingRTT = round((rttSum - rttMax) / (pingCount - 1))

def process_sync_msg(msg: bytearray, start=0):
    current_time = time.time()
    sv_time = msg[1]
    runtime = int(pingRTT * 0.5)
    syncTime = sv_time + runtime
    delta = delta_time(tracer_data.time, sv_time, TimerModalOperator.my_instance.m_timesteps)
    if delta > 10 or delta>3 and runtime < 8:
        tracer_data.time = int(round(sv_time)) % TimerModalOperator.my_instance.m_timesteps
    

def send_parameter_update(parameter: Parameter):
    tracer_data.parameter_update_msg = bytearray([])

    # Message Header
    tracer_data.parameter_update_msg.extend(struct.pack(' B', tracer_data.cID))                       # client ID
    tracer_data.parameter_update_msg.extend(struct.pack(' B', tracer_data.time))                      # sync time
    tracer_data.parameter_update_msg.extend(struct.pack(' B', MessageType.PARAMETERUPDATE.value))     # message type
    
    # Message Payload
    tracer_data.parameter_update_msg.extend(parameter.serialize())

    tracer_data.socket_u.send(tracer_data.parameter_update_msg)

def process_parameter_update(msg: bytearray, start=0) -> int:

    param: Parameter = None
    msg_size = len(msg) # for debugging
    updated_animation = False

    while start < len(msg):
        scene_id    = struct.unpack( 'B', msg[start   : start+1 ])[0]
        obj_id      = struct.unpack('<H', msg[start+1 : start+3 ])[0] # unpack object ID; 2 bytes (unsigned short); little endian
        param_id    = struct.unpack('<H', msg[start+3 : start+5 ])[0]
        param_type  = struct.unpack( 'B', msg[start+5 : start+6 ])[0]
        length      = struct.unpack('<I', msg[start+6 : start+10])[0] # unpack length of parameter data; 4 bytes (uint); little endian (includes the header bytes)

        msg_payload = msg[start+10 : start+length] # Extracting only the data for the current parameter from the message

        if 0 < obj_id <= len(tracer_data.scene_objects) and 0 <= param_id < len(tracer_data.scene_objects[obj_id - 1].parameter_list):
            param = tracer_data.scene_objects[obj_id - 1].parameter_list[param_id]
            # If receiveng an animated parameter udpate on a parameter that is not already animated
            # Note: 10 is the size of the header
            if not param.is_animated and param.get_size() < length-10:
                param.init_animation()

            param.deserialize(msg_payload)

            updated_animation = updated_animation or param.key_list.has_changed # If only one parameter animation is updated flag the animation to be updated later
                    
        start += length
    
    # At the end of the reading, if the message received was an Animation Parameter Update, trigger baking the animation over the (Character) Object
    if param != None and updated_animation:
        param.parent_object.populate_timeline_with_animation()

    return start


def send_RPC_msg(rpc_parameter: Parameter):
    #TODO: use new scene and object to hold AnimHost RPC Parameters (which will trigger RPC calls)
    scene_id    = 255   if rpc_parameter.parent_object == None else rpc_parameter.get_object_id()
    object_id   = 1     if rpc_parameter.parent_object == None else rpc_parameter.get_object_id()

    tracer_data.parameter_update_msg = bytearray([])
    tracer_data.parameter_update_msg.extend(struct.pack(' B', tracer_data.cID))                       # client ID
    tracer_data.parameter_update_msg.extend(struct.pack(' B', tracer_data.time))                      # sync time
    tracer_data.parameter_update_msg.extend(struct.pack(' B', MessageType.RPC.value))                 # message type
    tracer_data.parameter_update_msg.extend(struct.pack(' B', scene_id))                              # scene ID (not assigned to a specific scene - for AnimHost)
    tracer_data.parameter_update_msg.extend(struct.pack('<H', object_id))                             # object ID (not assigned to a specific object)
    tracer_data.parameter_update_msg.extend(struct.pack('<H', rpc_parameter.get_parameter_id()))      # parameter/call ID
    tracer_data.parameter_update_msg.extend(struct.pack(' B', rpc_parameter.get_tracer_type()))       # parameter type
    length = 10 + rpc_parameter.get_data_size()
    tracer_data.parameter_update_msg.extend(struct.pack('<I', length))                                # message length
    tracer_data.parameter_update_msg.extend(rpc_parameter.serialize_data())

    tracer_data.socket_u.send(tracer_data.parameter_update_msg)

def process_RPC_msg(msg: bytearray, start=0):
    scene_id    = struct.unpack( 'B', msg[start   : start+1 ])[0]
    obj_id      = struct.unpack('<H', msg[start+1 : start+3 ])[0] # unpack object ID; 2 bytes (unsigned short); little endian
    call_id     = struct.unpack('<H', msg[start+3 : start+5 ])[0]
    param_type  = struct.unpack( 'B', msg[start+5 : start+6 ])[0]
    length      = struct.unpack('<I', msg[start+6 : start+10])[0] # unpack length of parameter data; 4 bytes (uint); little endian (includes the header bytes)
    start =+ length

    # Do something with the information:)

    return start

# scene_object has type SceneObject (not importable due to circular dependencies)
def send_lock_msg(scene_object):
    lock_unlock_message = bytearray([])

    # Message header
    lock_unlock_message.extend(struct.pack('B', tracer_data.cID))           # client ID
    lock_unlock_message.extend(struct.pack('B', tracer_data.time))          # sync time
    lock_unlock_message.extend(struct.pack('B', MessageType.LOCK.value))    # message type
    
    # Message Body
    lock_unlock_message.extend(scene_object.get_lock_message())

    tracer_data.socket_u.send(lock_unlock_message)

# scene_object has type SceneObject (not importable due to circular dependencies)
def send_unlock_msg(scene_object: SceneObject):
    scene_object.lock_unlock(False) # Force unlock the scene_object

    lock_unlock_message = bytearray([])

    # Message header
    lock_unlock_message.extend(struct.pack('B', tracer_data.cID))           # client ID
    lock_unlock_message.extend(struct.pack('B', tracer_data.time))          # sync time
    lock_unlock_message.extend(struct.pack('B', MessageType.LOCK.value))    # message type
    
    # Message Body
    lock_unlock_message.extend(scene_object.get_lock_message())

    tracer_data.socket_u.send(lock_unlock_message)

def process_lock_msg(msg: bytearray, start = 0):
    scene_id    = struct.unpack( 'B', msg[start   : start+1])[0]
    obj_id      = struct.unpack('<H', msg[start+1 : start+3])[0]
    if 0 < obj_id <= len(tracer_data.scene_objects):
        lockstate = struct.unpack( 'B', msg[start+3 : start+4])[0]
        tracer_data.scene_objects[obj_id-1].lock_unlock(lockstate)

    return len(msg)
    
def close_socket_d():
    global tracer_data, v_prop
    tracer_data = bpy.context.window_manager.tracer_data
    v_prop = bpy.context.scene.tracer_properties
    if bpy.app.timers.is_registered(read_thread):
        print("Stopping thread")
        bpy.app.timers.unregister(read_thread)
        bpy.utils.unregister_class(TimerModalOperator)
    if tracer_data.socket_d:
        tracer_data.socket_d.close()
        
def close_socket_s():
    global tracer_data, tracer_props
    tracer_data = bpy.context.window_manager.tracer_data
    tracer_props = bpy.context.scene.tracer_properties
    if bpy.app.timers.is_registered(listener):
        print("Stopping subscription")
        bpy.app.timers.unregister(listener)
    if tracer_data.socket_s:
        tracer_data.socket_s.close()

def close_socket_c():
    global tracer_data, tracer_props
    tracer_data = bpy.context.window_manager.tracer_data
    tracer_props = bpy.context.scene.tracer_properties
    if bpy.app.timers.is_registered(create_ping_msg):
        print("Stopping create_ping_msg")
        bpy.app.timers.unregister(create_ping_msg)
    if tracer_data.socket_c:
        tracer_data.socket_c.close()

def close_socket_u():
    global tracer_data, tracer_props
    tracer_data = bpy.context.window_manager.tracer_data
    tracer_props = bpy.context.scene.tracer_properties
    if tracer_data.socket_u:
        tracer_data.socket_u.close()


def delta_time(startTime, endTime, length):
    def mod(a, b):
        return a % b  
    
    return min(
        mod((startTime - endTime), length),
        mod((endTime - startTime), length)
    )
