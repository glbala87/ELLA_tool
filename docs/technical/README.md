# Introduction


[[toc]]

ELLA is a tool for clinical interpretation of genetic variants.

The users will either interpret a **single variant** or several variants belonging together in an analysis.

The result of the interpretation work are **assessments** that include the classification of the variant (1-5, T). The assessments are the product of ELLA. When the same variant(s)  is seen in other samples the previous interpretation work can be reused, saving valuable time.

The interpretation work must be approved by another person in multi-step **workflow**.

In general ELLA has an append-only data model, where no data is deleted or overwritten. Instead an updated copy is made and the versions are linked.

**High-level system diagram of ELLA:**

<br>
<div style="text-align:center"><img src="./img/system.png"></div>

ELLA is built as a web application, divided between a frontend and a backend. The frontend runs fully in the user's browser, while the backend runs on a server. The frontend communicates with the backend via a JSON based REST API.

## Frontend
The frontend is written in javascript, using:

- SASS for CSS
- [AngularJS](https://angularjs.org/)
- [Cerebral](http://cerebraljs.com/) for client side state management.

## Backend
The backend written in Python, built using [Flask](http://flask.pocoo.org/).

## Database
ELLA uses a relational database [PostgreSQL](https://www.postgresql.org/) with the data model
defined using [SQLAlchemy](https://www.sqlalchemy.org/)

## Command line interface
ELLA has command line tool (using [Click](http://click.pocoo.org/)) to import gene panels, users and variants.
