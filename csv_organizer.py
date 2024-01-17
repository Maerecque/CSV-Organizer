# This script will go over every image in the directory and make some unique attributes for each image.
# This is to prevent the images from losing their tags when they are renamed.

import csv
import os
import base64
import tqdm


def check_image_exists(image_path: str) -> bool:
    """Checks if the image exists in the directory.

    Args:
        image_path (str): Path to the image.

    Returns:
        bool: True if the image exists, False if it doesn't.
    """
    return os.path.exists(image_path)


def open_csv(csv_filename) -> [list, list]:
    """Opens the csv file and returns a list of the data.

    Args:
        csv_filename (str): Name of the csv file.

    Returns:
        [list, list]: A list of the csv data and a list of the column names.
    """
    with open(csv_filename, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        csv_list = list(csv_reader)
    # Save the column names
    column_names = csv_list[0]

    # Remove the first row of the csv list because it contains the column names
    csv_list.pop(0)

    amount_removed = 0
    # Check if the image exists in the directory
    for row in tqdm.tqdm(csv_list, desc="Checking if images exist"):
        image_path = os.path.join(os.getcwd(), row[0])
        if not check_image_exists(image_path):
            csv_list.remove(row)
            amount_removed += 1

        # Check if the image has enough fields compared to the column names
        elif len(row) < len(column_names):
            # Add empty fields to the image
            for i in range(len(column_names) - len(row)):
                row.append("")

    print(f"Removed {amount_removed} images from the csv list")

    return [csv_list, column_names]


def hash_add_function(csv_filename: str, hash_field: str) -> None:
    """Go over every image in the directory and make some unique attributes for each image.
    This is to prevent the images from losing their tags when they are renamed.

    Args:
        csv_filename (str): Name of the csv file.
        hash_field (str): Name of the column that will contain the unique hash.
    """
    csv_list, columns_names = open_csv(csv_filename)

    # Get a list of all files in the current working directory
    file_formats = [".bmp", ".gif", ".jpeg", ".jpg", ".png"]
    files = [
        file
        for file in os.listdir()
        if os.path.isfile(file) and os.path.splitext(file)[1] in file_formats
    ]

    # Check if any files are missing from the csv list and if it is, add it to the csv list
    for file in tqdm.tqdm(files, desc="Checking if images are missing from the csv list"):
        image_name = os.path.basename(file)
        if not any(image_name in row for row in csv_list):
            # If it is missing, add it to the csv list
            amount_of_columns = len(columns_names)
            csv_list.append([image_name] + [""] * amount_of_columns)

    # Go over every image in the csv list and create unique attributes for each image
    for row in tqdm.tqdm(csv_list, desc="Creating unique attributes for each image"):
        image_hash = create_unique_image_hash(row[0])
        # Determine column index of the image hash
        image_hash_index = columns_names.index(hash_field)

        row[image_hash_index] = image_hash

    # Write the csv list to the csv file
    with open(csv_filename, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(columns_names)
        csv_writer.writerows(csv_list)


def check_hash(csv_filename: str, hash_field: str) -> None:
    """Check if the hash of the image is the same as the hash in the csv list.

    Args:
        csv_filename (str): Name of the csv file.
        hash_field (str): Name of the column that contains the unique hash.
    """
    csv_list, columns_names = open_csv(csv_filename)

    # Go over every image in the csv list and check if the hash is the same
    for row in tqdm.tqdm(csv_list, desc="Checking if the hash is the same"):
        image_hash = create_unique_image_hash(row[0])
        # Determine column index of the image hash
        image_hash_index = columns_names.index(hash_field)

        if row[image_hash_index] != image_hash:
            print(f"Hash of {row[0]} is not the same")


def create_unique_image_hash(image_path: str) -> str:
    """Create a unique hash from an image.
    The hash is based on the size of the image, the date the image was created and the file extension.

    Args:
        image_path (str): Image path.

    Returns:
        str: Unique hash for the image.
    """
    # Check if the image exists
    if not check_image_exists(image_path):
        return None

    # Get the size of the image
    size = os.path.getsize(image_path)

    # Get the date the image was created
    date = os.path.getctime(image_path)

    # Get the file extension and convert it to integer
    file_extension = os.path.splitext(image_path)[1]
    file_ext_int = int.from_bytes(file_extension.encode(), "big")

    # Create a unique hash based on the size and date and file extension using base64
    image_hash = base64.b64encode(str(size + date + file_ext_int).encode()).decode()

    return image_hash


if __name__ == "__main__":
    csv_filename = "file_tags.csv"
    hash_field = "Identifier"
    hash_add_function(csv_filename, hash_field)
