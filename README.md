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
- is providing an endpoint to read to the database (with caching!);

The backend has workers that:
- consume the messages and write some stuff in DB;
- will generate new messages sent to the MQ.

You'll need to run backend and frontend - feel free to use multiple terms for this

```sh
$ poetry run backend/main.py
$ poetry run frontend/main.py
```

You can now simulate random traffic.

```sh
$ poetry run traffic/main.py
```

If everything is working, you should be ready to add metrics into the code!

## Exercices

### Exercise 0: Preparing the code to handle metrics

If you heard correctly the presentation, you now know metrics are not "sent" to Prometheus, but rather "exposed".
You'll then need to first add the required library to the project, then expose the metrics endpoint.

On the frontend, it will cause no issue as a web server is already running. You'll just need to add the metrics endpoint.

On the backend, there is no web server running, so you'll need to add one.

#### Walkthrough

Prior to adding metrics, we then need to prepare the code to handle them. You'll need to include the `prometheus_client` library in the project. Try `poetry add prometheus_client`.

Then, on the frontend, you'll add the wsgi application to flask. You can find code on [Prometheus' Flask documentation](https://prometheus.github.io/client_python/exporting/http/flask/).

Code to add in `frontend/main.py`:

```python
+from prometheus_client import make_wsgi_app
+from werkzeug.middleware.dispatcher import DispatcherMiddleware
+
 app = Flask(__name__)
+# Add prometheus wsgi middleware to route /metrics requests
+app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
+    '/metrics': make_wsgi_app()
+})
```

On the backend, just import the `prometheus_client` library and add the metrics endpoint.

```python
...
+from prometheus_client import start_http_server
...

 def start():
     app = Engine()
+    start_http_server(5001)
     app.main()
```

If you've done everything correctly, you should be able to reach the metrics endpoint on the frontend at `http://localhost:5000/metrics`, and on the backend at `http://localhost:5001/metrics`. Just take a look at the metrics, you'll see some basic metrics are already there, like CPU usage, memory usage, opened FDs, python version, etc.


### Exercise 1: Add a counter metric

A counter is a metric that represents a single incrementing counter. It can only go up, and is reset to 0 when the process restarts. It's used to count events or operations, as web queries, database queries, etc.

In the frontend, you'll add a counter that will count the number of requests to the `/fruit` endpoint.

You only have 2 things to do:

- Declare the counter in the frontend code;
- Increment the counter when a request is made to the `/fruit` endpoint.

Declare the counter in the frontend code:

```python
HELLO_COUNTER = Counter('hello_total', 'Total number of hello requests')
```

Increment the counter when a request is made to the `/fruit` endpoint:

```python
HELLO_COUNTER.inc()
```

Restart the frontend, run a few queries, and you should see the counter incrementing.


### Exercise 2: Add a gauge metric

A Gauge is a metric that represents a single numerical value that can go up and down. It's used to represent things like the number of active users, the current memory usage, etc.

In the frontend, you'll add a gauge that will represent the total quantity of recently inserted fruits in the database. Check the code. If no fruit is provided, it will return the total quantity of all fruits.

You only have 2 things to do:

- Declare the gauge in the frontend code;
- Set the gauge value when a request is made to the `/fruit` endpoint.

Declare the gauge in the frontend code:

```python
ALL_FRUITS_GAUGE = Gauge('all_fruits', 'Total number of recent fruits in the database')
```

Set the gauge value when a request is made to the `/fruit` endpoint:

```python
ALL_FRUITS_GAUGE.set(total_quantity)
```

Restart the frontend, run a few queries, and you should see the gauge value updating.


### Exercise 3: Add a gauge with labels

In the last exercise, you've added a gauge that will represent the total quantity of recently inserted fruits in the database.

Now, you'll add a gauge that will represent the total quantity of recently inserted fruits for each fruit.

You only have 2 things to do:

- Declare the gauge in the frontend code, with labels;
- Set the gauge value when a request is made to the `/fruit` endpoint.

Declare the gauge in the frontend code:

```python
RECENT_FRUITS_GAUGE = Gauge('recent_fruits', 'Total number of recent fruits in the database', ['fruit'])
```

Set the gauge value when a request is made to the `/fruit` endpoint:

```python
RECENT_FRUITS_GAUGE.labels(fruit_name).set(total_quantity)
```

You can add multiple labels to any kind of metrics. Remember that labels are key/value pairs, and you can use them to filter metrics in Grafana, and you still can aggregate them if needed.


### Exercice 4: Histograms

Histograms are a bit more complex than the other metrics. They are used to represent a histogram of values in a given range. It's used to represent things like the latency of a request or a database query, size of files uploaded to a blob storage, etc.

In our samples, we can add histograms to represent the latency of a request to http endpoints, workers job duration, etc.

I propose to add histograms to all endpoints, making use of labels to track metrics by method and endpoint.

Again, you only have 2 things to do:

- Declare the histogram in the frontend code;
- Set the histogram value when a request is made to the `/fruit` endpoint.

Declare the histogram in the frontend code:

```python
HTTP_LATENCY_HISTOGRAM = Histogram('http_latency', 'Histogram of HTTP latencies', ['method', 'endpoint'])
```

Set the histogram value when a request is made to the `/fruit` endpoint. They are defined as decorators, so you can use them to wrap any function.

```python
@app.route('/hello', methods=['GET'])
@HTTP_LATENCY_HISTOGRAM.labels(method='GET', endpoint='/hello')
def hello():
...

@HTTP_LATENCY_HISTOGRAM.labels(method='GET', endpoint='/fruit')
...

@HTTP_LATENCY_HISTOGRAM.labels(method='POST', endpoint='/fruit')
...

```

Again, restart the frontend, run a few queries, and check the metrics endpoint. You should see the histograms being populated; It will look like this:

```
http_latency_count{endpoint="/fruit",method="GET"} 0.0
http_latency_sum{endpoint="/fruit",method="GET"} 0.0
http_latency_bucket{endpoint="/fruit",le="0.005",method="GET"} 0.0
http_latency_bucket{endpoint="/fruit",le="0.01",method="GET"} 0.0
http_latency_bucket{endpoint="/fruit",le="0.025",method="GET"} 0.0
http_latency_bucket{endpoint="/fruit",le="0.05",method="GET"} 1.0
http_latency_bucket{endpoint="/fruit",le="0.075",method="GET"} 1.0
...
```

### Exercice 5: Add a summary metric

Summary metrics are a bit more complex than histograms. They are used to represent the distribution of values in a given range. It's used to represent things like the latency of a request or a database query, size of files uploaded to a blob storage, etc. The difference with histograms is that summary metrics are not split into buckets, but rather represent the distribution of values.

I'll let you add a summary metric to the backend, representing the duration of the workers job. Have fun!


### Exercice 6: Using prometheus

So, until now, you've added metrics to the code, but you haven't used them in Prometheus or Grafana. If you've run docker-compose, you should have a prometheus instance running, and you should be able to see the metrics in the Prometheus UI as the backend and frontend endpoints are already configured in Prometheus.

Prometheus is reachable at `http://localhost:9090/query`.

In the Status -> Targets page, you should see the targets being scraped.

In the Graph page, you can write queries to see the metrics. Try it yourself! You can query the metrics you've added, and you should see them in the graph:

- hello_total
  - rate(hello_total[1m])

- recent_fruits
  - count(recent_fruits)
  - sum(recent_fruits)

- http_latency
  - sum(http_latency_count)
  - histogram_quantile(0.5, sum(rate(http_latency_bucket[5m])) by (le))
  - histogram_quantile(0.95, sum(rate(http_latency_bucket[5m])) by (le))

Other queries can be run, such as:

- count by(job) ({__name__=~".+"})
- {job="frontend"}


### Exercise 7: Using Grafana

Grafana is reachable at `http://localhost:3000/`.

You can create a new dashboard, and add panels to it. You can also add alerts to the dashboard, and you can create a new datasource to connect to Prometheus.

On first login, you'll be asked to create a new password. Try admin/admin if it asks for a password.

You'll need to connect Grafana with Prometheus. Add a Connection (Connections/Data sources), add a Prometheus datasource that targets `http://localhost:9090/`.

It is time to create a dashboard. with the metrics you've added so far.

Some ideas:
- A panel with the total number of fruits inserted in the database;
- A panel with the total number of fruits inserted in the database, split by fruit;
- A panel with the latency of the `/hello` and `/fruit` endpoints;
- A panel with the number of requests to the `/hello` and `/fruit` endpoints;

It works the same way as the Prometheus UI, you can write queries:
- Click on the "Explore" button;
- Write a query to get the total number of fruits inserted in the database;

If you're ready, now is the time to create a dashboard.
- Click on the "Dashboards" button in the menu;
- Click on "New" then "New Dashboard" to create a new dashboard;
- Add a visualisation panel, select the Prometheus datasource, and write a query (ex: `sum(recent_fruits)`);
- You can add other queries in the same panel. Try it yourself by adding the query `recent_fruits{fruit="banana"}`;
- It is possible to tweak the label, the panel settings (min/max, colors, legends, etc.);


### Exercise 8: Grafana opensource dashboards

There is quite a lot of opensource dashboards available, and you can find a lot of them on [Grafana Labs's website](https://grafana.com/grafana/dashboards/).

Try to import one, and see how it looks like. We're running RabbitMQ, Postgres, Redis and Prometheus, so you can find a lot of dashboards that will help you understand how everything works together.


### Exercice 9: Alerting

This part is yet to be done.
