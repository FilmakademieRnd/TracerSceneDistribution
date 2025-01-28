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
import sys
import re
import mathutils
import blf
import bpy_extras.view3d_utils
import subprocess  # use Python executable (for pip usage)
from pathlib import Path  # Object-oriented filesystem paths since Python 3.4
from ..settings import TracerData



#???  
def get_rna_ui():
    rna_ui = bpy.context.object.get('_RNA_UI')
    if rna_ui is None:
        bpy.context.object['_RNA_UI'] = {}
        rna_ui = bpy.context.object['_RNA_UI']
    return rna_ui
    


# Selecting the hierarchy of all the objects seen by TRACER  
def select_hierarchy(obj):
    # Deselect all objects first
    bpy.ops.object.select_all(action='DESELECT')

    # If obj is a single object
    if isinstance(obj, bpy.types.Object):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for child in obj.children_recursive:
            child.select_set(True)
            
    # If obj is a list of objects
    elif isinstance(obj, list[bpy.types.Object]):
        for o in obj:
            o.select_set(True)
            for child in o.children_recursive:
                child.select_set(True)
    else:
        print("Invalid object type provided.")

# Getting the names of the collections to which the passed obj belongs
def get_current_collections(obj: bpy.types.Object) -> list[str]:
    current_collections = []
    for coll in obj.users_collection:
        current_collections.append(coll.name)
    return current_collections

'''
----------------------BEGIN FUNCTIONS RELATED TO THE CONTROL PATH-------------------------------
'''


'''
----------------------END FUNCTIONS RELATED TO THE CONTROL PATH-------------------------------
'''