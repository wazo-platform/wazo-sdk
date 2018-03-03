# wazo-sdk

Developer tool kit for Wazo development


## Configuration

The default location of the configuration file is `~/.config/wdk/config.yml` you can check
`config.yml.sample` for an example.

If you wish to use another location for you configuration file you can use the `--config` flag
when launching `wdk` or set the `WDK_CONFIG_FILE` environment variable to the config file location.



## Mounting a project on a remove server

```sh
wdk --hostname <wazo-host> --dev-dir <local-source> mount <project>
```
