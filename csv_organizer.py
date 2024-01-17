# This script will go over every image in the directory and make some unique attributes for each image.
# This is to prevent the images from losing their tags when they are renamed.

# Note to future self:
# I did an oopsie and kinda did recursion in the check_hash() function, but this is not what I wanted or intended.
# Probable fix: Get a different function to extract the csv and stuff
# With love, past self

import csv
import os
import base64
import tqdm


class HashError(Exception):
    """Raised when the hash is not the same.

    Attributes:
        found_hash -- The hash that was found.
        exp_hash -- The hash that was expected.
        err_filename -- The filename that caused the error.
    """
    def __init__(self, fnd_hash, exp_hash, err_filename):
        self.fnd_hash = fnd_hash
        self.exp_hash = exp_hash
        self.err_filename = err_filename
        self.message = f"Hash of {self.err_filename} is not the same. Found hash: {self.fnd_hash}, expected hash: {self.exp_hash}"
        super().__init__(self.message)


def check_image_exists(csv_list: list, column_names: list = []) -> list:
    """Checks if the image exists in the directory.

    Args:
        csv_list (list): List of the csv data.
        column_names (list): List of the column names.

    Returns:
        list: List of the csv data without the missing images.
    """
    amount_removed = 0
    # Check if the image exists in the directory
    for row in tqdm.tqdm(csv_list, desc="Checking if images exist"):
        image_path = os.path.join(os.getcwd(), row[0])
        if not os.path.exists(image_path):
            csv_list.remove(row)
            amount_removed += 1

        # Check if the image has enough fields compared to the column names
        elif len(row) < len(column_names):
            # Add empty fields to the image
            for i in range(len(column_names) - len(row)):
                row.append("")

    print(f"Removed {amount_removed} images from the csv list")
    return csv_list


def check_missing_images(csv_list: list, column_names: list) -> list:
    """Checks if any files are missing from the csv list and if it is, add it to the csv list.

    Args:
        csv_list (list): List of the csv data.
        column_names (list): List of the column names.

    Returns:
        list: List of the csv data without the missing images.
    """
    amount_added = 0
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
            amount_of_columns = len(column_names)
            csv_list.append([image_name] + [""] * amount_of_columns)
            amount_added += 1

    print(f"Added {amount_added} images to the csv list")
    return csv_list


def open_csv(csv_filename, hash_field, keep_faulty_hashes) -> [list, list]:
    """Opens the csv file and returns a list of the data.
    The csv is opened and checked for missing images, non-existing images and empty fields.

    Args:
        csv_filename (str): Name of the csv file.
        hash_field (str): Name of the column that contains the unique hash.
        keep_faulty_hashes (bool): Keep images with faulty hashes.

    Returns:
        [list, list]: A list of the csv data and a list of the column names.
    """
    with open(csv_filename, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        csv_list = list(csv_reader)

    # Save the column names in a separate list
    column_names = csv_list[0]

    # Remove the first row of the csv list because it contains the column names
    csv_list.pop(0)

    csv_list = check_hash(csv_filename, hash_field, keep_faulty_hashes)

    # TODO: Check tell check_image_exists() to check if the image exists in the directory but exclude any files that have a faulty hash  # noqa: E501

    # Check if the image exists in the directory
    csv_list = check_image_exists(csv_list, column_names)

    # Check for missing images from the directory
    csv_list = check_missing_images(csv_list, column_names)

    return [csv_list, column_names]


def hash_add_function(csv_filename: str, hash_field: str) -> None:
    """Go over every image in the directory and make some unique attributes for each image.
    This is to prevent the images from losing their tags when they are renamed.

    Args:
        csv_filename (str): Name of the csv file.
        hash_field (str): Name of the column that will contain the unique hash.
    """
    csv_list, columns_names = open_csv(csv_filename)

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


def check_hash(csv_filename: str, hash_field: str, keep_faulty_hashes: bool) -> list:
    """Check if the hash of the image is the same as the hash in the csv list.

    Args:
        csv_filename (str): Name of the csv file.
        hash_field (str): Name of the column that contains the unique hash.

    Returns:
        list: List of the csv data without the images that have a different hash.
    """
    csv_list, columns_names = open_csv(csv_filename, hash_field, )

    try:
        # Go over every image in the csv list and check if the hash is the same
        for row in tqdm.tqdm(csv_list, desc="Checking if the hash is the same"):
            image_hash = create_unique_image_hash(row[0])
            # Determine column index of the image hash
            image_hash_index = columns_names.index(hash_field)

            if row[image_hash_index] != image_hash:
                print(f"Hash of {row[0]} is not the same")
                # Remove the image from the csv list
                if not keep_faulty_hashes:
                    csv_list.remove(row)
                raise HashError(row[image_hash_index], image_hash, row[0])

    # If the hash is not the same, raise an error
    except HashError as e:
        print(e.message)

    return csv_list


def create_unique_image_hash(image_path: str) -> str:
    """Create a unique hash from an image.
    The hash is based on the size of the image, the date the image was created and the file extension.

    Args:
        image_path (str): Image path.

    Returns:
        str: Unique hash for the image.
    """
    # Check if the image exists
    if not os.path.exists(image_path):
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
    keep_faulty_hashes = False
    csv_filename = "file_tags.csv"
    hash_field = "Identifier"
    open_csv(csv_filename, hash_field, keep_faulty_hashes)
