# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import unittest
import platform
import pytest
from azure.storage.queue import (
    VERSION,
    QueueServiceClient,
    QueueClient,
)
from settings.testcase import QueuePreparer
from devtools_testutils.storage import StorageTestCase

# ------------------------------------------------------------------------------
SERVICES = {
    QueueServiceClient: 'queue',
    QueueClient: 'queue',
}

_CONNECTION_ENDPOINTS = {'queue': 'QueueEndpoint'}

_CONNECTION_ENDPOINTS_SECONDARY = {'queue': 'QueueSecondaryEndpoint'}

class StorageQueueClientTest(StorageTestCase):
    def setUp(self):
        super(StorageQueueClientTest, self).setUp()
        self.sas_token = self.generate_sas_token()
        self.token_credential = self.generate_oauth_token()

    # --Helpers-----------------------------------------------------------------
    def validate_standard_account_endpoints(self, service, url_type, account_name, account_key):
        self.assertIsNotNone(service)
        self.assertEqual(service.account_name, account_name)
        self.assertEqual(service.credential.account_name, account_name)
        self.assertEqual(service.credential.account_key, account_key)
        self.assertTrue(f'{account_name}.{url_type}.core.windows.net' in service.url)
        self.assertTrue(f'{account_name}-secondary.{url_type}.core.windows.net' in service.secondary_endpoint)

    # --Direct Parameters Test Cases --------------------------------------------
    @QueuePreparer()
    def test_create_service_with_key(self, storage_account_name, storage_account_key):
        # Arrange

        for client, url in SERVICES.items():
            # Act
            service = client(
                self.account_url(storage_account_name, "queue"), credential=storage_account_key, queue_name='foo')

            # Assert
            self.validate_standard_account_endpoints(service, url, storage_account_name, storage_account_key)
            self.assertEqual(service.scheme, 'https')

    @QueuePreparer()
    def test_create_service_with_connection_string(self, storage_account_name, storage_account_key):

        for service_type in SERVICES.items():
            # Act
            service = service_type[0].from_connection_string(
                self.connection_string(storage_account_name, storage_account_key), queue_name="test")

            # Assert
            self.validate_standard_account_endpoints(
                service, service_type[1], storage_account_name, storage_account_key)
            self.assertEqual(service.scheme, 'https')

    @QueuePreparer()
    def test_create_service_with_sas(self, storage_account_name, storage_account_key):
        # Arrange

        for service_type in SERVICES:
            # Act
            service = service_type(
                self.account_url(storage_account_name, "queue"), credential=self.sas_token, queue_name='foo')

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertTrue(service.url.startswith('https://' + storage_account_name + '.queue.core.windows.net'))
            self.assertTrue(service.url.endswith(self.sas_token))
            self.assertIsNone(service.credential)

    @QueuePreparer()
    def test_create_service_with_token(self, storage_account_name, storage_account_key):
        for service_type in SERVICES:
            # Act
            service = service_type(
                self.account_url(storage_account_name, "queue"), credential=self.token_credential, queue_name='foo')

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertTrue(service.url.startswith('https://' + storage_account_name + '.queue.core.windows.net'))
            self.assertEqual(service.credential, self.token_credential)
            self.assertFalse(hasattr(service.credential, 'account_key'))
            self.assertTrue(hasattr(service.credential, 'get_token'))

    @QueuePreparer()
    def test_create_service_with_token_and_http(self, storage_account_name, storage_account_key):
        for service_type in SERVICES:
            # Act
            with self.assertRaises(ValueError):
                url = self.account_url(storage_account_name, "queue").replace('https', 'http')
                service_type(url, credential=self.token_credential, queue_name='foo')

    @QueuePreparer()
    def test_create_service_china(self, storage_account_name, storage_account_key):
        # Arrange

        for service_type in SERVICES.items():
            # Act
            url = self.account_url(storage_account_name, "queue").replace('core.windows.net', 'core.chinacloudapi.cn')
            service = service_type[0](
                url, credential=storage_account_key, queue_name='foo')

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertTrue(service.primary_endpoint.startswith(
                f'https://{storage_account_name}.{service_type[1]}.core.chinacloudapi.cn'))
            self.assertTrue(service.secondary_endpoint.startswith(
                f'https://{storage_account_name}-secondary.{service_type[1]}.core.chinacloudapi.cn'))

    @QueuePreparer()
    def test_create_service_protocol(self, storage_account_name, storage_account_key):
        # Arrange

        for service_type in SERVICES.items():
            # Act
            url = self.account_url(storage_account_name, "queue").replace('https', 'http')
            service = service_type[0](
                url, credential=storage_account_key, queue_name='foo')

            # Assert
            self.validate_standard_account_endpoints(
                service, service_type[1], storage_account_name, storage_account_key)
            self.assertEqual(service.scheme, 'http')

    @QueuePreparer()
    def test_create_service_empty_key(self, storage_account_name, storage_account_key):
        # Arrange
        QUEUE_SERVICES = [QueueServiceClient, QueueClient]

        for service_type in QUEUE_SERVICES:
            # Act
            with self.assertRaises(ValueError) as e:
                test_service = service_type('testaccount', credential='', queue_name='foo')

            self.assertEqual(
                str(e.exception), "You need to provide either a SAS token or an account shared key to authenticate.")

    @QueuePreparer()
    def test_create_service_with_socket_timeout(self, storage_account_name, storage_account_key):
        # Arrange

        for service_type in SERVICES.items():
            # Act
            default_service = service_type[0](
                self.account_url(storage_account_name, "queue"), credential=storage_account_key, queue_name='foo')
            service = service_type[0](
                self.account_url(storage_account_name, "queue"), credential=storage_account_key,
                queue_name='foo', connection_timeout=22)

            # Assert
            self.validate_standard_account_endpoints(
                service, service_type[1], storage_account_name, storage_account_key)
            assert service._client._client._pipeline._transport.connection_config.timeout == 22
            assert default_service._client._client._pipeline._transport.connection_config.timeout in [20, (20, 2000)]

    # --Connection String Test Cases --------------------------------------------
    @QueuePreparer()
    def test_create_service_with_connection_string_key(self, storage_account_name, storage_account_key):
        # Arrange
        conn_string = f'AccountName={storage_account_name};AccountKey={storage_account_key};'

        for service_type in SERVICES.items():
            # Act
            service = service_type[0].from_connection_string(conn_string, queue_name='foo')

            # Assert
            self.validate_standard_account_endpoints(
                service, service_type[1], storage_account_name, storage_account_key)
            self.assertEqual(service.scheme, 'https')

    @QueuePreparer()
    def test_create_service_with_connection_string_sas(self, storage_account_name, storage_account_key):
        # Arrange
        conn_string = f'AccountName={storage_account_name};SharedAccessSignature={self.sas_token};'

        for service_type in SERVICES:
            # Act
            service = service_type.from_connection_string(conn_string, queue_name='foo')

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertTrue(service.url.startswith('https://' + storage_account_name + '.queue.core.windows.net'))
            self.assertTrue(service.url.endswith(self.sas_token))
            self.assertIsNone(service.credential)

    @QueuePreparer()
    def test_create_service_with_connection_string_endpoint_protocol(self, storage_account_name, storage_account_key):
        # Arrange
        conn_string = (
            f'AccountName={storage_account_name};'
            f'AccountKey={storage_account_key};'
            'DefaultEndpointsProtocol=http;'
            'EndpointSuffix=core.chinacloudapi.cn;'
            )

        for service_type in SERVICES.items():
            # Act
            service = service_type[0].from_connection_string(conn_string, queue_name="foo")

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertTrue(
                service.primary_endpoint.startswith(
                    f'http://{storage_account_name}.{service_type[1]}.core.chinacloudapi.cn/'))
            self.assertTrue(
                service.secondary_endpoint.startswith(
                    f'http://{storage_account_name}-secondary.{service_type[1]}.core.chinacloudapi.cn'))
            self.assertEqual(service.scheme, 'http')

    @QueuePreparer()
    def test_create_service_with_connection_string_emulated(self, *args):
        # Arrange
        for service_type in SERVICES.items():
            conn_string = 'UseDevelopmentStorage=true;'

            # Act
            with self.assertRaises(ValueError):
                service = service_type[0].from_connection_string(conn_string, queue_name="foo")

    @QueuePreparer()
    def test_create_service_with_connection_string_custom_domain(self, storage_account_name, storage_account_key):
        # Arrange
        for service_type in SERVICES.items():
            conn_string = (
                f'AccountName={storage_account_name};'
                f'AccountKey={storage_account_key};'
                'QueueEndpoint=www.mydomain.com;'
                )

            # Act
            service = service_type[0].from_connection_string(conn_string, queue_name="foo")

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertTrue(service.primary_endpoint.startswith('https://www.mydomain.com/'))
            self.assertTrue(service.secondary_endpoint.startswith(
                f'https://{storage_account_name}-secondary.queue.core.windows.net'))

    @QueuePreparer()
    def test_create_service_with_conn_str_custom_domain_trailing_slash(self, storage_account_name, storage_account_key):
        # Arrange
        for service_type in SERVICES.items():
            conn_string = (
                f'AccountName={storage_account_name};'
                f'AccountKey={storage_account_key};'
                'QueueEndpoint=www.mydomain.com/;'
                )
            # Act
            service = service_type[0].from_connection_string(conn_string, queue_name="foo")

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertTrue(service.primary_endpoint.startswith('https://www.mydomain.com/'))
            self.assertTrue(service.secondary_endpoint.startswith(
                f'https://{storage_account_name}-secondary.queue.core.windows.net'))

    @QueuePreparer()
    def test_create_service_with_conn_str_custom_domain_sec_override(self, storage_account_name, storage_account_key):
        # Arrange
        for service_type in SERVICES.items():
            conn_string = (
                f'AccountName={storage_account_name};'
                f'AccountKey={storage_account_key};'
                'QueueEndpoint=www.mydomain.com/;'
                )
            # Act
            service = service_type[0].from_connection_string(
                conn_string, secondary_hostname="www-sec.mydomain.com", queue_name="foo")

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertTrue(service.primary_endpoint.startswith('https://www.mydomain.com/'))
            self.assertTrue(service.secondary_endpoint.startswith('https://www-sec.mydomain.com/'))

    @QueuePreparer()
    def test_create_service_with_conn_str_fails_if_sec_without_primary(self, storage_account_name, storage_account_key):
        for service_type in SERVICES.items():
            # Arrange
            conn_string = (
                f'AccountName={storage_account_name};'
                f'AccountKey={storage_account_key};'
                f'{_CONNECTION_ENDPOINTS_SECONDARY.get(service_type[1])}=www.mydomain.com;'
            )
            # Act

            # Fails if primary excluded
            with self.assertRaises(ValueError):
                service = service_type[0].from_connection_string(conn_string, queue_name="foo")

    @QueuePreparer()
    def test_create_service_with_conn_str_succeeds_if_sec_with_primary(self, storage_account_name, storage_account_key):
        for service_type in SERVICES.items():
            # Arrange
            conn_string = (
                f'AccountName={storage_account_name};'
                f'AccountKey={storage_account_key};'
                f'{_CONNECTION_ENDPOINTS.get(service_type[1])}=www.mydomain.com;'
                f'{_CONNECTION_ENDPOINTS_SECONDARY.get(service_type[1])}=www-sec.mydomain.com;'
            )
            # Act
            service = service_type[0].from_connection_string(conn_string, queue_name="foo")

            # Assert
            self.assertIsNotNone(service)
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertTrue(service.primary_endpoint.startswith('https://www.mydomain.com/'))
            self.assertTrue(service.secondary_endpoint.startswith('https://www-sec.mydomain.com/'))

    @QueuePreparer()
    def test_create_service_with_custom_account_endpoint_path(self, storage_account_name, storage_account_key):
        custom_account_url = "http://local-machine:11002/custom/account/path/" + self.sas_token
        for service_type in SERVICES.items():
            conn_string = (
                f'DefaultEndpointsProtocol=http;'
                f'AccountName={storage_account_name};'
                f'AccountKey={storage_account_key};'
                f'QueueEndpoint={custom_account_url};'
            )
            # Act
            service = service_type[0].from_connection_string(conn_string, queue_name="foo")

            # Assert
            self.assertEqual(service.account_name, storage_account_name)
            self.assertEqual(service.credential.account_name, storage_account_name)
            self.assertEqual(service.credential.account_key, storage_account_key)
            self.assertEqual(service.primary_hostname, 'local-machine:11002/custom/account/path')

        service = QueueServiceClient(account_url=custom_account_url)
        self.assertEqual(service.account_name, None)
        self.assertEqual(service.credential, None)
        self.assertEqual(service.primary_hostname, 'local-machine:11002/custom/account/path')
        self.assertTrue(service.url.startswith('http://local-machine:11002/custom/account/path/?'))

        service = QueueClient(account_url=custom_account_url, queue_name="foo")
        self.assertEqual(service.account_name, None)
        self.assertEqual(service.queue_name, "foo")
        self.assertEqual(service.credential, None)
        self.assertEqual(service.primary_hostname, 'local-machine:11002/custom/account/path')
        self.assertTrue(service.url.startswith('http://local-machine:11002/custom/account/path/foo?'))

        service = QueueClient.from_queue_url("http://local-machine:11002/custom/account/path/foo" + self.sas_token)
        self.assertEqual(service.account_name, None)
        self.assertEqual(service.queue_name, "foo")
        self.assertEqual(service.credential, None)
        self.assertEqual(service.primary_hostname, 'local-machine:11002/custom/account/path')
        self.assertTrue(service.url.startswith('http://local-machine:11002/custom/account/path/foo?'))

    @QueuePreparer()
    def test_request_callback_signed_header(self, storage_account_name, storage_account_key):
        # Arrange
        service = QueueServiceClient(self.account_url(storage_account_name, "queue"), credential=storage_account_key)
        name = self.get_resource_name('cont')

        # Act
        try:
            headers = {'x-ms-meta-hello': 'world'}
            queue = service.create_queue(name, headers=headers)

            # Assert
            metadata = queue.get_queue_properties().metadata
            self.assertEqual(metadata, {'hello': 'world'})
        finally:
            service.delete_queue(name)

    @QueuePreparer()
    def test_response_callback(self, storage_account_name, storage_account_key):
        # Arrange
        service = QueueServiceClient(self.account_url(storage_account_name, "queue"), credential=storage_account_key)
        name = self.get_resource_name('cont')
        queue = service.get_queue_client(name)

        # Act
        def callback(response):
            response.http_response.status_code = 200
            response.http_response.headers.clear()

        # Assert
        exists = queue.get_queue_properties(raw_response_hook=callback)
        self.assertTrue(exists)

    @QueuePreparer()
    def test_user_agent_default(self, storage_account_name, storage_account_key):
        service = QueueServiceClient(self.account_url(storage_account_name, "queue"), credential=storage_account_key)

        def callback(response):
            self.assertTrue('User-Agent' in response.http_request.headers)
            assert f"azsdk-python-storage-queue/{VERSION}" in response.http_request.headers['User-Agent']

        service.get_service_properties(raw_response_hook=callback)

    @QueuePreparer()
    def test_user_agent_custom(self, storage_account_name, storage_account_key):
        custom_app = "TestApp/v1.0"
        service = QueueServiceClient(
            self.account_url(storage_account_name, "queue"), credential=storage_account_key, user_agent=custom_app)

        def callback(response):
            self.assertTrue('User-Agent' in response.http_request.headers)
            assert (
                f"TestApp/v1.0 azsdk-python-storage-queue/{VERSION} "
                f"Python/{platform.python_version()} "
                f"({platform.platform()})"
                ) in response.http_request.headers['User-Agent']

        service.get_service_properties(raw_response_hook=callback)

        def callback(response):
            self.assertTrue('User-Agent' in response.http_request.headers)
            assert (
                f"TestApp/v2.0 TestApp/v1.0 azsdk-python-storage-queue/{VERSION} "
                f"Python/{platform.python_version()} ({platform.platform()})"
                ) in response.http_request.headers['User-Agent']

        service.get_service_properties(raw_response_hook=callback, user_agent="TestApp/v2.0")

    @QueuePreparer()
    def test_user_agent_append(self, storage_account_name, storage_account_key):
        service = QueueServiceClient(self.account_url(storage_account_name, "queue"), credential=storage_account_key)

        def callback(response):
            self.assertTrue('User-Agent' in response.http_request.headers)
            assert (
                f"customer_user_agent azsdk-python-storage-queue/{VERSION} "
                f"Python/{platform.python_version()} ({platform.platform()})"
                ) in response.http_request.headers['User-Agent']

        service.get_service_properties(raw_response_hook=callback, user_agent='customer_user_agent')

    @QueuePreparer()
    def test_create_queue_client_with_complete_queue_url(self, storage_account_name, storage_account_key):
        # Arrange
        queue_url = self.account_url(storage_account_name, "queue") + "/foo"
        service = QueueClient(queue_url, queue_name='bar', credential=storage_account_key)

            # Assert
        self.assertEqual(service.scheme, 'https')
        self.assertEqual(service.queue_name, 'bar')

    def test_error_with_malformed_conn_str(self):
        # Arrange

        for conn_str in ["", "foobar", "foobar=baz=foo", "foo;bar;baz", "foo=;bar=;", "=", ";", "=;=="]:
            for service_type in SERVICES.items():
                # Act
                with self.assertRaises(ValueError) as e:
                    service = service_type[0].from_connection_string(conn_str, queue_name="test")

                if conn_str in("", "foobar", "foo;bar;baz", ";"):
                    self.assertEqual(
                        str(e.exception), "Connection string is either blank or malformed.")
                elif conn_str in ("foobar=baz=foo" , "foo=;bar=;", "=", "=;=="):
                    self.assertEqual(
                        str(e.exception), "Connection string missing required connection details.")

    @QueuePreparer()
    def test_closing_pipeline_client(self, storage_account_name, storage_account_key):
        # Arrange
        for client, url in SERVICES.items():
            # Act
            service = client(
                self.account_url(storage_account_name, "queue"), credential=storage_account_key, queue_name='queue')

            # Assert
            with service:
                assert hasattr(service, 'close')
                service.close()

    @QueuePreparer()
    def test_closing_pipeline_client_simple(self, storage_account_name, storage_account_key):
        # Arrange
        for client, url in SERVICES.items():
            # Act
            service = client(
                self.account_url(storage_account_name, "queue"), credential=storage_account_key, queue_name='queue')
            service.close()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
