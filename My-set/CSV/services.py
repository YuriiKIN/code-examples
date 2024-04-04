import csv


class CSVParser:
    @classmethod
    def parse_and_create_projects(cls, csv_content: str, user_id: int) -> tuple[int, int]:
        """
        Parse CSV content and create or update projects.

        Args:
            csv_content (str): The content of the CSV file.
            user_id (int): The ID of the user.

        Returns:
            tuple: A tuple containing the number of objects created and updated.
        """
        decoded_content = csv_content.splitlines()
        reader = csv.DictReader(decoded_content)
        objects_created = 0
        objects_updated = 0

        for row in reader:
            project, created = cls.create_project(row, user_id)
            cls.add_technologies(row['technologies'], project)
            cls.add_industries(row['industries'], project)
            if created:
                objects_created += 1
            objects_updated += 1

        return objects_created, objects_updated

    @staticmethod
    def create_project(row: dict, user_id: int) -> Project:
        """
        Create or update a project.

        Args:
            row (dict): The row of the CSV file as a dictionary.
            user_id (int): The ID of the user.

        Returns:
            tuple: A tuple containing the project object and a boolean indicating if it was created.
        """
        return Project.objects.update_or_create(
            title=row['title'],
            url=row['url'],
            description=row['description'],
            notes=row['notes'],
            user_id=user_id
        )

    @staticmethod
    def add_technologies(tech_list: str, project: Project) -> None:
        """
        Add technologies to a project.

        Args:
            tech_list (str): Comma-separated list of technologies.
            project (Project): The project to add technologies to.
        """
        technologies = [Technology(tech.strip()) for tech in tech_list.split(',')]
        for tech_name in technologies:
            tech, _ = Technology.objects.get_or_create(name=tech_name)
            project.technologies.add(tech)

    @staticmethod
    def add_industries(industry_list: str, project: Project) -> None:
        """
        Add industries to a project.

        Args:
            industry_list (str): Comma-separated list of industries.
            project (Project): The project to add industries to.
        """
        industries = [industry.strip() for industry in industry_list.split(',')]
        for industry_name in industries:
            industry, _ = Industry.objects.get_or_create(name=industry_name)
            project.industries.add(industry)

