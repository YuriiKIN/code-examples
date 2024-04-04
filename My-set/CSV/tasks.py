logger = logging.getLogger(__name__)

@app.task
def process_csv_file(csv_content: str, user_id: int) -> tuple:
    """
    Process the CSV file content to create or update projects.

    Args:
        csv_content (str): The content of the CSV file.
        user_id (int): The ID of the user who owns the projects.

    Returns:
        Tuple[int, int]: A tuple containing the number of objects created and updated.

    Raises:
        KeyError: If the CSV file misses any required field.
        Exception: If any other error occurs during CSV processing.

    """
    try:
        objects_created, objects_updated = CSVParser.parse_and_create_projects(csv_content, user_id)
        return objects_created, objects_updated
    except KeyError as e:
        raise KeyError(f'CSV file missed required field: {",".join(e.args)}')
    except Exception as e:
        logger.error(f'Something went wrong during CSV processing: {e}')
        raise Exception("Something went wrong, try again later")
