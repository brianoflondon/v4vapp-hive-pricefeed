# v4vapp-hive-pricefeed
This is a simple price feed for a Hive Witness to run.


## Running from DockerHub


```shell
docker run --rm -d --name=v4vapp-pricefeed \
    --env HIVE_WITNESS_NAME=your_witness_name \
    --env HIVE_WITNESS_ACTIVE_KEY=your_witness_active_key  \
    brianoflondon/v4vapphivepricefeed:latest
```