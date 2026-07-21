from __future__ import annotations

import json
from typing import Any

import pytest

from spider_vtbasmr_gui.integrations.netdisk.client import NetdiskClient
from spider_vtbasmr_gui.integrations.netdisk.gateway import NetdiskGatewayError


class FakeGateway:
    appid = "app-id"
    product = "netdisk"
    device_id = "device-id"

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request_json(self, **request: Any) -> dict[str, Any]:
        self.requests.append(request)
        return self.responses.pop(0)


def test_transfer_share_all_builds_verified_transfer_request() -> None:
    gateway = FakeGateway(
        [
            {"errno": 0, "data": {"spwd": "verified"}},
            {"errno": 0, "data": {"list": [{"fsid": 10}, {"fs_id": "20"}]}},
            {"errno": 0, "data": {"task_id": 1}},
        ]
    )
    client = NetdiskClient(gateway)  # type: ignore[arg-type]

    client.transfer_share_all(
        "https://pan.baidu.com/s/1abc123?pwd=a1b2",
        "/target/folder",
    )

    assert [request["path"].rsplit("/", 1)[-1] for request in gateway.requests] == [
        "verify",
        "list",
        "transfer",
    ]
    transfer = gateway.requests[-1]
    assert transfer["params"]["device_id"] == "device-id"
    assert json.loads(transfer["form_data"]["fsid_list"]) == ["10", "20"]
    assert transfer["form_data"]["to_path"] == "/target/folder"


def test_download_by_paths_resolves_file_id_before_submitting() -> None:
    gateway = FakeGateway(
        [
            {"errno": 0, "list": [{"server_filename": "batch", "fs_id": 42}]},
            {"code": 0, "data": {"task_id": "task"}},
        ]
    )
    client = NetdiskClient(gateway)  # type: ignore[arg-type]

    client.download_by_paths("/nas/download", ["/transfer/batch"])

    assert gateway.requests[0]["params"]["dir"] == "/transfer"
    assert gateway.requests[1]["json_data"] == {
        "targetPath": "/nas/download",
        "fsIds": [42],
        "rtype": 1,
    }


def test_nonzero_api_code_is_reported_without_network_retry() -> None:
    gateway = FakeGateway([{"errno": -1, "message": "denied"}])
    client = NetdiskClient(gateway)  # type: ignore[arg-type]

    with pytest.raises(NetdiskGatewayError, match="denied"):
        client.create_folder("/target")

    assert len(gateway.requests) == 1