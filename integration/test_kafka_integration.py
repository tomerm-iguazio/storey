# Copyright 2020 Iguazio
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
import asyncio
import datetime
import json
import os
from time import sleep

import pytest

from storey import AsyncEmitSource, Event, Reduce, SyncEmitSource, build_flow
from storey.targets import KafkaTarget

kafka_brokers = os.getenv("KAFKA_BROKERS")
topic = "test_kafka_integration"

if kafka_brokers:
    import kafka


def append_return(lst, x):
    lst.append(x)
    return lst


@pytest.fixture()
def kafka_topic_setup_teardown():
    # Setup
    kafka_admin_client = kafka.KafkaAdminClient(bootstrap_servers=kafka_brokers)
    kafka_consumer = kafka.KafkaConsumer(topic, bootstrap_servers=kafka_brokers, auto_offset_reset="earliest")
    try:
        kafka_admin_client.delete_topics([topic])
        sleep(1)
    except kafka.errors.UnknownTopicOrPartitionError:
        pass
    kafka_admin_client.create_topics([kafka.admin.NewTopic(topic, 1, 1)])

    # Test runs
    yield kafka_consumer

    # Teardown
    kafka_admin_client.delete_topics([topic])
    kafka_admin_client.close()
    kafka_consumer.close()


@pytest.mark.skipif(
    not kafka_brokers,
    reason="KAFKA_BROKERS must be defined to run kafka tests",
)
def test_kafka_target(kafka_topic_setup_teardown):
    kafka_consumer = kafka_topic_setup_teardown

    controller = build_flow(
        [
            SyncEmitSource(),
            KafkaTarget(kafka_brokers, topic, sharding_func=0, full_event=False),
        ]
    ).run()
    events = []
    for i in range(100):
        key = None
        if i > 0:
            key = f"key{i}"
        event = Event({"hello": i, "time": datetime.datetime(2023, 12, 26)}, key)
        events.append(event)
        controller.emit(event)

    controller.terminate()
    controller.await_termination()

    kafka_consumer.subscribe([topic])
    for event in events:
        record = next(kafka_consumer)
        if event.key is None:
            if event.key is None:
                assert record.key is None
            else:
                assert record.key.decode("UTF-8") == event.key
        assert record.value.decode("UTF-8") == json.dumps(event.body, default=str)


async def async_test_write_to_kafka_full_event_readback(kafka_topic_setup_teardown):
    kafka_consumer = kafka_topic_setup_teardown

    controller = build_flow(
        [
            AsyncEmitSource(),
            KafkaTarget(kafka_brokers, topic, sharding_func=lambda _: 0, full_event=True),
        ]
    ).run()
    events = []
    for i in range(10):
        event = Event(i, id=str(i))
        events.append(event)
        await controller.emit(event)

    await asyncio.sleep(5)

    readback_records = []
    kafka_consumer.subscribe([topic])
    for event in events:
        record = next(kafka_consumer)
        if event.key is None:
            if event.key is None:
                assert record.key is None
            else:
                assert record.key.decode("UTF-8") == event.key
        readback_records.append(json.loads(record.value.decode("UTF-8")))

    controller = build_flow(
        [
            AsyncEmitSource(),
            Reduce([], lambda acc, x: append_return(acc, x), full_event=True),
        ]
    ).run()
    for record in readback_records:
        await controller.emit(Event(record, id="some-new-id"))

    await controller.terminate()
    result = await controller.await_termination()

    assert len(result) == 10

    for i, record in enumerate(result):
        assert record.body == i
        assert record.id == str(i)


@pytest.mark.skipif(
    not kafka_brokers,
    reason="KAFKA_BROKERS must be defined to run kafka tests",
)
def test_async_test_write_to_kafka_full_event_readback(kafka_topic_setup_teardown):
    asyncio.run(async_test_write_to_kafka_full_event_readback(kafka_topic_setup_teardown))
