import bpy
import json
import os
import mathutils

trs_data = []
bps_data = []

def add_TRS(matrix, name):


    position = (matrix.to_translation().x, matrix.to_translation().z, matrix.to_translation().y)
    scale = (matrix.to_scale().x, matrix.to_scale().z, matrix.to_scale().y)

    rot = matrix.to_quaternion()
    rot.invert()
    rotation = (rot[1], rot[3], rot[2], rot[0])

    trs_data.append({
        "name": name,
        "position": {
            "x": position[0],
            "y": position[1],
            "z": position[2],
        },
        "scale": {
            "x": scale[0],
            "y": scale[1],
            "z": scale[2],
        },
        "rotation": {
            "x": rotation[0],
            "y": rotation[1],
            "z": rotation[2],
            "w": rotation[3],
        }
})
    
def add_bind_pose(bp_matrix, name):
    
    matrix_as_list = [list(row) for row in bp_matrix]

    # Append the bind pose data to bps_data
    bps_data.append({
        "name": name,
        "matrix": matrix_as_list
    })




def save_TRS_to_json():
    """
    Save the accumulated TRS data to a JSON file on the desktop with the specified name.

    Parameters:
        trs_data (list): The list of TRS data dictionaries to save.
    """
    # Define the desktop and output file paths
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(desktop_path, "MATRIX_LOCAL.json")

    try:
        # Ensure the desktop directory exists (it always should, but for safety)
        os.makedirs(desktop_path, exist_ok=True)

        # Save the JSON file
        with open(output_file, 'w') as json_file:
            json.dump(trs_data, json_file, indent=4)
            json.dump(bps_data, json_file, indent=4)
        print(f"TRS data saved to {output_file}")
    except Exception as e:
        print(f"Error saving TRS data to JSON: {e}")

