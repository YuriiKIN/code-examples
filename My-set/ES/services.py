from elasticsearch_dsl import Search, Response


class ProjectListService:

    @classmethod
    def get_technology_dict(cls, response: Response) -> dict[str, int]:
        """
        Extracts technology data from Elasticsearch response.

        Args:
            response (Response): The Elasticsearch response.

        Returns:
            dict[str, int]: A dictionary containing technology names and their counts.

        """
        technologies = {bucket.key: bucket.doc_count for bucket in response.aggs.technologies.buckets}
        return technologies

    @classmethod
    def get_industry_dict(cls, response: Response) -> dict[str, int]:
        """
        Extracts industry data from Elasticsearch response.

        Args:
            response (Response): The Elasticsearch response.

        Returns:
            dict[str, int]: A dictionary containing industry names and their counts.

        """
        industries = {bucket.key: bucket.doc_count for bucket in response.aggs.industries.buckets}
        return industries

    @classmethod
    def confirm_dicts_with_items(cls, initial_dict: dict[str, int], filtered_dict: dict[str, int]) -> dict[str, str]:
        """
        Compares initial and filtered dictionaries and formats the differences.

        Args:
            initial_dict (dict): The initial dictionary.
            filtered_dict (dict): The filtered dictionary.

        Returns:
            dict: A dictionary with formatted differences.

        """
        new_dict = dict()

        if filtered_dict == initial_dict:
            return {item: f"{initial_dict[item]}" for item in initial_dict}

        for item in initial_dict:

            if filtered_dict.get(item):

                count = initial_dict[item] - filtered_dict[item]

                if count == 0:
                    new_dict[item] = initial_dict[item]
                else:
                    new_dict[item] = f'+{count}'
            else:
                if initial_dict[item] == 0:
                    new_dict[item] = f'{initial_dict[item]}'
                else:
                    new_dict[item] = f'+{initial_dict[item]}'

        return cls.sort_items_by_the_list(new_dict, list(filtered_dict.keys()))

    @classmethod
    def get_active_dict_items(cls, initial_dict: dict[str, int], filtered_dict: dict[str, int]) -> dict[str, int]:
        """
        Returns the intersection of two dictionaries.

        Args:
            initial_dict (dict): The initial dictionary.
            filtered_dict (dict): The filtered dictionary.

        Returns:
            dict: A dictionary containing items present in both dictionaries.

        """
        new_dict = dict()
        for item in initial_dict:
            if filtered_dict.get(item):
                new_dict[item] = filtered_dict[item]
            else:
                new_dict[item] = 0
        return new_dict

    @classmethod
    def get_aggregation_results(cls, es_set: Search) -> tuple[dict, dict]:
        """
        Executes Elasticsearch query and retrieves aggregation results.

        Args:
            es_set (Search): The Elasticsearch query.

        Returns:
            tuple[dict, dict]: A tuple containing dictionaries for technologies and industries.

        """
        response = es_set.execute()
        technologies = cls.get_technology_dict(response)
        industries = cls.get_industry_dict(response)
        return technologies, industries

    @classmethod
    def sort_items_by_the_list(cls, items: dict, string_list: list[str]) -> dict:
        """
        Sorts items based on the given list.

        Args:
            items (dict): The dictionary to be sorted.
            string_list (list): The list based on which sorting is done.

        Returns:
            dict: A sorted dictionary.

        """
        return dict(sorted(items.items(), key=lambda x: (x[0] not in string_list)))

