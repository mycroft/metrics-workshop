# metrics-workshop

This little project contains some basic python code (a frontend, a backend) that will be used as a working project in which observability metrics will be added to demonstrate the purpose of adding counter, gauge & histogram metrics.

## Build & run

First, launch the backend/storage components with `docker-compose`:

```sh
$ docker-compose up -d
```

It should launch a bunch of containers with:
- prometheus
- grafana
- rabbitmq
- postgresql
- redis
- a couple of exporters


Verify the state of the stack with:

```sh
$ docker-compose ps
NAME                IMAGE                                          COMMAND                  SERVICE             CREATED         STATUS         PORTS
grafana             grafana/grafana:latest                         "/run.sh"                grafana             5 minutes ago   Up 5 minutes
node_exporter       prom/node-exporter:latest                      "/bin/node_exporter"     node_exporter       5 minutes ago   Up 5 minutes
postgres            postgres:16                                    "docker-entrypoint.s…"   postgres            5 minutes ago   Up 5 minutes
postgres_exporter   prometheuscommunity/postgres-exporter:latest   "/bin/postgres_expor…"   postgres_exporter   5 minutes ago   Up 5 minutes
prometheus          prom/prometheus:latest                         "/bin/prometheus --c…"   prometheus          5 minutes ago   Up 5 minutes
rabbitmq            rabbitmq:4.0.4                                 "docker-entrypoint.s…"   rabbitmq            5 minutes ago   Up 5 minutes

```

All those components are running on localhost as we'll start python code outside the docker environment, and to make sure prometheus fetches everything correctly, running everything using `network_mode: host` really makes things easier.

You can reach the services with the following urls:

- prometheus: http://localhost:9090/query;
- grafana: http://localhost:3000/ (default login/password is admin/admin);
- postgresql: reachable localhost on port 5432. Use login/password demo/demo to connect to the 'demo' database;
- the node exporter is reachable on port 9100 (endpoint /metrics);
- you can check metrics exporters for postgres, rabbitmq on ports 9187 and 15692 (endpoint /metrics).
- redis is running on 6379, and its prometheus exporter is running on 9121.

## Going through the workshop

The workshop is composed of two parts: A frontend part, built with flask, and a backend part, a basic python running a few worker threads.

To be fast, the frontend:
- is providing an endpoint that will push messages to the MQ;
- is providing an endpoint to read to the database;

The backend has workers that:
- consume the messages and write some stuff in DB;
- will generate new messages sent to the MQ.
