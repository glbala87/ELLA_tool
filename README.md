<div align="center" style="padding-bottom: 20px">
  <a href="http://allel.es">
    <img width="250px" style="border: 0;" src="https://gitlab.com/alleles/ella/raw/dev/docs/logo_blue.svg"/>
  </a>
</div>


ELLA is an analysis tool for interpretation of genetic variants, see http://allel.es for more information.

Most functionality is baked into a Makefile, run `make help` to see a quick overview of available commands.

### Setup demo instance

If you have Docker installed you can bring up a demo instance easily by running

```
make demo
```

This will start a demo instance populated with testdata at http://localhost:3114.
Most interesting test users are `testuser1` and `testuser5`, both with password `demo`.
To stop the demo, run

```
make kill-demo
```

### Production setup

For details on how to setup ELLA for production, please see the [technical documentation](http://allel.es/docs/).

For support and suggestions, [send us an e-mail](ma&#105;lt&#111;&#58;&#101;%6&#67;la&#37;2&#68;s&#117;pport&#64;m&#101;&#100;i&#115;&#105;&#110;&#46;%75i%&#54;F&#46;n%&#54;F)!
