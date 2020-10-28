# homeassistant-prometheus-query
Inspired from homeassitant Command line Sensor this sensor take values from [Prometheus](https://prometheus.io/) metrics using [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/) query .  It allow to specify one or more query creating a sensors for each query.

## Configuration

To enable it, add the following lines to your `configuration.yaml`:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: prometheus-query
    name: Temperature Pisa
    prometheus_url: http://localhost:9090
    prometheus_query: temperature{location="Pisa",province="PI",region="Tuscany"}
    unit_of_measurement: "°C"
```

### Configuration Variables

-  name

  (string)(Required) Name of the sensor..

-  prometheus_url

  (string)(Required) the url of your Prometheus server

-  prometheus_query

  (string)(Required) the PromQL query to retrieve sensor 

-  unit_of_measurement

  (string)(Optional) Defines the unit of measurement of the sensor, if any.

It's a custom component so it must be downloaded under /custom_components folder.
