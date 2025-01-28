"""
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
"""

#from typing import Annotated, Set
import bpy
import sys
#from bpy_extras import anim_utils
#import os
#import re
#import time
#from mathutils import Vector, Euler
import subprocess  # use Python executable (for pip usage)

from bpy.types import Context
from bpy.app.handlers import persistent

#from .settings import TracerData, TracerProperties
#from .SceneObjects.SceneObject import SceneObject
#from .SceneObjects.SceneObjectCharacter import SceneObjectCharacter
#from .SceneObjects.SceneObjectPath import SceneObjectPath
#from .SceneObjects.AbstractParameter import Parameter, AnimHostRPC
from .Core.ServerAdapter import send_RPC_msg, send_parameter_update, set_up_thread, close_socket_d, close_socket_s, close_socket_c, close_socket_u
#from .Core.tools import clean_up_tracer_data, check_ZMQ, setup_tracer_collection, parent_to_root, add_path, make_point, add_point, move_point, update_curve, path_points_check
from .Core.SceneManager import SceneManager
#from .GenerateSkeletonObj import process_armature

## operator classes
#
class SetupScene(bpy.types.Operator):
    bl_idname = "object.setup_tracer"
    bl_label = "TRACER Scene Setup"
    bl_description = 'Create Collections for static and editable objects'

    def execute(self, context):
        print('setup scene')
        setup_tracer_collection()           # setup_tracer_connection -> See line 281
        return {'FINISHED'}

class DoDistribute(bpy.types.Operator):
    bl_idname = "object.zmq_distribute"
    bl_label = "Connect to TRACER"
    bl_description = 'Distribute the scene to TRACER clients'

    def execute(self, context):
        print("do distribute")
        if check_ZMQ():                     # check_ZMQ -> See line 264
            reset_tracer_connection()       # reset_tracer_connection -> See line 272
            scene_manager: SceneManager = bpy.context.window_manager.scene_manager
            if scene_manager.is_distributed:
                scene_manager.clear_scene_data(level=2)
                scene_manager.is_distributed = False
                DoDistribute.bl_label = "Connect to TRACER"
                return {'FINISHED'}
            else:
                context.scene.tracer_properties.close_connection = False
                # In order to change the mode, an active object MUST be there
                if not context.active_object and len(context.view_layer.objects) > 0:
                    # If the context has no active object, set any non-hidden object as active object
                    a_valid_object = None
                    i = 0
                    while i < len(context.view_layer.objects) and a_valid_object == None:
                        if not context.view_layer.objects[i].hide_get():
                            a_valid_object = context.view_layer.objects[i]
                    a_valid_object.select_set(True)
                    context.view_layer.objects.active = a_valid_object

                # Get current mode
                current_mode = context.active_object.mode
                if current_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode = 'OBJECT', toggle= True)    # Force OBJECT mode
                bpy.ops.object.select_all(action='DESELECT')
                obj_count = scene_manager.gather_scene_data()
                bpy.ops.wm.real_time_updater('INVOKE_DEFAULT')
                bpy.ops.object.single_select('INVOKE_DEFAULT')
                if obj_count > 0:
                    set_up_thread()
                    scene_manager.is_distributed = True
                    DoDistribute.bl_label = "Close connection to TRACER"
                    self.report({'INFO'}, f'Sending {str(obj_count)} Objects to TRACER')
                else:
                    self.report({'ERROR'}, 'TRACER collections not found or empty')
                if current_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode = current_mode)    # Revert mode to previous one
        else:
            self.report({'ERROR'}, 'Please Install Zero MQ before continuing')
        
        return {'FINISHED'}

class UpdateScene(bpy.types.Operator):
    bl_idname = "object.update_scene"
    bl_label = "Send Scene"
    bl_description = 'Send the latest version of the scene to TRACER'

    def execute(self, context):
        print('Updating scene data...')
        scene_manager: SceneManager = context.window_manager.scene_manager
        scene_manager.clear_scene_data(level=2)
        obj_count = scene_manager.gather_scene_data()
        if obj_count > 0:
            self.report({'INFO'}, f'Sending {str(obj_count)} Objects to TRACER')
        return {'FINISHED'}

