#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name = "django-userlog",
    version = "1.0",
    description = "Log user actions on models",
    long_description = "Hooks into the django admin log, and provides log messages for userland models.",
    keywords = "django logging log",
    license = open("LICENSE.md").read(),
    author = "Rolf Håvard Blindheim",
    author_email = "rhblind@gmail.com",
    url = "https://github.com/rhblind/django_userlog",
    install_requires = [
        "django",
    ],
    packages = [
        "userlog",
        "userlog.templatetags"
    ],
    package_data = {
        "userlog": [
            "static/css/*.css",
            "static/images/*.png",
            "static/javascripts/*.js",
            "templates/userlog/*.html",
        ]
    },
    classifiers = [
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
