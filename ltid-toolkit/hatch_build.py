import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class LTIDLogGraphBuildHook(BuildHookInterface):
    src_dir = Path.cwd() / ".." / "ltid-log-graph"
    jar_dir = Path() / "ltid" / "include"
    jar_name_template = "ltid-log-graph-{version}.jar"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        subprocess.run(
            ["mvn", "package", "dependency:copy-dependencies", "-Dmaven.test.skip"],
            cwd=self.src_dir / "pkg",
        )
        jar_name = self.jar_name_template.format(version=self.metadata.version)
        build_data["force_include"][self.src_dir / "target" / "dependency"] = self.jar_dir
        build_data["force_include"][self.src_dir / "target" / jar_name] = self.jar_dir / jar_name