class InstallZMQ(bpy.types.Operator):
    bl_idname = "object.zmq_install"
    bl_label = "Install ZMQ"
    bl_description = 'Install Zero MQ. You need admin rights for this to work!'

    def execute(self, context):
        print('Installing ZMQ')
        zmq_result = install_ZMQ()          # install_ZMQ -> See line 226
        if zmq_result == 'admin error':
            self.report({'ERROR'}, f'You need to be Admin to install ZMQ')
            return {'FINISHED'}
        if zmq_result == 'success':
            self.report({'INFO'}, f'Successfully Installed ZMQ')
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, str(zmq_result))
            return {'FINISHED'}

class SetupCharacter(bpy.types.Operator):
    bl_idname = "object.setup_character"
    bl_label = "TRACER Character Setup"
    bl_description = 'generate obj for each Character bone'

    def execute(self, context):
        print('Setup Character')
        character_name: str = bpy.context.scene.tracer_properties.character_name

        if character_name == '' or bpy.data.objects[character_name] == None:
            self.report({'ERROR'}, f'Invalid character to setup')
            return {'FINISHED'}
        
        if bpy.data.objects[character_name].type != 'ARMATURE':
            self.report({'ERROR'}, f'Invalid character to setup')
            return {'FINISHED'}

        if  not bpy.data.objects[character_name].get('TRACER Setup Done', False):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[character_name]
            #process_armature(bpy.data.objects[character_name])
            bpy.data.objects[character_name]['TRACER Setup Done'] = True
        return {'FINISHED'}
    
class MakeEditable(bpy.types.Operator):
    bl_idname = "object.make_obj_editable"
    bl_label = "Make selected Editable"
    bl_description = 'generate a new custom property called Editable for all selected obj'

    def execute(self, context):
        print('Make obj Editable')
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            # Add custom property "Editable" with type bool and default value True
            obj["TRACER-Editable"] = True

        # Forcing update visualisation of Property Panel
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return{'FINISHED'}
    
class ParentToRoot(bpy.types.Operator):
    bl_idname = "object.parent_selected_to_root"
    bl_label = "Add Object to TRACER"
    bl_description = 'Parent all the selected object to the TRACER Scene Root'

    def execute(self, context):
        print('Parent objects')
        parent_to_root(bpy.context.selected_objects)            # parent_to_root -> See line 322
        return {'FINISHED'}
    
class ParentCharacterToRoot(bpy.types.Operator):
    bl_idname = "object.parent_character_to_root"
    bl_label = "Add Character to TRACER"
    bl_description = 'Parent the chosen Character to the TRACER Scene Root'

    def execute(self, context):
        print('Parent character')
        if bpy.context.scene.tracer_properties.character_name in bpy.data.objects:
            character = bpy.data.objects[bpy.context.scene.tracer_properties.character_name]
            parent_to_root([character])                         # parent_to_root -> See line 322
        else:
            self.report({'ERROR'}, 'Assign a valid value to the Character field.')
        return {'FINISHED'}

''' --------------------------------------------------------------------------------------------------------------------
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++        HELPER FUNCTIONS FOR THE OPERATORS        +++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
-------------------------------------------------------------------------------------------------------------------- '''

# Installing ZMQ package for python
def install_ZMQ():
    if check_ZMQ():         # check_ZMQ -> See line 264
        return 'ZMQ is already installed'
    else:
        if bpy.app.version[0] == 2 and bpy.app.version[1] < 81:
            return 'This only works with Blender versions > 2.81'

        else:
            try:
                # will likely fail the first time, but works after `ensurepip.bootstrap()` has been called once
                import pip
            except ModuleNotFoundError as e:
                # only first attempt will reach here
                print("Pip import failed with: ", e)
                print("ERROR: Pip not activated, trying bootstrap()")
                try:
                    import ensurepip
                    ensurepip.bootstrap()
                except:  # catch *all* exceptions
                    e = sys.exc_info()[0]
                    print("ERROR: Pip not activated, trying bootstrap()")
                    print("bootstrap failed with: ", e)
            py_exec = sys.executable

        # pyzmq pip install
        try:
            print("Trying pyzmq install")
            output = subprocess.check_output([py_exec, '-m', 'pip', 'install', '--ignore-installed', 'pyzmq'])
            print(output)
            if (str(output).find('not writeable') > -1):
                return 'admin error'
            else:
                return 'success'
        except subprocess.CalledProcessError as e:
            print("ERROR: Couldn't install pyzmq.")
            return (e.output)
        
