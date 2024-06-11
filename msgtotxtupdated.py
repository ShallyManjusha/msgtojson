import os
import extract_msg
import csv
import easyocr
import re
import json

def process_msg_file(msg_file, output_folder):
    # Get the filename without extension
    file_name = os.path.splitext(os.path.basename(msg_file))[0]
    
    # Create a folder based on the filename
    output_subfolder = os.path.join(output_folder, file_name)
    os.makedirs(output_subfolder, exist_ok=True)
    
    # Save the message file inside the created folder
    msg = extract_msg.Message(msg_file)
    msg.save(customPath=output_subfolder)
    
    # Return the path to the created folder
    return output_subfolder

def extract_text_from_images(images_dir):
    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])  # You can specify other languages as well

    # Create output CSV file path inside the subfolder
    subfolders = next(os.walk(images_dir))[1]
    if len(subfolders) != 1:
        print(f"Warning: Expected exactly one subfolder in {images_dir}.")
        return
    subfolder_name = subfolders[0]
    output_subfolder = os.path.join(images_dir, subfolder_name)
    output_csv = os.path.join(output_subfolder, 'output.csv')

    # Open CSV file for writing
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Image Name', 'Extracted Text'])  # Write header

        # Loop through images in the directory
        for filename in os.listdir(output_subfolder):
            if filename.endswith(('.png', '.jpg', '.jpeg')):  # Check for image files
                image_path = os.path.join(output_subfolder, filename)

                # Extract text from the image
                try:
                    result = reader.readtext(image_path)
                    text = ' '.join([entry[1] for entry in result])
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    text = "Error"

                # Write to CSV
                csv_writer.writerow([filename, text])

def process_folder(folder_path):
    msg_files = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file)) and file.lower().endswith('.msg')]
    if msg_files:
        for msg_file in msg_files:
            output_folder = process_msg_file(os.path.join(folder_path, msg_file), folder_path)
            extract_text_from_images(output_folder)
    else:
        print("No MSG files found in the input folder. Skipping processing.")

def read_message_file(message_file):
    with open(message_file, 'r') as file:
        return file.readlines()

def read_csv_file(csv_file):
    data = {}
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        for row in reader:
            data[row[0]] = row[1]
    return data

def replace_text(message_lines, image_data):
    updated_lines = []
    for line in message_lines:
        match = re.search(r'\[cid:(\w+\.\w+)@', line)
        if match:
            image_name = match.group(1)
            if image_name in image_data:
                extracted_text = image_data[image_name]
                new_line = f'{image_name}: {extracted_text}\n'  # Modified format
                updated_lines.append(new_line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    return updated_lines

def write_updated_message(file_path, updated_lines):
    with open(file_path, 'w') as file:
        file.writelines(updated_lines)


def main():
    input_folder = "sampledata"
    output_msg_folder = "output_msg"
    processed_files = []

    # Create the output_msg folder if it doesn't exist
    os.makedirs(output_msg_folder, exist_ok=True)

    process_folder(input_folder)

    # Loop through the subfolders and process each one
    for folder_name in os.listdir(input_folder):
        folder_path = os.path.join(input_folder, folder_name)
        if os.path.isdir(folder_path):
               # Find the subfolder within the folder
            subfolder_path = None
            for subfolder_name in os.listdir(folder_path):
                subfolder_full_path = os.path.join(folder_path, subfolder_name)
                if os.path.isdir(subfolder_full_path):
                    subfolder_path = subfolder_full_path
                    break

            if subfolder_path:
                message_path = os.path.join(subfolder_path, 'message.txt')
                csv_path = os.path.join(subfolder_path, 'output.csv')
                new_message_path = os.path.join(subfolder_path, f"{folder_name}.txt")
                os.rename(message_path, new_message_path)
                
                message_lines = read_message_file(new_message_path)
                image_data = read_csv_file(csv_path)
                updated_lines = replace_text(message_lines, image_data)
                message_file = os.path.join(subfolder_path, f"{folder_name}.txt")
                write_updated_message(message_file, updated_lines)


                # Generate JSON output
                json_output = {
                    "document_name": folder_name,
                    "page_num": "NA",
                    "text": "".join(updated_lines)
                }

                # Store JSON file in output_msg folder
                json_output_path = os.path.join(output_msg_folder, f"{folder_name}.json")
                with open(json_output_path, 'w') as json_file:
                    json.dump(json_output, json_file, indent=4)

                processed_files.append(json_output_path)

    print("JSON output generated for processed MSG files:")
    for file_path in processed_files:
        print(file_path)

if __name__ == "__main__":
    main()




