#!/bin/sh
mvn test -Dmaven.test.redirectTestOutputToFile -Dmaven.test.failure.ignore --fail-never --also-make --projects $@
