import os
import glob
import numpy as np
import rasterio
from rasterio.merge import merge
import matplotlib.pyplot as plt
from matplotlib import font_manager

def mosaic_year_tiles(year_path):
    """Mosaic all tiles for a given year into a single array and return it along with transform."""
    tif_files = glob.glob(os.path.join(year_path, "*.tif"))
    if not tif_files:
        raise FileNotFoundError(f"No .tif files found in {year_path}")

    srcs = [rasterio.open(tif) for tif in tif_files]

    # Mosaic the tiles
    mosaic_arr, mosaic_transform = merge(srcs)
    # mosaic_arr shape is (bands, height, width). For single-band: (1, H, W)
    # Convert to a simple 2D array
    mosaic_arr = mosaic_arr[0]  # single band

    # Close all the source datasets
    for src in srcs:
        src.close()

    # Convert any non-zero value to 1 (presence)
    mosaic_arr = np.where(mosaic_arr > 0, 1, 0)
    return mosaic_arr, mosaic_transform

def main(data_dir, output_dir="output_images"):
    os.makedirs(output_dir, exist_ok=True)

    # Get sorted list of available years
    years = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])

    # Read and mosaic each year’s data
    year_arrays = {}
    for y in years:
        arr, transform = mosaic_year_tiles(os.path.join(data_dir, y))
        year_arrays[y] = arr

    # Initialize cumulative arrays after loading the first year
    cumulative_losses = None
    cumulative_gains = None

    # Pixel area in square kilometers (approx.)
    pixel_area_km2 = 0.000350

    previous_arr = None
    for i, y in enumerate(years):
        current_arr = year_arrays[y]

        if cumulative_losses is None:
            # Initialize cumulative arrays as False everywhere
            cumulative_losses = np.zeros_like(current_arr, dtype=bool)
            cumulative_gains = np.zeros_like(current_arr, dtype=bool)

        # If there's a previous year, calculate gains and losses for this year
        if previous_arr is not None:
            prev = previous_arr
            curr = current_arr

            gains = (prev == 0) & (curr == 1)
            losses = (prev == 1) & (curr == 0)

            # Update cumulative gains and losses
            cumulative_gains[gains] = True
            cumulative_losses[losses] = True

        # Create an RGBA image
        # Start fully transparent
        height, width = current_arr.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)

        # Gains: yellow [255, 255, 0], alpha=255 where cumulative_gains is True
        rgba[cumulative_gains] = [255, 255, 0, 255]

        # Losses: red [255, 0, 0], alpha=255 where cumulative_losses is True
        # This overwrites gains where a pixel is both gained and then lost
        rgba[cumulative_losses] = [255, 0, 0, 255]

        # Compute cumulative areas
        total_gains_area = np.sum(cumulative_gains) * pixel_area_km2
        total_losses_area = np.sum(cumulative_losses) * pixel_area_km2

        # Plot and add text
        fig, ax = plt.subplots(figsize=(10, 10), facecolor='none')
        ax.imshow(rgba, interpolation='none')
        ax.axis('off')

        # Define font properties
        font_size = 12  # Adjust font size here
        font_style = 'Roboto'  # Change to your desired font style

        # Optionally, verify if the font exists
        if font_style not in set(f.name for f in font_manager.fontManager.ttflist):
            print(f"Warning: The font '{font_style}' is not found. Using default font.")
            font_style = 'sans-serif'

        # Add title text at top-left with transparent background
        title_text = (
            f"Year: {y}\n"
            f"Cumulative Gains: {total_gains_area:.2f} km²\n"
            f"Cumulative Losses: {total_losses_area:.2f} km²"
        )
        ax.text(
            0.05, 0.99, title_text,
            transform=ax.transAxes,
            fontsize=font_size,
            fontfamily=font_style,
            color='white',
            ha='left',
            va='top',
            bbox=dict(facecolor='none', edgecolor='none')  # Fully transparent background
        )

        # Save figure with transparent background
        output_path = os.path.join(output_dir, f"{y}.png")
        plt.savefig(output_path, dpi=300, transparent=True, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        print(f"Saved {output_path}")

        previous_arr = current_arr

if __name__ == "__main__":
    data_dir = input("Enter the path to the data directory: ")
    main(data_dir, "withlabels_india_output_images")















# import os
# import glob
# import numpy as np
# import rasterio
# from rasterio.merge import merge
# from rasterio.enums import ColorInterp
# from rasterio.transform import from_bounds
#
# def mosaic_year_tiles(year_path):
#     """Mosaic all tiles for a given year into a single array and return it along with transform and CRS."""
#     tif_files = glob.glob(os.path.join(year_path, "*.tif"))
#     if not tif_files:
#         raise FileNotFoundError(f"No .tif files found in {year_path}")
#
#     srcs = [rasterio.open(tif) for tif in tif_files]
#
#     # Mosaic the tiles
#     mosaic_arr, mosaic_transform = merge(srcs)
#     # mosaic_arr shape is (bands, height, width). For single-band: (1, H, W)
#     mosaic_arr = mosaic_arr[0]  # single band
#
#     # Get CRS from the first source
#     src_crs = srcs[0].crs
#
#     # Close all the source datasets
#     for src in srcs:
#         src.close()
#
#     # Convert any non-zero value to 1 (presence)
#     mosaic_arr = np.where(mosaic_arr > 0, 1, 0)
#     return mosaic_arr, mosaic_transform, src_crs
#
# def main(data_dir, output_dir="output_images"):
#     os.makedirs(output_dir, exist_ok=True)
#
#     # Get sorted list of available years
#     years = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
#
#     if not years:
#         print("No year folders found in the specified data directory.")
#         return
#
#     # Read and mosaic each year's data
#     year_arrays = {}
#     transforms = {}
#     crs_list = []
#     for y in years:
#         print(f"Mosaicking tiles for year: {y}")
#         arr, transform, crs = mosaic_year_tiles(os.path.join(data_dir, y))
#         year_arrays[y] = arr
#         transforms[y] = transform
#         crs_list.append(crs)
#
#     # Check CRS consistency (assuming all are the same)
#     if len(set(crs.to_string() for crs in crs_list)) > 1:
#         print("Warning: Different CRS detected among tiles. Reprojection will be necessary.")
#         # Implement reprojection if needed
#         # For simplicity, we'll proceed assuming CRS are the same
#     src_crs = crs_list[0]
#
#     # Initialize cumulative arrays
#     cumulative_losses = None
#     cumulative_gains = None
#
#     # Pixel area in square kilometers (approx.)
#     pixel_area_km2 = 0.000350
#
#     previous_arr = None
#     for i, y in enumerate(years):
#         current_arr = year_arrays[y]
#
#         if cumulative_losses is None:
#             # Initialize cumulative arrays as False everywhere
#             cumulative_losses = np.zeros_like(current_arr, dtype=bool)
#             cumulative_gains = np.zeros_like(current_arr, dtype=bool)
#
#         # If there's a previous year, calculate gains and losses for this year
#         if previous_arr is not None:
#             prev = previous_arr
#             curr = current_arr
#
#             gains = (prev == 0) & (curr == 1)
#             losses = (prev == 1) & (curr == 0)
#
#             # Update cumulative gains and losses
#             cumulative_gains[gains] = True
#             cumulative_losses[losses] = True
#
#         # Create an RGBA image
#         # Start fully transparent
#         height, width = current_arr.shape
#         rgba = np.zeros((height, width, 4), dtype=np.uint8)
#
#         # Gains: yellow [255, 255, 0, 255]
#         rgba[cumulative_gains] = [0, 255, 0, 255]
#
#         # Losses: red [255, 0, 0, 255]
#         rgba[cumulative_losses] = [255, 0, 0, 255]
#
#         # Compute cumulative areas
#         total_gains_area = np.sum(cumulative_gains) * pixel_area_km2
#         total_losses_area = np.sum(cumulative_losses) * pixel_area_km2
#
#         print(f"Year: {y}, Cumulative Gains: {total_gains_area:.2f} km², Cumulative Losses: {total_losses_area:.2f} km²")
#
#         # Reorder from (height, width, 4) to (4, height, width) for rasterio
#         rgba_bands = np.transpose(rgba, (2, 0, 1))
#
#         # Define a rasterio profile with correct color interpretation
#         profile = {
#             'driver': 'GTiff',
#             'height': height,
#             'width': width,
#             'count': 4,
#             'dtype': 'uint8',
#             'crs': src_crs,
#             'transform': transforms[y],
#             'photometric': 'RGB',
#             'interleave': 'pixel',
#             'compress': 'lzw',     # Optional: compress to save space
#             'tiled': True,         # Optional: enables tiling for better performance
#             'blockxsize': 256,     # Optional: set tile size
#             'blockysize': 256,
#         }
#
#         # Define color interpretation for each band
#         color_interp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue, ColorInterp.alpha]
#
#         output_path = os.path.join(output_dir, f"{y}.tif")
#         with rasterio.open(output_path, 'w', **profile) as dst:
#             for idx in range(4):
#                 dst.write(rgba_bands[idx], idx + 1)
#             # Assign color interpretation
#             dst.colorinterp = color_interp
#
#         print(f"Saved {output_path}")
#
#         previous_arr = current_arr
#
# if __name__ == "__main__":
#     data_dir = input("Enter the path to the data directory: ")
#     main(data_dir, "india_output_images")
#
