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
import time

from mathutils import Vector, Euler, Matrix
from .settings import TracerData

# Called at DoDistribute Operator in bl_op.py
class RealTimeUpdaterOperator(bpy.types.Operator):
    bl_idname = "wm.real_time_updater"
    bl_label = "Real-Time Updater"

    _timer = None
    tracer_data: TracerData = None
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            self.check_for_updates(context)
        
        if bpy.context.scene.tracer_properties.close_connection:
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        tracer_collection = bpy.data.collections.get("TRACER_Collection")
        self.start_transforms = {}
        self.previous_bone_transforms = {}
        self.tracer_data = bpy.context.window_manager.tracer_data
        for obj in tracer_collection.objects:
            # Common properties for all objects
            self.add_to_listening(obj)

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    ### Function to compute the Euclidean distance between two color vectors
    def color_difference(color1, color2):
        return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) ** 0.5
    
    def add_to_listening(self, obj: bpy.types.Object):
        matrix_local = obj.matrix_local.copy()
        transform_data = (matrix_local.to_translation(), matrix_local.to_euler(), matrix_local.to_scale())

        # Additional properties for lights
        if obj.type == 'LIGHT':
            light_data = (obj.data.color.copy(), obj.data.energy)
            self.start_transforms[obj.name] = transform_data + light_data
        
        # Additional properties for cameras
        elif obj.type == 'CAMERA':
            camera_data = (obj.data.angle, obj.data.clip_start, obj.data.clip_end)
            self.start_transforms[obj.name] = transform_data + camera_data

        elif obj.type == 'ARMATURE':  # Ensure it's an armature object
            self.start_transforms[obj.name] = transform_data
            for bone in obj.pose.bones:
                # Get the bone's current pose transform (location, rotation_quaternion, scale)
                current_location = bone.location
                current_rotation = bone.rotation_quaternion

                # Create a key for this bone's transformation
                bone_name = bone.name
                current_transform = bone.matrix_basis.to_quaternion()
                self.previous_bone_transforms[bone_name] = current_transform

        # For other types of objects
        else:
            self.start_transforms[obj.name] = transform_data

    ### Function called at a regular interval to check for updates in the Scene w.r.t. the values in TRACER
    def check_for_updates(self, context):
        #print("Update!")
        tracer_collection: bpy.types.Collection = bpy.data.collections.get("TRACER_Collection")
        tracer_objects = tracer_collection.objects
        for obj in tracer_objects:
            if obj.name not in self.start_transforms:
                self.add_to_listening(obj)
                continue

            stored_values = self.start_transforms[obj.name]
            start_loc: Vector = stored_values[0]
            start_rot: Euler  = stored_values[1]
            start_scl: Vector = stored_values[2]

            matrix_local: Matrix = obj.matrix_local.copy()

            # Compare the current transform with the starting one
            if (matrix_local.to_translation() - start_loc).length > 0.0001:
                for scene_obj in self.tracer_data.SceneObjects:
                    if obj == scene_obj.editable_object and not scene_obj.network_lock :
                        scene_obj.parameter_list[0].set_value(matrix_local.to_translation())
                        print(obj.name +" Start location" + " " + str(start_loc)  +" " + str(matrix_local.to_translation()))

            rotation_difference = (start_rot.to_matrix().inverted() @ matrix_local.to_3x3()).to_euler()
            if any(abs(value) > 0.0001 for value in rotation_difference):
                for scene_obj in self.tracer_data.SceneObjects:
                    if obj == scene_obj.editable_object and not scene_obj.network_lock :
                        # Directly set rotation using Euler, or convert to quaternion if required
                        scene_obj.parameter_list[1].set_value(matrix_local.to_quaternion()) 
                        print(matrix_local.to_quaternion())  

            if (matrix_local.to_scale() - start_scl).length > 0.0001:
                for scene_obj in self.tracer_data.SceneObjects:
                    if obj == scene_obj.editable_object and not scene_obj.network_lock :
                        scene_obj.parameter_list[2].set_value(matrix_local.to_scale())
                        print("222")

            if obj.type == 'LIGHT':
                start_color, start_energy = self.start_transforms[obj.name][3:5]

                if RealTimeUpdaterOperator.color_difference(obj.data.color, start_color) > 0.0001:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.editable_object and not scene_obj.network_lock :
                            scene_obj.parameter_list[3].set_value(obj.data.color)

                if abs(obj.data.energy - start_energy) > 0.0001:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.editable_object and not scene_obj.network_lock :
                            scene_obj.parameter_list[4].set_value(obj.data.energy)

            # Additional checks for cameras
            elif obj.type == 'CAMERA':
                start_angle, start_clip_start, start_clip_end = stored_values[3:6]

                if abs(obj.data.angle - start_angle) > 0.0001:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.editable_object and not scene_obj.network_lock :
                            scene_obj.parameter_list[3].set_value(obj.data.angle)

                if abs(obj.data.clip_start - start_clip_start) > 0.0001:
                    for scene_obj in self.tracer_data.SceneObjects:
                        if obj == scene_obj.editable_object and not scene_obj.network_lock:
                            scene_obj.parameter_list[4].set_value(obj.data.clip_start)

                if abs(obj.data.clip_end - start_clip_end) > 0.0001:
                    for scene_obj in self.tracer_data.SceneObjects :
                        if obj == scene_obj.editable_object and not scene_obj.network_lock:
                            scene_obj.parameter_list[5].set_value(obj.data.clip_end)
            elif obj.type == 'ARMATURE':  # Ensure it's an armature object
                for scene_obj in self.tracer_data.SceneObjects :
                    if obj == scene_obj.editable_object and not scene_obj.network_lock:
                       
                        for bone in obj.pose.bones:
                            bone_name = bone.name

                            if bone.parent:
                                # Convert current bone's pose matrix to the local space of its parent
                                local_matrix = bone.parent.matrix.inverted() @ bone.matrix
                            else:
                                # Root bone stays the same (pose matrix is already correct)
                                local_matrix = bone.matrix

                            # Extract the correct local rotation
                            current_rotation = local_matrix.to_quaternion()

                            # Compare the current bone transform with the stored previous transform
                            if bone_name in self.previous_bone_transforms:
                                prev_transform = self.previous_bone_transforms[bone_name]

                                if current_rotation.dot(prev_transform) < 0.9999:
                                    for scene_obj in self.tracer_data.SceneObjects:
                                        if obj == scene_obj.editable_object and not scene_obj.network_lock:
                                            for parameter in scene_obj.parameter_list:
                                                if parameter.name == bone_name + "-rotation_quaternion":
                                                    parameter.set_value(current_rotation)

                                    # Store the updated local transform
                                    self.previous_bone_transforms[bone_name] = current_rotation.copy()



                # Update the starting transform and specific properties for lights and cameras
            if obj.type == 'LIGHT':
                self.start_transforms[obj.name] = (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy(), obj.data.color.copy(), obj.data.energy)
            elif obj.type == 'CAMERA':
                self.start_transforms[obj.name] = (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy(), obj.data.angle, obj.data.clip_start, obj.data.clip_end)
            else:
                self.start_transforms[obj.name] = (obj.matrix_local.to_translation().copy(), obj.rotation_euler.copy(), obj.scale.copy())

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    




