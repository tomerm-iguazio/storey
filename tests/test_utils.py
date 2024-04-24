# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import datetime

from fsspec.implementations.local import LocalFileSystem

from storey.utils import (
    find_filters,
    get_combined_filters,
    get_remaining_path,
    url_to_file_system,
)


def test_get_path_utils():
    url = "wasbs://mycontainer@myaccount.blob.core.windows.net/path/to/object.csv"
    schema, path = get_remaining_path(url)
    assert path == "mycontainer/path/to/object.csv"
    assert schema == "wasbs"


def test_ds_get_path_utils():
    url = "ds://:file@profile/path/to/object.csv"
    fs, path = url_to_file_system(url, "")
    assert path == "/path/to/object.csv"
    assert isinstance(fs, LocalFileSystem)


def test_find_filters():
    filters = []
    find_filters([], datetime.datetime.min, datetime.datetime.max, filters, "time")
    assert filters == [[("time", ">", datetime.datetime.min), ("time", "<=", datetime.datetime.max)]]
    filters = []
    find_filters([], None, datetime.datetime.max, filters, "time")
    assert filters == [[("time", "<=", datetime.datetime.max)]]
    filters = []
    find_filters([], None, None, filters, None)
    assert filters == [[]]


def test_get_combined_filters():
    min_filter = ("time", ">", datetime.datetime.min)
    max_filter = ("time", "<=", datetime.datetime.max)
    city_filter = ("city", "=", "Tel Aviv")

    assert get_combined_filters(datetime_filters=[[]], additional_filters=[]) == [[]]
    assert get_combined_filters(datetime_filters=[[max_filter]], additional_filters=[]) == [[max_filter]]
    assert get_combined_filters(datetime_filters=[[]], additional_filters=[city_filter]) == [[city_filter]]

    datetime_filter = [[min_filter, max_filter]]
    additional_filters = [city_filter]
    combined_filters = get_combined_filters(datetime_filters=datetime_filter, additional_filters=additional_filters)
    assert combined_filters == [[min_filter, max_filter, city_filter]]
    datetime_filter = [[min_filter], [max_filter]]
    additional_filters = [city_filter, ("age", ">=", "40")]
    combined_filters = get_combined_filters(datetime_filters=datetime_filter, additional_filters=additional_filters)
    assert combined_filters == [
        [min_filter, *additional_filters],
        [max_filter, *additional_filters],
    ]
