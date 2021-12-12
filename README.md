# homeassistant-prometheus-query

Inspired from homeassitant Command line Sensor this sensor take values from [Prometheus](https://prometheus.io/) metrics using [PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/) query .  It allow to specify one or more query creating a sensors for each query.

## Configuration

To enable it, add the following lines to your `configuration.yaml`:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: prometheus_query
    name: Temperature Pisa
    unique_id: sensorEntityId
    prometheus_url: http://localhost:9090
    prometheus_query: temperature{location="Pisa",province="PI",region="Tuscany"}
    unit_of_measurement: "°C"
    state_class: total_increasing
    device_class: temperature
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


It's a custom component so it must be downloaded under /custom_components folder.
