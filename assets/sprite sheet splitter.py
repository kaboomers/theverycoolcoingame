import os
from PIL import Image

def split_sprite_sheet(image_path, rows, cols):
    try:
        # 1. Open the image
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # 2. Calculate individual sprite size
        sprite_width = img_width // cols
        sprite_height = img_height // rows
        
        print(f"Image Size: {img_width}x{img_height}")
        print(f"Calculated Sprite Size: {sprite_width}x{sprite_height}")

        # 3. Create the output folder in the same directory as the image
        file_dir = os.path.dirname(image_path)
        file_name = os.path.splitext(os.path.basename(image_path))[0]
        output_folder = os.path.join(file_dir, f"{file_name}_sprites")
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Created folder: {output_folder}")
        else:
            print(f"Saving to existing folder: {output_folder}")

        # 4. Loop through rows and columns to cut and save
        count = 0
        for row in range(rows):
            for col in range(cols):
                # Calculate the area to crop
                left = col * sprite_width
                top = row * sprite_height
                right = left + sprite_width
                bottom = top + sprite_height
                
                # Crop the image
                sprite = img.crop((left, top, right, bottom))
                
                # Save the individual sprite
                # We use formatted strings to keep filenames ordered (e.g., sprite_001.png)
                save_path = os.path.join(output_folder, f"sprite_{count:03d}.png")
                sprite.save(save_path)
                count += 1
        
        print(f"Success! {count} sprites saved to '{output_folder}'")

    except FileNotFoundError:
        print("Error: The file path you provided does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("--- Sprite Sheet Splitter ---")
    
    # Get user inputs
    path_input = input("Enter the full path to the sprite sheet image: ").strip().strip('"')
    
    try:
        rows_input = int(input("How many ROWS (vertical count) are there? "))
        cols_input = int(input("How many COLUMNS (horizontal count) are there? "))
        
        split_sprite_sheet(path_input, rows_input, cols_input)
        
    except ValueError:
        print("Error: Please enter valid whole numbers for rows and columns.")