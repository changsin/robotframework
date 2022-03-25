#  Copyright 2022-2023 Testworks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import base64
import datetime
import hashlib
import hmac
import json
import logging
import sys

import requests

from robot.result import ResultVisitor


class AzureLogWriter:

    def __init__(self, execution_result):
        self._execution_result = execution_result

    def write(self, output, settings):
        logger = logging.getLogger(output)
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(output, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        azure_publisher = AzureLogPublisher(logger, settings.customer_id, settings.shared_key, settings.log_type)
        writer = AzureLogWriterVisitor(logger, azure_publisher)
        self._execution_result.visit(writer)


class AzureLogWriterVisitor(ResultVisitor):
    def __init__(self, log_writer, azure_publisher):
        self._writer = log_writer
        self.azure_publisher = azure_publisher
        self.testcases = []

    def start_suite(self, suite):
        pass

    def _get_stats(self, statistics):
        return (
            statistics.total,
            statistics.failed,
            statistics.skipped
        )

    def end_suite(self, suite):
        tests, failures, skipped = self._get_stats(suite.statistics)
        attrs = {"name": suite.name,
                 "tests": tests,
                 "failures": failures,
                 "skipped": skipped,
                 "time": self._time_as_seconds(suite.elapsedtime),
                 "timestamp": self._starttime_to_isoformat(suite.starttime),
                 "testcases": self.testcases}
        self._writer.info('testsuite {}'.format(json.dumps(attrs)))
        self.azure_publisher.post_data(json.dumps([attrs]), self.azure_publisher.log_type)

    def visit_test(self, test):
        message = test.message
        if test.failed:
            message += ': AssertionError'
        elif test.skipped:
            message += ': SkipExecution'

        testcase = {
            'classname': test.parent.longname,
            'name': test.name,
            'time': self._time_as_seconds(test.elapsedtime),
            'message': test.message
        }
        self._writer.info(testcase)
        self.testcases.append(testcase)

    def _time_as_seconds(self, millis):
        return '{:.3f}'.format(millis / 1000)

    def visit_keyword(self, kw):
        pass

    def visit_statistics(self, stats):
        pass

    def visit_errors(self, errors):
        pass

    def end_result(self, result):
        pass

    def _starttime_to_isoformat(self, stime):
        if not stime:
            return None
        return f'{stime[:4]}-{stime[4:6]}-{stime[6:8]}T{stime[9:22]}000'


class AzureLogPublisher:
    def __init__(self, logger, customer_id, shared_key, log_type):
        self.logger = logger
        self.customer_id = customer_id
        self.shared_key = shared_key
        # The log type is the name of the event that is being submitted
        self.log_type = log_type

    # Build the API signature
    def build_signature(self, date, content_length, method, content_type, resource):
        x_headers = 'x-ms-date:' + date
        string_to_hash = "{}\n{}\n{}\n{}\n{}".format(method, content_length, content_type, x_headers, resource)
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
        decoded_key = base64.b64decode(self.shared_key)
        encoded_hash = base64.b64encode(
            hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
        authorization = "SharedKey {}:{}".format(self.customer_id, encoded_hash)
        return authorization

    # Build and send a request to the POST API
    def post_data(self, body, log_type):
        method = 'POST'
        content_type = 'application/json'
        resource = '/api/logs'
        rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        content_length = len(body)
        signature = self.build_signature(rfc1123date, content_length, method, content_type, resource)
        uri = "https://{}.ods.opinsights.azure.com{}?api-version=2016-04-01".format(self.customer_id, resource)

        headers = {
            'content-type': content_type,
            'Authorization': signature,
            'Log-Type': log_type,
            'x-ms-date': rfc1123date
        }

        response = requests.post(uri, data=body, headers=headers)
        if 200 <= response.status_code <= 299:
            self.logger.info('Accepted')
        else:
            self.logger.error("Response code: {} {} {}".format(response.status_code, response.reason, response.text))
