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
from .SceneObjects.SceneObjectCharacter import SceneObjectCharacter
from .tools import get_current_collections, switch_collection, parent_to_root, select_hierarchy, setup_tracer_collection;

### Function to create an empty object
def create_empty(name, location, rotation, scale, parent):
    empty = bpy.data.objects.new(name, None)
    empty.location = location
    empty.rotation_euler = rotation.to_euler()
    empty.scale = scale
    bpy.context.collection.objects.link(empty)
    if parent:
        empty.parent = parent
    return empty

def was_already_processed(armature_root_bone: bpy.types.PoseBone) -> bool:
    return armature_root_bone.name in bpy.data.objects

### Function to create an object for every bone present in the armature so that the character can be interfaced with TRACER
def process_armature(armature):
    # Get the active armature object???
    armature: bpy.types.Object = armature

    # Find the root bone (typically named "Hips")
    root_bone = None
    for bone in armature.pose.bones:
        if not bone.parent:
            root_bone = bone
            break

    # Check if the active object is an armature and whehter it has already been processed previously 
    if armature and armature.type == 'ARMATURE' and not was_already_processed(root_bone):
        
        # Adding character-specific Properties to the Blender Armature Object to set up. This allows the character to be steered on the Control Path and its animation to be edited using the Control Rig 
        if not armature.get("IK-Flag"):
            armature["IK-Flag"] = False

        if not armature.get("TRACER-Editable"):
            armature["TRACER-Editable"] = bpy.context.scene.tracer_properties.character_editable_flag

        # Forcing update visualisation of Property Panel
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
                area.tag_redraw()


        ################################################
        ###### CHARACTER SETUP FOR SCENE TRANSFER ######
        ################################################

        bpy.ops.object.mode_set(mode='POSE')  # Switch to pose mode
        
        # List to store bone information
        bone_data_list = []
        
        if root_bone:
            # Create empty object for the root bone
            empty_root = create_empty(root_bone.name, armature.matrix_world @ root_bone.head, root_bone.rotation_quaternion, root_bone.scale, None)
            empty_objects = {root_bone.name: empty_root}
            
            # Parent the root empty to the armature
            empty_root.parent = armature
            
            # Add root bone data to the list
            bone_data = {
                'name': root_bone.name,
                'parent': None,
                'location': armature.matrix_world @ root_bone.head,
                'rotation': root_bone.rotation_quaternion,
                'scale': root_bone.scale
            }
            bone_data_list.append(bone_data)
        
            # Iterate through each bone (excluding the root bone)
            for bone in armature.pose.bones:
                if bone != root_bone:
                    bone_matrix_global = armature.matrix_world @ bone.matrix
                    bone_location_global = bone_matrix_global.to_translation()
                    bone_rotation_global = bone_matrix_global.to_quaternion()

                    bone_data = {
                        'name': bone.name,
                        'parent': bone.parent,
                        'location': bone_location_global,
                        'rotation': bone_rotation_global,
                        'scale': bone.scale
                    }
                    bone_data_list.append(bone_data)
        
        bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to object mode
        
        if root_bone:
            # Dictionary to store empty objects by bone name
            for bone_data in bone_data_list[1:]:
                parent_name = bone_data['parent'].name if bone_data['parent'] else root_bone.name
                # Create empty object for each bone
                empty = create_empty(bone_data['name'], bone_data['location'], bone_data['rotation'], bone_data['scale'], empty_objects[parent_name])
                empty_objects[bone_data['name']] = empty

            # Parent the empty objects hierarchy to the armature
            for empty in empty_objects.values():
                if empty.parent:
                    empty.parent_type = 'OBJECT'
                    empty.matrix_parent_inverse = empty.parent.matrix_world.inverted()
                    armature.select_set(True)
                    bpy.context.view_layer.objects.active = armature
                    bpy.ops.object.parent_set(type='BONE', keep_transform=True)

        collection_name = "TRACER_Collection"  # Specify the collection name
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            setup_tracer_collection()

        if(get_current_collections(armature) != get_current_collections(empty_root)):
            bpy.ops.object.select_all(action='DESELECT')
            select_hierarchy(empty_root)
            switch_collection(bpy.context.selected_objects)
        else:
            bpy.ops.object.select_all(action='DESELECT')
            armature.select_set(True)
            parent_to_root([armature])

        for empty in empty_objects.values():
            empty.hide_set(True)

    else:
        if was_already_processed(root_bone):
            bpy.context.window.modal_operators[-1].report({'WARNING'}, "The Character has already been processed")
        else:
            bpy.context.window.modal_operators[-1].report({'WARNING'}, "Active object is not an armature or no armature is selected.")

