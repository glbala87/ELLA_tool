---
title: Overview and introduction
---

# Technical documentation: <br>Overview and introduction

This page provides an introduction to the technical aspects of ELLA. 

[[toc]]

Detailed descriptions of various technical aspects of ELLA are found in these separate sections: 

- [Setup](/technical/setup.md): How to deploy and setup a demo, production and/or development environment.
- [Configuration](/technical/configuration.md): How to configure ELLA for your needs.
- [Production tasks](/technical/production-tasks.md): Common production tasks with the ELLA command line interface (ella-cli).
- [System internals](/technical/sysinternals.md): ELLA's inner workings.

## About ELLA

ELLA is a tool for clinical interpretation of genetic variants, where the user either interprets a **single variant**, or several variants belonging together in an analysis. The result of the interpretation work are **assessments** that include the classification of the variant (Class 1-5, Drug response, Risk factor or Not provided). The interpretation must be approved by another person in a multi-step **workflow**.

The assessments are the main product of ELLA. When the same variant(s) is seen in other samples, the previous interpretation can be reused, saving valuable time.

In general, ELLA has an append-only data model, where no data is deleted or overwritten. Instead, an updated copy is made and the versions are linked.

ELLA is built as a web application with a frontend and backend. The frontend runs fully in the user's browser, while the backend runs on a server. The frontend communicates with the backend via a JSON-based REST API.

<div class="figure_text">
    <img src="./img/system.png">
    <p><strong>Figure: </strong>High-level system diagram of ELLA.</p>
</div>

## Frontend

The frontend is written in javascript, using:

- SASS for CSS
- [AngularJS](https://angularjs.org/)
- [Cerebral](http://cerebraljs.com/) for client side state management.

## Backend

The backend is written in Python and built using [Flask](http://flask.pocoo.org/).

## Database

ELLA uses a relational [PostgreSQL](https://www.postgresql.org/) database with the data model defined using [SQLAlchemy](https://www.sqlalchemy.org/).

## Command line interface (ella-cli)

Most admin tasks in ELLA are handled using the ELLA command line interface (ella-cli). This is located in `bin/ella-cli`, but should be available in `$PATH` if you use a Docker image. For available options, see [Production tasks using the ella-cli](/technical/production-tasks.md) or type `ella-cli --help`.

