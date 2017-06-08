# Introduction


ella is a variant analysis and interpretation tool blablabla


## The application

ella is built as a web application, divided between a frontend and a backend. The frontend runs fully in the user's browser, while the backend runs on a server. The frontend communicates with the backend via a JSON based REST API.


** Frontend **

The frontend is built using [AngularJS](https://angularjs.org/) (v1) as a SPA (single page application). It's written using Javascript (ES6/ES2015 with [Babel](http://babeljs.io/) transpiling it to into ES5) and SASS for creating CSS.

** Backend **

The backend written in Python, built using [Flask](http://flask.pocoo.org/).

** Datamodel **

The datamodel is defined using [SQLAlchemy](https://www.sqlalchemy.org/), and is assuming a PostgreSQL database.
