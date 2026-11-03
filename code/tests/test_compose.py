import json
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parent.parent

CONTRACT_VARIABLES = {
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "QDRANT_URL",
}


def load_env_example_vars():
    env_file = CODE_DIR / ".env.example"
    assert env_file.is_file(), f".env.example not found at {env_file}"
    vars_dict = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            vars_dict[k.strip()] = v.strip()
    return vars_dict


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


def test_compose_project_name(compose_config):
    """Ensure top-level project name is explicitly defined and matches pyproject.toml."""
    raw_compose = (CODE_DIR / "compose.yaml").read_text()
    assert re.search(r"^name:\s*preparatory-phase-support", raw_compose, re.MULTILINE), (
        "compose.yaml must define top-level 'name: preparatory-phase-support'"
    )
    assert compose_config.get("name") == "preparatory-phase-support"


def test_required_services_defined(compose_config):
    """Ensure both postgres and qdrant services are defined."""
    services = compose_config.get("services", {})
    assert "postgres" in services, "Service 'postgres' must be defined"
    assert "qdrant" in services, "Service 'qdrant' must be defined"


def test_images_are_pinned_and_not_latest(compose_config):
    """Ensure all service images use an exact numeric tag and not 'latest' or untagged."""
    services = compose_config.get("services", {})
    for name in ["postgres", "qdrant"]:
        service = services.get(name, {})
        image = service.get("image", "")
        assert image, f"Service '{name}' has no image specified"
        image_name = image.split("/")[-1]
        assert ":" in image_name, f"Image '{image}' for service '{name}' has no tag"
        tag = image_name.split(":", 1)[1]
        assert re.fullmatch(r"v?\d+\.\d+(\.\d+)?", tag), (
            f"Image '{image}' tag '{tag}' must be an exact numeric version"
        )


def test_services_have_healthchecks(compose_config):
    """Ensure both services define an active healthcheck with a test command."""
    services = compose_config.get("services", {})
    for name in ["postgres", "qdrant"]:
        service = services.get(name, {})
        healthcheck = service.get("healthcheck")
        assert healthcheck, f"Service '{name}' must have a healthcheck"
        test_cmd = healthcheck.get("test")
        assert test_cmd, f"Service '{name}' healthcheck must have a test command"
        assert test_cmd != ["NONE"] and test_cmd != "NONE", (
            f"Service '{name}' healthcheck must not be disabled"
        )


