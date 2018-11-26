<div style="text-align: center;padding-top: 50px;padding-bottom: 50px">
	<img width="250px;" src="https://gitlab.com/alleles/ella/raw/dev/docs/logo_blue.svg">
</div>

*ella* is a web app based on AngularJS with a Flask REST backend.

Most functionality is now baked into a Makefile, run `make help` to see a quick overview of available commands.

## Documentation
More info about the app can be found in the docs folder.
The docs are written in Markdown and compiled using [VuePress](https://vuepress.vuejs.org/).

To create a web-based view of the docs:
- install VuePress: `npm install -g vuepress` / `yarn global add vuepress`
- `cd docs`; `vuepress dev` / `vuepress build`
