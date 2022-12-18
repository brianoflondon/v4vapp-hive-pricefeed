# v4vapp-hive-pricefeed
This is a simple price feed for a Hive Witness to run.

## Running from DockerHub

As long as you already have Docker installed on your machine, the following command line will work

```shell
docker run -d --name=v4vapp-pricefeed \
    --restart unless-stopped \
    --env HIVE_WITNESS_NAME=your_witness_name \
    --env HIVE_WITNESS_ACTIVE_KEY=your_witness_active_key  \
    brianoflondon/v4vapphivepricefeed:latest
```

Once it is running you can check on it with `docker logs v4vapp-pricefeed -f` to stream the logs. If you want to stop it, `docker stop v4vapp-pricefeed` will do that.

## Running in Docker Compose

If you want to use Docker Compose there is an example in this repo. There is also a sample `.sample.env` file: edit this with your Witness name and key, save it as `.env` and you should be good to go.

```yaml
  pricefeed:
    container_name: v4vapp-pricefeed
    image: brianoflondon/v4vapphivepricefeed:latest
    logging:
      driver: "json-file"
      options:
          max-file: "5"
          max-size: "10m"
    env_file:
      - ".env"
    restart: unless-stopped
```
