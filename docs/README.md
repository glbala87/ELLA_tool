# Introduction

E||a is tool to interpret genetic variants found in patient samples.
 
The users will either interpret a **single variant** or several variants belonging together in an analysis.

The result of the interpretation work are **assessments** that include the
classification of the variant (1-5, T). The assessments are the product of e||a. When the same varithe variant(s)
 is seen in other samples the previous interpretation work can be reused, saving valuable time.

The interpretation work must be approved by another person in multi-step **workflow**.

In general e||a has an append-only data model, where no data is deleted or overwritten.
Instead an updated copy is made and the versions are linked.

Data in: pipeline, deposit, CLI. Types of data. Data stored in database
User updates the database with classification, adding references etc.
Export: dump of all classifications to Excel/XML

Diagram (e||a surroundings):

                                                  +-----+                                             
                                                  |     |                 +-------------+             
               +---------------------+            |     |                 |             |             
               |                     |            |     |                 |             |             
               |                     |            |     |                 |             |             
               |                     |            |  A  |                 |    DB       |             
               |      Web client     |            |  P  |                 |             |             
               |                     |            |  I  |                 |             |             
               |                     |            |     |                 |             |             
               |                     |            | +   |                 |             |             
               |                     |            |     |                 |             |             
               |                     |            |     |                 +-------------+             
               |                     |            |     |                                             
               |                     |            |     |                                             
               +---------------------+            |     |                                             
                                                  |     |        +-----------------------------------+
                                                  |     |        |          CLI                      |
                                                  |     |        |                                   |
                                                  |     |        +-----------------------------------+
                                                  +-----+                                             

     pipeline  --vcf--> deposit --> e||a
     CLI ---vcf, genepanel, users, annotation ---> e||a
     e||a --xml, reports --> user


## The application

ella is built as a web application, divided between a frontend and a backend. The frontend runs fully in the user's browser, while the backend runs on a server. The frontend communicates with the backend via a JSON based REST API.


### Frontend

The frontend is built using [AngularJS](https://angularjs.org/) (v1) as a SPA (single page application).
It's written using Javascript (ES6/ES2015) with [Babel](http://babeljs.io/) transpiling it to into ES5. and SASS for creating CSS.
The client side state is managed by [Cerebral](http://cerebraljs.com/)

### Backend

The backend written in Python, built using [Flask](http://flask.pocoo.org/).

### Database

e||a uses a relational database [PostgreSQL](https://www.postgresql.org/) with the data model  
defined using [SQLAlchemy](https://www.sqlalchemy.org/)

### Command line interface

e||a has command line tool (using [Click](http://click.pocoo.org/)) to import genepanels, users and variants.

