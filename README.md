# v4vapp-hive-pricefeed
This is a simple price feed for a Hive Witness to run.

## Development setup with uv

This project now uses `uv` for dependency management. To prepare a local environment, install `uv` and run:

```shell
uv sync --locked --no-install-project
```

Then use `uv run` to execute commands in the project environment, for example:

```shell
uv run python src/v4vapp_hive_pricefeed/pricefeed.py
```

If you prefer to run `python` directly, first activate the project virtual environment (for example `source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\activate` on Windows), otherwise the system Python may not see the installed dependencies.

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

The `.env` file should be in the same directory as your `docker-compose.yml` file, and the relevant section of that file should look like this:
```
HIVE_WITNESS_NAME=hive-witness-name
HIVE_WITNESS_ACTIVE_KEY=hive-witness-active-key
```


```yaml
services:

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

## Price feed update rules

The feed is updated when any of these are true:

- `price_feed.json` does not exist
- the previous data does not contain a valid `base` price
- the previous data does not contain a valid `timestamp`
- the new `base` price differs from the previous one by at least `2%`
- the previous feed is older than `12 hours`

### Fallbacks

- if `price_feed.json` is missing, malformed, or missing the required fields → update
- if any exception occurs while checking the old feed → update

So business rule: publish only when the new price has changed by at least 2% or the last published price is older than 12 hours.
