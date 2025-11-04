# homeassistant-prometheus-query

Inspired from homeassitant Command line Sensor this sensor take values from [Prometheus](https://prometheus.io/) metrics using [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/) query .  It allow to specify one or more query creating a sensors for each query.

## Configuration

To enable it, add the following lines to your `configuration.yaml`:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: prometheus_query
    name: "Temperature Pisa"
    unique_id: "tempPisa"
    prometheus_url: http://localhost:9090
    prometheus_query: temperature{job="cfrt",location=~"Pisa Fac Agraria.*",province="PI",region="Toscana"}
    unit_of_measurement: "°C"
  - platform: prometheus_query
    name: "Temperature Cecina"
    unique_id: "tempCecina"
    prometheus_url: http://localhost:9090
    prometheus_query: temperature{job="cfrt",location=~"Cecina.*",province="LI",region="Toscana"}
    unit_of_measurement: "°C"
  - platform: prometheus_query
    name: "Wind Quercianella"
    unique_id: "windQuercianella"
    prometheus_url: http://localhost:9090
    prometheus_query: wind_speed{job="cfrt",location="Quercianella",province="LI",region="Toscana"} * 3.6

sensor single_query: 
  - platform: prometheus_query
    name: "Temperatures"
    unique_id: "temps"
    prometheus_url: http://localhost:9090
    prometheus_query: temperature{region="Toscana"}
    unit_of_measurement: "°C"
    unique_instance_key: location
    scan_interval: 00:30:00
    monitored_instances:
      - instance_name: Pisa Fac Agraria
        name: Pisa Fac Agraria Temperature
      - instance_name: Cecina
        name: Cecina Temperature
```

### Configuration Variables

- name
  
  (string)(Required) Name of the sensor..

- unique_id: sensor Entity Id (See home assitant docs)
  
  (string)(Required if using more than one sensor) Id of the sensor..

- prometheus_url
  
  (string)(Required) the url of your Prometheus server

- prometheus_query
  
  (string)(Required) the PromQL query to retrieve sensor

- unit_of_measurement
  
  (string)(Optional) Defines the unit of measurement of the sensor, if any.

- state_class
  
  (string)(Optional) Defines the type of sensor. `measurement` for metrics that are gauges,`total_increasing` for metrics that are counters.

- device_class
  
  (string)(Optional) Defines the type of device. see [Here](https://github.com/home-assistant/core/blob/master/homeassistant/components/sensor/__init__.py) for device types, such as `energy`, `battery`, `temperature`

- scan_interval

  (timedelta)(Optional) Defines the interval between each polling query, for instance, `00:00:20`, `20` or could be a time perid dict.

- unique_instance_key

  (string)(Optional) which key to use for creating multiple sensors. use in combination with `monitored_instances`, default to `instance`

- monitored_instances

  (list)(Optional) Using alongside query that return multiple value. each item in this list contain `instance_name` and `name`. This is the way to allow one query to update miltiple sensors.

- monitored_instances.instance_name

  (string)(Required) instance name to map to a new sensor

- monitored_instances.name

  (string)(Optional) mapped name of the sensor

It's a custom component so it must be downloaded under /custom_components folder.
