# contrib/

You'll find here:

- prometheus.yml - used by prometheus when running docker-compose up
- blackbox-exporter.yml - used by blackbox-exporter when running docker-compose up
- dashboard.json - backup of the grafana dashboard

To update dashboard.json, just use the API with login/password basic authentication:

```sh
$ curl http://admin:admin@localhost:3000/api/dashboards/uid/fe6aoi1zpsi68d | jq > dashboard.json
```
