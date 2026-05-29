#!/bin/bash
set -xe

cd web && bun run build && cd ..

tar -cf app.tar.gz ./app ./web/dist pyproject.toml
