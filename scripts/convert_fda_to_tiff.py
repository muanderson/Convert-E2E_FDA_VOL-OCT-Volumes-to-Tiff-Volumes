from oct_converter.readers import FDA
import os
import numpy as np
import tifffile as tiff
import argparse

"""
Script to process FDA OCT files and convert them to TIFF volumes.
Takes an input directory containing .fda files and processes each slice,
stacking them into a proper 3D volume before saving as TIFF.
"""

def log_volume(volume):
    """
    Apply a double square root transformation to the OCT volume for better visualization.
    This transformation helps to enhance contrast and reduce the dynamic range of OCT data,
    making subtle features more visible while maintaining structural information.
    
    Args:
        volume (numpy.ndarray): Input OCT volume data, can be 3D or 4D
        
    Returns:
        numpy.ndarray: Transformed volume with enhanced contrast
    """
    image_np = volume
    if image_np.ndim > 3:
        image_np = image_np[..., 0]
    transformed_image = np.sqrt(np.sqrt(image_np))
    return transformed_image

def process_fda_files(input_dir, output_dir):
    """
    Process all FDA files in the input directory and save them as TIFF volumes.
    Each FDA file is processed slice by slice and stacked into a 3D volume.
    
    Args:
        input_dir (str): Path to directory containing FDA files
        output_dir (str): Path to directory where TIFF volumes will be saved
    """
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.fda'):
                FDA_filepath = os.path.join(root, file)
                img = FDA(FDA_filepath)
                
                try:
                    # Get all slices
                    volume = []
                    for slice_idx in range(img.num_slices):
                        slice_data = img.read_slice(slice_idx)
                        volume.append(slice_data)
                    
                    # Stack slices into 3D volume
                    volume = np.stack(volume, axis=0)
                    
                    relative_path = os.path.relpath(root, input_dir)
                    output_subdir = os.path.join(output_dir, relative_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    
                    folder_name = os.path.splitext(file)[0]
                    fda_folder = os.path.join(output_subdir, folder_name)
                    os.makedirs(fda_folder, exist_ok=True)
                    
                    volume = volume.astype(np.float32)
                    volume = log_volume(volume)
                    tiff_filepath = os.path.join(fda_folder, f'{folder_name}.tiff')
                    print(f"Saving OCT volume to {tiff_filepath}")
                    
                    tiff.imwrite(tiff_filepath, volume)
                    
                except Exception as e:
                    print(f"Error processing {FDA_filepath}: {str(e)}")
                    continue

def main():
    parser = argparse.ArgumentParser(description='Convert FDA OCT files to TIFF volumes')
    parser.add_argument('input_dir', type=str, help='Directory containing fda files')
    parser.add_argument('output_dir', type=str, help='Directory where TIFF volumes will be saved')
    
    args = parser.parse_args()
    
    process_fda_files(args.input_dir, args.output_dir)

if __name__ == '__main__':
    main()