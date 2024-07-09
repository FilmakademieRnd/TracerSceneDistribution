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

import bpy
import time

class RealTimeUpdaterOperator(bpy.types.Operator):
    bl_idname = "wm.real_time_updater"
    bl_label = "Real-Time Updater"

    _timer = None

    
    def modal(self, context, event):
        if event.type == 'TIMER':
            self.check_for_updates(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        collection = bpy.data.collections.get("VPET_Collection")
        self.start_transforms = {}
        global vpet
        vpet = bpy.context.window_manager.vpet_data
        for obj in collection.objects:
            # Common properties for all objects
            transform_data = (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy())

            # Additional properties for lights
            if obj.type == 'LIGHT':
                light_data = (obj.data.color.copy(), obj.data.energy)
                self.start_transforms[obj.name] = transform_data + light_data

            # Additional properties for cameras
            elif obj.type == 'CAMERA':
                camera_data = (obj.data.angle, obj.data.clip_start, obj.data.clip_end)
                self.start_transforms[obj.name] = transform_data + camera_data

            # For other types of objects
            else:
                self.start_transforms[obj.name] = transform_data

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    

    def color_difference(color1, color2):
        """Calculate the Euclidean distance between two color vectors."""
        return sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)) ** 0.5

    def check_for_updates(self, context):
        print("Update!")
        for obj in bpy.data.collections.get("VPET_Collection").objects:
            if obj.name not in self.start_transforms:
                continue

            stored_values = self.start_transforms[obj.name]
            start_location, start_rotation, start_scale = stored_values[:3]

                # Compare the current transform with the starting one
            if (obj.location - start_location).length > 0.0001:
                for scene_obj in vpet.SceneObjects:
                    if obj == scene_obj.editableObject:
                        scene_obj._parameterList[0].set_value(obj.location)

            rotation_difference = (start_rotation.to_matrix().inverted() @ obj.rotation_euler.to_matrix()).to_euler()
            if any(abs(value) > 0.0001 for value in rotation_difference):
                for scene_obj in vpet.SceneObjects:
                    if obj == scene_obj.editableObject:
                        scene_obj._parameterList[1].set_value(obj.rotation_quaternion)

            if (obj.scale - start_scale).length > 0.0001:
                for scene_obj in vpet.SceneObjects:
                    if obj == scene_obj.editableObject:
                        scene_obj._parameterList[2].set_value(obj.scale)

            if obj.type == 'LIGHT':
                start_color, start_energy = self.start_transforms[obj.name][3:5]

                if RealTimeUpdaterOperator.color_difference(obj.data.color, start_color) > 0.0001:
                    for scene_obj in vpet.SceneObjects:
                        if obj == scene_obj.editableObject:
                            scene_obj._parameterList[3].set_value(obj.data.color)

                if abs(obj.data.energy - start_energy) > 0.0001:
                    for scene_obj in vpet.SceneObjects:
                        if obj == scene_obj.editableObject:
                            scene_obj._parameterList[4].set_value(obj.data.energy)

        # Additional checks for cameras
            elif obj.type == 'CAMERA':
                start_angle, start_clip_start, start_clip_end = stored_values[3:6]

                if abs(obj.data.angle - start_angle) > 0.0001:
                    for scene_obj in vpet.SceneObjects:
                        if obj == scene_obj.editableObject:
                            scene_obj._parameterList[3].set_value(obj.data.angle)

                if abs(obj.data.clip_start - start_clip_start) > 0.0001:
                    for scene_obj in vpet.SceneObjects:
                        if obj == scene_obj.editableObject:
                            scene_obj._parameterList[4].set_value(obj.data.clip_start)

                if abs(obj.data.clip_end - start_clip_end) > 0.0001:
                    for scene_obj in vpet.SceneObjects:
                        if obj == scene_obj.editableObject:
                            scene_obj._parameterList[5].set_value(obj.data.clip_end)


                # Update the starting transform and specific properties for lights and cameras
            if obj.type == 'LIGHT':
                self.start_transforms[obj.name] = (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy(), obj.data.color.copy(), obj.data.energy)
            elif obj.type == 'CAMERA':
                self.start_transforms[obj.name] = (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy(), obj.data.angle, obj.data.clip_start, obj.data.clip_end)
            else:
                self.start_transforms[obj.name] = (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy())

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    
