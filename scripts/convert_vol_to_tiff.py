import numpy as np
import struct
import skimage.io as io
import os
import argparse

"""
Script to process Heidelberg .vol OCT files and convert them to TIFF volumes.
Takes an input directory containing .vol files and converts them to 3D TIFF volumes,
preserving the directory structure in the output location.
"""

def read_vol_file(raw_file):
    """
    Read and process a .vol file, extracting the OCT volume data.
    
    Args:
        raw_file (str): Path to .vol file
        
    Returns:
        numpy.ndarray: Processed OCT volume data, normalized to [0,1] range
    """
    rawfile = open(raw_file, 'rb')
    Header = rawfile.read(2048)
    
    SizeX = struct.unpack('i', Header[12:16])[0]
    NumBscans = struct.unpack('i', Header[16:20])[0]
    SizeZ = struct.unpack('i', Header[20:24])[0]
    
    SizeXSlo = struct.unpack('i', Header[48:52])[0]
    SizeYSlo = struct.unpack('i', Header[52:56])[0]
    SloImageSize = SizeXSlo * SizeYSlo
    
    BscanHdrSize = struct.unpack('i', Header[100:104])[0]
    BsBlkSize = BscanHdrSize + SizeX * SizeZ * 4
    
    OffsetNow = 2048 + SloImageSize
    rawfile.seek(OffsetNow)
    Bscan = rawfile.read(BsBlkSize)
    BscanHdr = Bscan[:BscanHdrSize]
    NumSeg = struct.unpack('i', BscanHdr[48:52])[0]
    
    BscanVol = np.ones([NumBscans, SizeZ, SizeX]) * -1.0
    for i in np.arange(NumBscans):
        OffsetNow = 2048 + SloImageSize + i * BsBlkSize
        rawfile.seek(OffsetNow)
        Bscan = rawfile.read(BsBlkSize)
        BscanVol[i, ...] = np.array(struct.unpack('f' * len(BscanVol[i, ...].flatten()), 
                                                 Bscan[BscanHdrSize:SizeX * SizeZ * 4 + BscanHdrSize])).reshape((SizeZ, SizeX))
    
    rawfile.close()
    
    BscanVol[BscanVol >= 3.40e+38] = 0.0
    
    min_val = np.min(BscanVol)
    max_val = np.max(BscanVol)
    if max_val > min_val:
        BscanVol = (BscanVol - min_val) / (max_val - min_val)
    
    return BscanVol

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

def process_vol_files(input_dir, output_dir):
    """
    Process all .vol files in the input directory and save them as TIFF volumes.
    
    Args:
        input_dir (str): Path to directory containing .vol files
        output_dir (str): Path to directory where TIFF volumes will be saved
    """
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.vol'):
                print('Converting:', file)
                vol_filepath = os.path.join(root, file)
                
                try:
                    bscan_vol = read_vol_file(vol_filepath)
                    
                    relative_path = os.path.relpath(root, input_dir)
                    output_subdir = os.path.join(output_dir, relative_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    
                    base_filename = os.path.splitext(file)[0]
                    tiff_filepath = os.path.join(output_subdir, f"{base_filename}.tiff")
                    
                    volume_data = bscan_vol.astype(np.float32)
                    volume_data = log_volume(volume_data)
                    io.imsave(tiff_filepath, volume_data)
                    
                    print('Saved:', tiff_filepath)
                    
                except Exception as e:
                    print(f"Error processing {vol_filepath}: {str(e)}")
                    continue

def main():
    parser = argparse.ArgumentParser(description='Convert Heidelberg .vol OCT files to TIFF volumes')
    parser.add_argument('input_dir', type=str, help='Directory containing .vol files')
    parser.add_argument('output_dir', type=str, help='Directory where TIFF volumes will be saved')
    
    args = parser.parse_args()
    
    process_vol_files(args.input_dir, args.output_dir)

if __name__ == '__main__':
    main()