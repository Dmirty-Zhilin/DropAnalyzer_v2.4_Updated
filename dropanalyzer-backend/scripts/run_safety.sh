#!/usr/bin/env bash
pip freeze > requirements-lock.txt
safety check -r requirements-lock.txt
