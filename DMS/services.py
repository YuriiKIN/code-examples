import os
import re

import wordninja
import whois
from better_profanity import profanity


class KeywordService:

    @classmethod
    def get_keywords_from_domain(cls, *, domain: str) -> list[str]:
        """
        Get available keywords from a domain.

        Args:
            domain (str): The domain name.

        Returns:
            List[str]: List of keywords extracted from the domain.
        """
        domain_name = domain.split(".")[0]
        if len(domain_name) <= 3:
            return [domain_name]
        return wordninja.split(domain_name)

    @classmethod
    def is_adult_content(cls, *, keyword: str) -> bool:
        """
        Check if a keyword contains adult content.

        Args:
            keyword (str): The keyword to check.

        Returns:
            bool: True if the keyword contains adult content, False otherwise.
        """
        abs_file_path = os.path.join(os.path.dirname(__file__), "adult_content/adult_words_check")
        if profanity.contains_profanity(keyword):
            return True
        with open(abs_file_path, "r") as f:
            content_regex = f.read()
        for word in content_regex.split("\n"):
            if re.match(word, keyword):
                return True
        return False


class WhoisService:

    @classmethod
    def data_validation(cls, *, domain_data) -> whois.parser.WhoisEntry | None:
        """
        Validate WHOIS data.

        Args:
            domain_data (Union[whois.parser.WhoisEntry, None]): The WHOIS data.

        Returns:
            Union[whois.parser.WhoisEntry, None]: The validated WHOIS data.
        """
        if (domain_data.expiration_date is None
                and domain_data.emails is None
                and domain_data.registrar is None):
            return None
        return domain_data

    @classmethod
    def whois_data_formatting(cls, *, domain_data: whois.parser.WhoisEntry) -> whois.parser.WhoisEntry:
        """
        Format WHOIS data.

        Args:
            domain_data (whois.parser.WhoisEntry): The WHOIS data.

        Returns:
            whois.parser.WhoisEntry: The formatted WHOIS data.
        """
        if isinstance(domain_data.name_servers, str):
            domain_data.name_servers = [domain_data.name_servers.split()[0]]
        if isinstance(domain_data.expiration_date, list):
            domain_data.expiration_date = domain_data.expiration_date[0]
        if domain_data.emails is None:
            domain_data.emails = domain_data.registrar_email
        if isinstance(domain_data.emails, list):
            domain_data.emails = domain_data.emails[0]
        return domain_data

    @classmethod
    def get_data_from_domain(cls, * domain_name: str) -> whois.parser.WhoisEntry | None:
        """
        Get WHOIS data for a domain.

        Args:
            domain_name (str): The domain name.

        Returns:
            Union[whois.parser.WhoisEntry, None]: The WHOIS data for the domain.
        """
        try:
            domain_data = whois.whois(domain_name)
        except whois.parser.PywhoisError:
            return None
        else:
            cls.whois_data_formatting(domain_data=domain_data)
            return cls.data_validation(domain_data=domain_data)