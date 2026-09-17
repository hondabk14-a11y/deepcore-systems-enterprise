from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from deploy.huggingface.package_space import FILES, package
from deploy.huggingface.publish_space import publish


def test_package_contains_only_reviewed_sources(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "space"
    package(root, output, "a" * 40)
    actual = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    assert actual == set(FILES.values()) | {"deployment.json"}
    assert "TREASURY" not in str(actual)
    assert ".env" not in str(actual)


@pytest.mark.parametrize("private,sdk", [(False, "docker"), (True, "gradio")])
def test_upload_rejects_public_or_wrong_sdk(private, sdk):
    api = Mock()
    api.space_info.return_value = SimpleNamespace(private=private, sdk=sdk)
    with pytest.raises(ValueError, match="private Docker"):
        publish(api, "BKillings/deepcore-systems-enterprise", "/tmp/package")
    api.upload_folder.assert_not_called()


def test_upload_uses_observed_parent_commit():
    api = Mock()
    api.space_info.return_value = SimpleNamespace(private=True, sdk="docker", sha="b" * 40)
    publish(api, "BKillings/deepcore-systems-enterprise", "/tmp/package")
    assert api.upload_folder.call_args.kwargs["parent_commit"] == "b" * 40


def test_wrong_owner_is_rejected_before_network_call():
    api = Mock()
    with pytest.raises(ValueError, match="namespace"):
        publish(api, "someone-else/deepcore", "/tmp/package")
    api.space_info.assert_not_called()
