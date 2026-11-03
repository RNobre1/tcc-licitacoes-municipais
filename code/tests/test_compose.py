import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def compose_config():
    if shutil.which("docker") is None:
        pytest.skip("docker CLI is not available")

    res = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=CODE_DIR,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        pytest.fail(f"docker compose config failed: {res.stderr or res.stdout}".strip())
    return json.loads(res.stdout)


def test_required_services_defined(compose_config):
    """Ensure both postgres and qdrant services are defined."""
    services = compose_config.get("services", {})
    assert "postgres" in services, "Service 'postgres' must be defined"
    assert "qdrant" in services, "Service 'qdrant' must be defined"


def test_images_are_pinned_and_not_latest(compose_config):
    """Ensure all service images use an exact tag and not 'latest' or untagged."""
    services = compose_config.get("services", {})
    for name in ["postgres", "qdrant"]:
        service = services.get(name, {})
        image = service.get("image", "")
        assert image, f"Service '{name}' has no image specified"
        assert ":" in image, f"Image '{image}' for service '{name}' is untagged"
        _, tag = image.rsplit(":", 1)
        assert tag, f"Image '{image}' for service '{name}' has empty tag"
        assert tag != "latest" and not tag.endswith(":latest"), (
            f"Image '{image}' for service '{name}' must not use 'latest' tag"
        )


def test_services_have_healthchecks(compose_config):
    """Ensure both services define a healthcheck with a test command."""
    services = compose_config.get("services", {})
    for name in ["postgres", "qdrant"]:
        service = services.get(name, {})
        healthcheck = service.get("healthcheck")
        assert healthcheck, f"Service '{name}' must have a healthcheck"
        assert healthcheck.get("test"), f"Service '{name}' healthcheck must have a test command"


def test_services_have_named_volumes(compose_config):
    """Ensure both services mount a named volume and top-level volumes are declared."""
    services = compose_config.get("services", {})
    top_volumes = compose_config.get("volumes", {})

    for name in ["postgres", "qdrant"]:
        service = services.get(name, {})
        volumes = service.get("volumes", [])
        named_volumes = [v for v in volumes if v.get("type") == "volume"]
        assert named_volumes, f"Service '{name}' must have at least one named volume"

        for vol in named_volumes:
            vol_source = vol.get("source")
            assert vol_source in top_volumes, (
                f"Named volume '{vol_source}' for '{name}' must be declared in root volumes"
            )


def test_published_ports_bind_to_localhost(compose_config):
    """Ensure all published ports bind strictly to 127.0.0.1."""
    services = compose_config.get("services", {})
    for name in ["postgres", "qdrant"]:
        service = services.get(name, {})
        ports = service.get("ports", [])
        assert ports, f"Service '{name}' must have published ports"
        for port in ports:
            host_ip = port.get("host_ip")
            assert host_ip == "127.0.0.1", (
                f"Port {port} in service '{name}' must bind to '127.0.0.1', got '{host_ip}'"
            )


def test_host_ports_match_contract(compose_config):
    """Ensure PostgreSQL is published on 5433 and Qdrant on 6333."""
    services = compose_config.get("services", {})

    postgres_ports = services.get("postgres", {}).get("ports", [])
    postgres_published = {str(p.get("published")) for p in postgres_ports}
    assert "5433" in postgres_published, (
        f"PostgreSQL host port must be 5433, found {postgres_published}"
    )

    qdrant_ports = services.get("qdrant", {}).get("ports", [])
    qdrant_published = {str(p.get("published")) for p in qdrant_ports}
    assert "6333" in qdrant_published, f"Qdrant host port must be 6333, found {qdrant_published}"


def test_makefile_has_up_and_down_targets():
    """Ensure Makefile exists and defines 'up' and 'down' targets."""
    makefile = CODE_DIR / "Makefile"
    assert makefile.is_file(), f"Makefile not found at {makefile}"
    content = makefile.read_text()
    assert re.search(r"^up\s*:", content, re.MULTILINE), "Makefile must define 'up' target"
    assert re.search(r"^down\s*:", content, re.MULTILINE), "Makefile must define 'down' target"