def test_services_have_named_volumes(compose_config):
    """Ensure both services mount named volumes at expected target locations."""
    services = compose_config.get("services", {})
    top_volumes = compose_config.get("volumes", {})

    expected_targets = {
        "postgres": "/var/lib/postgresql",
        "qdrant": "/qdrant/storage",
    }

    for name, target in expected_targets.items():
        service = services.get(name, {})
        volumes = service.get("volumes", [])
        named_volumes = [v for v in volumes if v.get("type") == "volume"]
        assert named_volumes, f"Service '{name}' must have at least one named volume"

        for vol in named_volumes:
            vol_source = vol.get("source")
            assert vol_source in top_volumes, (
                f"Named volume '{vol_source}' for '{name}' must be declared in root volumes"
            )

        mounted_targets = [v.get("target") for v in named_volumes]
        assert target in mounted_targets, (
            f"Service '{name}' must mount named volume to '{target}', got {mounted_targets}"
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
    """Ensure PostgreSQL is published on 5433->5432 and Qdrant on 6333->6333."""
    services = compose_config.get("services", {})

    postgres_ports = services.get("postgres", {}).get("ports", [])
    assert any(
        str(p.get("published")) == "5433" and p.get("target") == 5432 for p in postgres_ports
    ), f"PostgreSQL must map published port 5433 to container port 5432, got {postgres_ports}"

    qdrant_ports = services.get("qdrant", {}).get("ports", [])
    assert any(
        str(p.get("published")) == "6333" and p.get("target") == 6333 for p in qdrant_ports
    ), f"Qdrant must map published port 6333 to container port 6333, got {qdrant_ports}"


def test_contract_variables_declared_in_env_example():
    """Ensure .env.example declares the six variables from the day 07 contract."""
    env_vars = load_env_example_vars()
    missing = CONTRACT_VARIABLES - set(env_vars.keys())
    assert not missing, f".env.example is missing contract variables: {missing}"


def test_compose_variables_declared_in_env_example():
    """Ensure all ${VAR} references in compose.yaml exist in .env.example."""
    compose_text = (CODE_DIR / "compose.yaml").read_text()
    env_vars = load_env_example_vars()
    interpolated = set(re.findall(r"(?<!\$)\$\{([A-Za-z0-9_]+)(?::[^}]*)?\}", compose_text))
    undeclared = interpolated - set(env_vars.keys())
    assert not undeclared, f"compose.yaml references undeclared variables: {undeclared}"


@pytest.mark.parametrize(
    "var_name",
    [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ],
)
def test_postgres_variables_not_hardcoded_in_compose(var_name):
    """Ensure PostgreSQL variables come from environment variables (${...}), never literals."""
    compose_text = (CODE_DIR / "compose.yaml").read_text()
    match = re.search(rf"{var_name}:\s*(\S+)", compose_text)
    assert match, f"{var_name} must be defined in compose.yaml"
    val = match.group(1).strip("\"'")
    assert val.startswith("${") and val.endswith("}"), (
        f"{var_name} in compose.yaml must come from '${{...}}', got literal: '{match.group(1)}'"
    )


def test_env_example_ports_match_contract():
    """Ensure ports configured in .env.example match contract host ports 5433 and 6333."""
    env_vars = load_env_example_vars()
    assert env_vars.get("DATABASE_PORT") == "5433"
    qdrant_url = env_vars.get("QDRANT_URL", "")
    parsed = urllib.parse.urlparse(qdrant_url)
    assert parsed.port == 6333


def test_makefile_has_up_and_down_targets():
    """Ensure Makefile exists and defines 'up' and 'down' targets."""
    makefile = CODE_DIR / "Makefile"
    assert makefile.is_file(), f"Makefile not found at {makefile}"
    content = makefile.read_text()
    assert re.search(r"^up\s*:", content, re.MULTILINE), "Makefile must define 'up' target"
    assert re.search(r"^down\s*:", content, re.MULTILINE), "Makefile must define 'down' target"


def test_makefile_recipes_match_contract():
    """Ensure Makefile recipes run non-blocking wait on up and preserve volumes on down."""
    res_up = subprocess.run(
        ["make", "-n", "up"], cwd=CODE_DIR, capture_output=True, text=True, check=True
    )
    assert "docker compose up" in res_up.stdout
    assert "-d" in res_up.stdout
    assert "--wait" in res_up.stdout

    res_down = subprocess.run(
        ["make", "-n", "down"], cwd=CODE_DIR, capture_output=True, text=True, check=True
    )
    assert "docker compose down" in res_down.stdout
    assert "-v" not in res_down.stdout
    assert "--volumes" not in res_down.stdout


@pytest.fixture
def fake_docker_env(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_docker = bin_dir / "docker"
    log_file = tmp_path / "docker.log"
    fake_docker.write_text(f'#!/bin/sh\necho "$@" >> "{log_file}"\nexit 0\n')
    fake_docker.chmod(0o755)

    makefile_content = (CODE_DIR / "Makefile").read_text()
    (tmp_path / "Makefile").write_text(makefile_content)

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    return tmp_path, log_file, env


def test_makefile_up_fails_without_env_file(fake_docker_env):
    """Ensure make up fails with a clear message and does not run docker when .env is missing."""
    work_dir, log_file, env = fake_docker_env
    res = subprocess.run(["make", "up"], cwd=work_dir, env=env, capture_output=True, text=True)
    assert res.returncode != 0
    output = f"{res.stdout}\n{res.stderr}"
    assert "copy .env.example to .env first" in output
    assert not log_file.exists(), "fake docker executable should not be called when .env is missing"


def test_makefile_up_succeeds_with_env_file(fake_docker_env):
    """Ensure make up succeeds and runs docker compose up when .env is present."""
    work_dir, log_file, env = fake_docker_env
    (work_dir / ".env").touch()
    res = subprocess.run(["make", "up"], cwd=work_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert log_file.exists(), "fake docker executable should be called when .env is present"
    assert log_file.read_text().strip() == "compose up -d --wait"


def test_makefile_down_works_without_env_file(fake_docker_env):
    """Ensure make down succeeds and runs docker compose down even when .env is missing."""
    work_dir, log_file, env = fake_docker_env
    res = subprocess.run(["make", "down"], cwd=work_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert log_file.exists(), "fake docker executable should be called by make down"
    assert log_file.read_text().strip() == "compose down"