# Checking for ZMQ package installation
def check_ZMQ():
    try:
        import zmq
        return True
    except Exception as e:
        print(e)
        return False

def reset_tracer_connection():
    close_socket_d()
    close_socket_s()
    close_socket_c()
    close_socket_u()
    scene_manager: SceneManager = bpy.context.window_manager.scene_manager
    scene_manager.clear_scene_data(level=2)

## Create Collections that will contain every TRACER object
def setup_tracer_collection():
    tracer_props = bpy.context.scene.tracer_properties

    current_mode = ''
    if bpy.context.active_object:
        # Get current mode
        current_mode = str(bpy.context.active_object.mode)
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT', toggle=True)    # Force OBJECT mode
    
    # Check if the collection exists. If not, create it and link it to the scene.
    tracer_collection = bpy.data.collections.get(tracer_props.tracer_collection)
    if tracer_collection is None:
        tracer_collection = bpy.data.collections.new(tracer_props.tracer_collection)
        bpy.context.scene.collection.children.link(tracer_collection)

    # Check if the "TRACER Scene Root" object already exists. If not, create it and link it to the collection.
    root = bpy.context.scene.objects.get('TRACER Scene Root')
    if root is None:
        bpy.ops.object.empty_add(type='PLAIN_AXES', rotation=(0,0,0), location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.active_object.name = 'TRACER Scene Root'
        root = bpy.context.active_object
        if root.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(root)
        # Unlinking object from ALL collections
        for coll in bpy.data.collections:
            if root.name in coll.objects:
                coll.objects.unlink(root)
        
        tracer_collection.objects.link(root)
        if root.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(root)
    else:
        # Check if the "TRACER Scene Root" object is already linked to the collection. If not link it.
        if not root.name in tracer_collection.objects:
            tracer_collection.objects.link(root)
    
    if current_mode != '' and current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode = 'OBJECT', toggle=True)    # Revert mode to previous one

# Makes the TRACER Scene Root object the parent of every currently selected object
def parent_to_root(objs: list[bpy.types.Object]) -> tuple[set[str], str]:
    parent_object_name = "TRACER Scene Root"
    parent_object: bpy.types.Object = bpy.data.objects.get(parent_object_name)
    collection: bpy.types.Collection = bpy.data.collections.get(bpy.context.scene.tracer_properties.tracer_collection)

    if parent_object is None or collection is None:
        report_type = {'ERROR'}
        report_string = "Set up the TRACER Scene components first"
        return (report_type, report_string)

    for obj in objs:
        # Check if the object is not the parent object itself
        if obj != parent_object:
            # Set the parent of the selected object to the parent object
            obj.parent = parent_object
            obj.matrix_parent_inverse = parent_object.matrix_world.inverted()
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            # Link the object to the new collection
            collection.objects.link(obj)
            switch_collection(obj.children_recursive)       # switch_collection -> See line 344 - just down below :)

def switch_collection(objs: list[bpy.types.Object]) -> tuple[set[str], str]:
    collection_name: str = bpy.context.scene.tracer_properties.tracer_collection  # Specify the collection name
    collection: bpy.types.Collection = bpy.data.collections.get(collection_name)
    if collection is None:
        report_type = {'ERROR'}
        report_string = "Set up the TRACER Scene components first"
        return (report_type, report_string)
                    
    for obj in objs:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)

        # Link the object to the new collection
        collection.objects.link(obj)