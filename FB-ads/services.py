import base64
import datetime
import json
import re
import requests

from ad_creation_api.exceptions import AdCreationError, AcceptPolicyError, AdStatsError
import http.client

http.client._MAXHEADERS = 1000


class AdCreationService:

    @classmethod
    def get_eaab_token(cls, headers: dict, cookies: dict, proxies: dict) -> tuple[str, str]:
        """
        Get EAAB token.

        Args:
            headers (Dict[str, str]): Headers for the request.
            cookies (Dict[str, str]): Cookies for the request.
            proxies (Dict[str, str]): Proxies for the request.

        Returns:
            Tuple[str, str]: Tuple containing the access token and act ID.
        """
        r = requests.Session()
        if proxies:
            r.proxies = proxies

        response = r.get('https://www.facebook.com/profile.php', headers=headers, cookies=cookies, allow_redirects=True).text
        ads_response = r.get('https://www.facebook.com/adsmanager/manage/campaigns', cookies=cookies, allow_redirects=True).text
        nek1 = re.search(r'window.location.replace\("(.*?)"\)', str(ads_response)).group(1).replace('\\', '')
        resp = r.get(nek1, cookies=cookies, allow_redirects=True).text
        access_token = re.search(r'accessToken="(.*?)"', str(resp)).group(1)
        act_id = re.search(r'act=(\d+)', str(resp)).group(1)

        if not access_token:
            raise AdCreationError("Failed to get access token")

        return access_token, act_id

    @classmethod
    def download_image(cls, url: str) -> str:
        """
        Download image from URL and encode it to base64.

        Args:
            url (str): URL of the image to download.

        Returns:
            str: Base64 encoded image content.
        """
        response = requests.get(url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')

    @classmethod
    def get_image_hash(cls, act_id: str, access_token: str, cookies: dict, img_url: str, proxies: dict) -> str:
        """
        Get the hash of an image.

        Args:
            act_id (str): The ID of the Facebook ad account.
            access_token (str): The access token.
            cookies (Dict[str, str]): Cookies for the request.
            img_url (str): URL of the image.
            proxies (Dict[str, str]): Proxies for the request.

        Returns:
            str: The hash of the image.
        """
        image_url = f'https://adsmanager-graph.facebook.com/v18.0/act_{act_id}/adimages'
        data = {
            'access_token': access_token,
            'bytes': cls.download_image(img_url)
        }
        response = requests.post(
            image_url,
            cookies=cookies,
            data=data,
            proxies=proxies,
        )
        if response.status_code == 200:
            return response.json().get('images').get('bytes').get('hash')

        raise AdCreationError("Failed to upload image")

    @classmethod
    def get_camping_body_string(cls, **kwargs) -> str:
        """
        Get the body string for a campaign creation.

        Args:
            **kwargs: Keyword arguments containing adsTargetOptions.

        Returns:
            str: The body string for the campaign.
        """
        return ("name=" + kwargs.get('adsTargetOptions').get('campaign_name') +
                "&objective=" + kwargs.get('adsTargetOptions').get('objective') +
                "&status=ACTIVE&"
                + cls.return_object_budget('campaign', kwargs) +
                "special_ad_categories=CREDIT&"
                "special_ad_category_country=UA")

    @classmethod
    def get_adset_body_string(cls, **kwargs) -> str:
        """
        Get the body string for an ad set creation.

        Args:
            **kwargs: Keyword arguments containing adsTargetOptions.

        Returns:
            str: The body string for the ad set.
        """
        targeting = json.dumps(
            {
                "geo_locations": {
                    "countries": kwargs.get('adsTargetOptions').get('countries'),
                    "location_types": kwargs.get('adsTargetOptions').get('location_types')
                },
                "age_min": kwargs.get('adsTargetOptions').get('age_from'),
                "age_max": kwargs.get('adsTargetOptions').get('age_to'),
                "genders": [kwargs.get('adsTargetOptions').get('genders')],
                "locales": kwargs.get('adsTargetOptions').get('adlocale'),
                'publisher_platforms': ['facebook',],
                'facebook_positions': ['feed',]
            }
        )
        attr_spec = json.dumps([{'event_type': 'CLICK_THROUGH', 'window_days': kwargs.get('adsTargetOptions').get('window_days')}])
        promoted_object = json.dumps({"page_id": "{result=get_page_id:$.data.0.id}", "custom_event_type": kwargs.get('adsTargetOptions').get('custom_event_type')})

        return ('name=' + kwargs.get('adsTargetOptions').get('adset_name') +
                '&billing_event=IMPRESSIONS&'
                'optimization_goal=LEAD_GENERATION'
                '&campaign_id={result=create_campaign:$.id}&'
                'targeting=' + targeting +
                '&status=ACTIVE&'
                + cls.return_object_budget('adset', kwargs) +
                'attribution_spec=' + attr_spec +
                '&promoted_object=' + promoted_object)

    @classmethod
    def get_adcreative_body_string(cls, img_hash: str, **kwargs) -> str:
        """
        Get the body string for an ad creative creation.

        Args:
            img_hash (str): The hash of the image.
            **kwargs: Keyword arguments containing payload and adsTargetOptions.

        Returns:
            str: The body string for the ad creative.
        """
        adcreative_data = json.dumps(
            {
                "page_id": "{result=get_page_id:$.data.0.id}",
                "link_data": {
                    'message': kwargs.get('payload').get('creativeConfigs').get('text'),
                    'description': kwargs.get('payload').get('creativeConfigs').get('description'),
                    'name': kwargs.get('payload').get('creativeConfigs').get('header'),
                    "link": kwargs.get('payload').get('creativeConfigs').get('link'),
                    "image_hash": img_hash,
                    'call_to_action': {
                        'type': 'LEARN_MORE',
                        'value': {
                            'link': kwargs.get('payload').get('creativeConfigs').get('link'),
                        }
                    }
                }
            }
        )
        return ('name=' + kwargs.get('adsTargetOptions').get('ad_name') +
                '&object_story_spec=' + adcreative_data)

    @classmethod
    def get_ad_body_string(cls, **kwargs) -> str:
        """
        Get the body string for an ad creation.

        Args:
            **kwargs: Keyword arguments containing adsTargetOptions.

        Returns:
            str: The body string for the ad.
        """
        ad_data = json.dumps(
            {
                "creative_id": "{result=create_adcreative:$.id}"
            }
        )

        return ('name='+ kwargs.get('adsTargetOptions').get('ad_name') +
                '&adset_id={result=create_adset:$.id}&'
                'status=ACTIVE&'
                'creative=' + ad_data)

    @classmethod
    def make_batch_request(
            cls,
            access_token: str,
            act_id: str,
            headers: dict,
            cookies: dict,
            proxy: dict,
            **kwargs
    ) -> dict:
        """
        Make a batch request to Facebook Graph API.

        Args:
            access_token (str): The access token.
            act_id (str): The ID of the Facebook ad account.
            headers (Dict[str, str]): Headers for the request.
            cookies (Dict[str, str]): Cookies for the request.
            proxy (Dict[str, str]): Proxies for the request.
            **kwargs: Keyword arguments containing payload and adsTargetOptions.

        Returns:
            dict: The JSON response from the batch request.
        """
        img_url = kwargs.get('payload').get("creativeConfigs").get('image')
        img_hash = cls.get_image_hash(act_id, access_token, cookies, img_url, proxy)

        batch_requests = [
            {
                "method": "GET",
                "relative_url": "me/adaccounts",
                "name": "get_adaccounts"
            },
            {
                "method": "GET",
                "relative_url": "me/accounts",
                "name": "get_page_id"
            },
            {
                "method": "POST",
                "relative_url": "act_{result=get_adaccounts:$.data.0.account_id}/campaigns",
                "body": cls.get_camping_body_string(**kwargs),
                'name': 'create_campaign'
            },
            {
                "method": "POST",
                "relative_url": "act_{result=get_adaccounts:$.data.0.account_id}/adsets",
                "body": cls.get_adset_body_string(**kwargs),
                "name": 'create_adset'
            },
            {
                'method': 'POST',
                'relative_url': 'act_{result=get_adaccounts:$.data.0.account_id}/adcreatives',
                "body": cls.get_adcreative_body_string(img_hash=img_hash, **kwargs),
                'name': 'create_adcreative'
            },
            {
                'method': 'POST',
                'relative_url': 'act_{result=get_adaccounts:$.data.0.account_id}/ads',
                "body": cls.get_ad_body_string(**kwargs),
                'name': 'create_ad'
            },
        ]
        response = requests.post(
            url='https://graph.facebook.com/v18.0/',
            cookies=cookies,
            json={"batch": batch_requests, "access_token": access_token},
            proxies=proxy,
            headers=headers,
        )
        return response.json()

    @classmethod
    def get_cookies(cls, cookies: dict) -> dict:
        """
        Convert cookies from list of dictionaries to a single dictionary.

        Args:
            cookies (Dict[str, str]): Cookies in the form of a list of dictionaries.

        Returns:
            Dict[str, str]: Converted cookies in the form of a dictionary.
        """
        cookies_dict = dict()
        for cookie in cookies:
            cookies_dict[cookie["name"]] = cookie["value"]

        return cookies_dict

    @classmethod
    def convert_proxy_format(cls, proxy) -> dict:
        """
        Convert proxy format from '//host:port' to 'http://username:password@host:port'.

        Args:
            proxy (str): Proxy string in the format '//host:port' or '//username:password@host:port'.

        Returns:
            str: Converted proxy string in the format 'http://username:password@host:port'.
        """
        proxy = proxy.split('//')[1]
        parts = proxy.split(':')
        if len(parts) == 4:
            host, port, login, password = parts
            return f'http://{login}:{password}@{host}:{port}'
        else:
            return proxy

    @classmethod
    def create_ad(cls, cookies: dict, user_agent: str, proxy: str = '', **kwargs) -> dict:
        """
        Create FB ad.

        Args:
            cookies (Dict[str, str]): Cookies for the request.
            user_agent (str): User agent string for the request.
            proxy (str, optional): Proxy string. Defaults to ''.
            **kwargs: Keyword arguments containing payload and adsTargetOptions.

        Returns:
            dict: JSON response from the batch request.
        """
        cookies = cls.get_cookies(cookies)
        headers = {
            "User-Agent": user_agent
        }
        proxies = {}
        if proxy:
            proxies = {
                'http': cls.convert_proxy_format(proxy),
                'https': cls.convert_proxy_format(proxy)
            }
        access_token, act_id = cls.get_eaab_token(headers=headers, cookies=cookies, proxies=proxies)
        cls.accept_policy(act_id=act_id, access_token=access_token, cookies=cookies)
        return cls.make_batch_request(
            access_token=access_token,
            act_id=act_id,
            headers=headers,
            cookies=cookies,
            proxy=proxies,
            **kwargs
        )

    @classmethod
    def return_object_budget(cls, budget_object: str, data: dict) -> str:
        """
        Return the budget string based on the budget object and data.

        Args:
            budget_object (str): The budget object.
            data (Dict[str, any]): Data containing adsTargetOptions.

        Returns:
            str: The budget string.
        """
        target_options = data.get("adsTargetOptions")
        if budget_object == target_options.get("budget_object") == budget_object:
            return (target_options.get('budget_type') +
                    '_budget=' + str(target_options.get('budget')) +
                    '&bid_strategy=' +
                    target_options.get('bid_strategy') + '&')
        return '&'

    @classmethod
    def accept_policy(cls, act_id: str, access_token: str, cookies: dict) -> None:
        """
        Accept the FB ad policy.

        Args:
            act_id (str): The ID of the Facebook ad account.
            access_token (str): The access token.
            cookies (Dict[str, str]): Cookies for the request.

        Raises:
            AcceptPolicyError: If failed to accept ad policy.
        """
        accept_policy_url = 'https://graph.facebook.com/graphql'
        data = {
            "doc_id": "1975240642598857",
            "variables": json.dumps({
                "input": {
                    "client_mutation_id": "1",
                    "actor_id": act_id
                }
            }),
            "access_token": access_token
        }
        cookies = cookies

        response = requests.post(
            url=accept_policy_url,
            cookies=cookies,
            data=data
        )
        if response.status_code != 200:
            raise AcceptPolicyError("Failed to accept ad policy")


class AdStatisticService:

    @classmethod
    def convert_proxy_format(cls, proxy: str) -> str:
        """
        Convert proxy format from '//host:port' to 'http://username:password@host:port'.

        Args:
            proxy (str): Proxy string in the format '//host:port' or '//username:password@host:port'.

        Returns:
            str: Converted proxy string in the format 'http://username:password@host:port'.
        """
        proxy_pattern = r'^http:\/\/\S+:\d+$|^http:\/\/\S+:\d+:\S+:\S+$'
        if re.match(proxy_pattern, proxy):
            proxy = proxy.split('//')[1]
            parts = proxy.split(':')
            if len(parts) == 4:
                host, port, login, password = parts
                return f'http://{login}:{password}@{host}:{port}'
            else:
                return proxy

    @classmethod
    def get_cookies(cls, cookies_list: list) -> dict:
        """
        Convert cookies from list of dictionaries to a single dictionary.

        Args:
            cookies_list (List[Dict[str, str]]): Cookies in the form of a list of dictionaries.

        Returns:
            Dict[str, str]: Converted cookies in the form of a dictionary.
        """
        cookies_dict = dict()
        for cookie in cookies_list:
            cookies_dict[cookie["name"]] = cookie["value"]
        return cookies_dict

    @classmethod
    def format_spent(cls, spent: int) -> float:
        """
        Format spent amount.

        Args:
            spent (int): Spent amount in coins.

        Returns:
            float: Spent amount with two decimal places.
        """
        return round(spent * 0.01, 2)

    @classmethod
    def format_mode_data(cls, mode_object: dict, date_to: str, date_from: str) -> dict:
        """
        Format adset/campaign data.

        Args:
            mode_object (Dict[str, any]): Mode object containing mode information.
            date_to (str): End date of the mode.
            date_from (str): Start date of the mode.

        Returns:
            Dict[str, any]: Formatted mode information.
        """
        mode_info = {
            "id": mode_object.get("id"),
            "name": mode_object.get("name"),
            "status": mode_object.get("status"),
            "cpm": mode_object.get("cpm", 0),
            "cpl": mode_object.get("cpl", 0),
            "ctr": mode_object.get("ctr"),
            "impressions": mode_object.get("impressions"),
            "spent": cls.format_spent(int(mode_object.get("spent"))),
            "date_from": date_from,
            "date_to": date_to,
            'by_day': []
        }
        return mode_info

    @classmethod
    def format_lead_data(cls, lead_data: dict) -> dict:
        """
        Format lead data.

        Args:
            lead_data (Dict[str, any]): Lead data containing lead information.

        Returns:
            Dict[str, any]: Formatted lead information.
        """
        payment_methods = []
        if lead_data.get("all_payment_methods"):
            payment_methods = lead_data.get("all_payment_methods").get("pm_credit_card").get('data')
        lead_info = {
            "id": lead_data.get('id'),
            "name": lead_data.get("name"),
            "currency": lead_data.get("currency"),
            "adtrust_dsl": lead_data.get("adtrust_dsl"),
            "credit_card": payment_methods,
            'data': dict()
        }
        return lead_info

    @classmethod
    def create_batch_request(cls, act_id: str, mode: str, time_range: dict, by_day: bool) -> list[dict]:
        """
        Create batch request for retrieving insights data for campaigns/adsets.

        Args:
            act_id (str): Ad account ID.
            mode (str): Mode type ('campaigns' or 'adsets').
            time_range (Dict[str, Union[str, int]]): Time range for insights data.
            by_day (bool): Flag indicating whether to include data by day.

        Returns:
            List[Dict[str, str]]: Batch request list.
        """
        mode_type = {
            'campaigns': "campaign",
            'adsets': "adset",
        }
        batch_request = []
        if by_day:
            batch_request.append(
                {
                    "method": "GET",
                    "relative_url": f"{act_id}/insights?"
                            f"fields={mode_type[mode]}_id,cost_per_result,cpm,ctr,impressions,spend"
                            f"&level={mode_type[mode]}"
                            "&limit=5000"
                            f"&time_range={json.dumps(time_range)}"
                            "&include_headers=false"
                            "&time_increment=1"
                }
            )
        batch_request.append({
                "method": "GET",
                "relative_url": f"{act_id}/insights?"
                    f"fields={mode_type[mode]}_id,cost_per_result,cpm,ctr,impressions,spend"
                    f"&level={mode_type[mode]}"
                    "&limit=5000"
                    f"&time_range={json.dumps(time_range)}"
                    "&include_headers=false"
            })
        return batch_request

    @classmethod
    def run_batch_request(cls, batch_body: list, access_token: str, cookies: dict, proxies: dict, headers: dict) -> list:
        """
        Execute batch request.

        Args:
            batch_body (List[Dict[str, str]]): Batch request body.
            access_token (str): Access token for authentication.
            cookies (Dict[str, str]): Cookies for authentication.
            proxies (Dict[str, str]): Proxies for making the request.
            headers (Dict[str, str]): Headers for the request.

        Returns:
            List[Dict[str, str]]: Batch response data.
        """
        batch_response = requests.post(
            url='https://graph.facebook.com/v18.0/',
            cookies=cookies,
            json={"batch": batch_body, "access_token": access_token},
            proxies=proxies,
            headers=headers,
        )
        batch_response_data = []
        if batch_response.status_code == 200:
            for response in batch_response.json():
                if response.get('code') == 200:
                    batch_response_data.append(json.loads(response.get('body')))
                else:
                    raise AdStatsError("response from FB:" + str(response.get('body')))
        return batch_response_data

    @classmethod
    def format_batch_unit(cls, mode_data: dict, by_day: bool) -> dict:
        """
        Format batch unit data.

        Args:
            mode_data (dict): Data of adset/campaign.
            by_day (bool): Flag indicating whether data is by day.

        Returns:
            dict: Formatted batch unit data.
        """
        cpl = 0
        cost_per_result = mode_data.get('cost_per_result')
        if cost_per_result:
            if cost_per_result[0].get('values'):
                cpl = cost_per_result[0].get('values')[0].get('value')

        batch_unit_data = {
            "cpl": round(float(cpl), 2),
            "cpm": round(float(mode_data.get('cpm', 0)), 2),
        }
        if by_day:
            batch_unit_data.update(
                {
                    "day": mode_data.get('date_start'),
                    "impressions": int(mode_data.get('impressions', 0)),
                    "spent": float(mode_data.get('spend', 0)),
                    "ctr": float(mode_data.get('ctr', 0)),
                }
            )
        return batch_unit_data

    @classmethod
    def format_stats_data(cls, stats_data: list) -> list:
        """
        Format statistics data.

        Args:
            stats_data (list): List of statistics data.

        Returns:
            list: Formatted statistics data.
        """
        for lead_data in stats_data:
            if lead_data.get('data'):
                lead_data['data'] = [unit_dict for unit_dict in lead_data.get('data').values()]

        return stats_data

    @classmethod
    def update_stats_unit(cls, batch_data: list, stats_data: list, mode: str, by_day: bool) -> list:
        """
        Update statistics unit.

        Args:
            batch_data (list): List of batch data.
            stats_data (list): List of statistics data.
            mode (str): Mode string.
            by_day (bool): Flag indicating whether data is by day.

        Returns:
            list: Updated statistics data.
        """
        mode_type = {
            'campaigns': "campaign",
            'adsets': "adset",
        }
        for index, batch_unit in enumerate(batch_data):
            if not batch_unit.get('data'):
                continue
            for mode_data in batch_unit.get('data'):
                batch_unit_dict = cls.format_batch_unit(mode_data, by_day)
                stats_unit = stats_data[index]['data'].get(mode_data.get(f'{mode_type[mode]}_id'))
                if stats_unit:
                    if not by_day:
                        stats_unit.update(batch_unit_dict)
                    else:
                        stats_unit['by_day'].append(batch_unit_dict)
        return stats_data

    @classmethod
    def unit_data(cls, batch_data: list, stats_data: list, mode: str, by_day: bool) -> list:
        """
        Unit batch and stats data.

        Args:
            batch_data (list): List of batch data.
            stats_data (list): List of statistics data.
            mode (str): Mode string.
            by_day (bool): Flag indicating whether data is by day.

        Returns:
            list: Formatted statistics data.
        """
        if not by_day:
            stats_data = cls.update_stats_unit(batch_data, stats_data, mode, by_day)
        if by_day:
            stats_data_without_cpl_cpm = cls.update_stats_unit(batch_data[::2], stats_data, mode, by_day)
            stats_data = cls.update_stats_unit(batch_data[1::2], stats_data_without_cpl_cpm, mode, False)

        return cls.format_stats_data(stats_data)

    @classmethod
    def parce_stats_response(cls, response_data: dict, mode: str, time_range: dict, by_day: bool) -> tuple[list, list]:
        """
        Parse statistics response.

        Args:
            response_data (dict): Response data.
            mode (str): Mode string.
            time_range (dict): Time range dictionary.
            by_day (bool): Flag indicating whether data is by day.

        Returns:
            tuple: Tuple containing result list and batch request.
        """
        result_list = []
        batch_request = []
        for lead_data in response_data.get('data'):
            lead_info = cls.format_lead_data(lead_data)
            batch_request.extend(cls.create_batch_request(lead_info.get('id'), mode, time_range, by_day))
            if lead_data.get(mode):
                for mode_object in lead_data.get(mode).get('data'):
                    mode_info = cls.format_mode_data(mode_object, time_range.get('until'), time_range.get('since'))

                    lead_info['data'][mode_info.get('id')] = mode_info
            result_list.append(lead_info)
        return result_list, batch_request

    @classmethod
    def get_ad_stats(
            cls,
            by_day: bool,
            mode: str,
            date_from: datetime.date,
            date_to: datetime.date,
            lead_creds: dict
    ) -> list:
        """
        Get FB advertisement statistics.

        Args:
            by_day (bool): Flag indicating whether data is by day.
            mode (str): adsets/campaigns.
            date_from (datetime.date): Start date of the time range.
            date_to (datetime.date): End date of the time range.
            lead_creds (dict): Dictionary containing lead credentials.

        Returns:
            list: Advertisement statistics.
        """
        ad_stats_url = 'https://graph.facebook.com/v18.0/me/adaccounts?'
        cookies = cls.get_cookies(lead_creds.get('cookies'))
        headers = {
            "User-Agent": lead_creds.get('user_agent')
        }
        if lead_creds.get('proxy'):
            proxies = {
                'http': cls.convert_proxy_format(lead_creds.get('proxy')),
                'https': cls.convert_proxy_format(lead_creds.get('proxy')),
            }
        else:
            proxies = {}
        access_token, _ = AdCreationService.get_eaab_token(headers=headers, cookies=cookies, proxies=proxies)
        time_range = json.dumps({'since': str(date_from), 'until': str(date_to)})
        params = {
            'limit': 500,
            'fields': (
                "name,"
                "status,"
                "adtrust_dsl,"
                "all_payment_methods{pm_credit_card{account_id,credential_id,display_string,exp_month,exp_year}},"
                "currency,"
                f"{mode}.limit(500)"
                f".time_range({time_range})"
                "{id,name,status,cpm,ctr,impressions,spent}"
            ),
            "access_token": access_token,
        }
        response = requests.get(
            url=ad_stats_url,
            params=params,
            cookies=cookies,
            proxies=proxies,
            headers=headers
        )
        mode_objects_data, batch_body = cls.parce_stats_response(response.json(), mode, json.loads(time_range), by_day)
        batch_info = cls.run_batch_request(batch_body, access_token, cookies, proxies, headers)
        stats = cls.unit_data(batch_info, mode_objects_data, mode, by_day)

        if response.status_code == 200:
            return stats
        else:
            raise AdStatsError('Failed to make request')
