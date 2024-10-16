import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from lighthive.client import Client
from lighthive.datastructures import Operation
from lighthive.exceptions import RPCNodeException
from single_source import get_version

__version__ = get_version(__name__, Path(__file__).parent.parent)

HIVE_WITNESS_NAME = os.getenv("HIVE_WITNESS_NAME")
HIVE_WITNESS_ACTIVE_KEY = os.getenv("HIVE_WITNESS_ACTIVE_KEY")
PRICE_FEED_MIN_PUBLISH_TIME_HOURS = 12
PRICE_FEED_MIN_PERCENTAGE_DELTA = 0.02


class HiveKeyError(Exception):
    pass


class V4VApiError(Exception):
    pass


def price_feed_update_needed(base: float) -> bool:
    """
    Check if previous run of price feed has put an output file down and the
    age of the feed is less than 12 hours.
    Returns false if there is no need to update the feed.
    """
    try:
        if os.path.isfile("price_feed.json"):
            with open("price_feed.json", "r") as f:
                prev_ans = json.load(f)
                prev_base = prev_ans.get("base")
                prev_timestamp = prev_ans.get("timestamp")
            if prev_base and prev_timestamp:
                per_diff = abs(base - prev_base) / ((base + prev_base) / 2)
                quote_timediff = timedelta(
                    seconds=int(datetime.utcnow().timestamp() - prev_timestamp)
                )
                if abs(per_diff) < 0.02 and quote_timediff.total_seconds() < (
                    12 * 3600
                ):
                    logging.info(
                        f"Price feed un-changed  | Base Now: {base:.3f} | "
                        f"Prev Base: {prev_base:.3f} | "
                        f"Change: {per_diff*100:.1f} % | "
                        f"Age: {quote_timediff}"
                    )
                    return False
                else:
                    logging.info(
                        f"Price feed needs update | Base Now: {base:.3f} | "
                        f"Prev Base: {prev_base:.3f} | "
                        f"Change: {per_diff*100:.1f} % | "
                        f"Age: {quote_timediff}"
                    )
    except Exception as ex:
        logging.error(f"Problem checking old feed price {ex}")
    return True


async def publish_feed(publisher: str = "brianoflondon"):
    """Publishes a price feed to Hive"""
    try:
        headers = {"user-agent": f"v4vapp-pricefeed/{__version__}"}
        resp = httpx.get(
            "https://api.v4v.app/v1/cryptoprices/?use_cache=true&pricefeed=true",
            headers=headers,
        )
        if resp.status_code == 200:
            rjson = resp.json()
            base: float = rjson["v4vapp"]["Hive_HBD"]
            if price_feed_update_needed(base):
                client = Client(
                    keys=[HIVE_WITNESS_ACTIVE_KEY],
                )
                client.node_list.append("https://rpc.podping.org/")
                client.current_node = "https://rpc.podping.org"
                logging.info(f"Trying to publish via node: {client.current_node}")
                op = Operation(
                    "feed_publish",
                    {
                        "publisher": publisher,
                        "exchange_rate": {
                            "base": f"{base:.3f} HBD",
                            "quote": "1.000 HIVE",
                        },
                    },
                )
                trx = client.broadcast_sync(op=op, dry_run=False)
                logging.info(
                    f"Price feed published: {trx} via node: {client.current_node}"
                )
                with open("price_feed.json", "w") as f:
                    json.dump(
                        {"base": base, "timestamp": datetime.utcnow().timestamp()}, f
                    )
        else:
            logging.error("Problem with api.v4v.app")
            raise V4VApiError(resp)

    except ValueError as ex:
        if ["Error loading Base58 object" in arg for arg in ex.args]:
            logging.error(
                "Hive Active key is not a valid Base58 key, check and try again."
            )
            raise HiveKeyError
        logging.error(ex)
        raise HiveKeyError

    except AssertionError as ex:
        logging.error(f"Another Hive Key error: {ex}")
        raise HiveKeyError

    except RPCNodeException as ex:
        if ["Missing Active Authority" in arg for arg in ex.args]:
            logging.error(
                f"Given Active Key does not have correct authority for {publisher}"
            )
            raise HiveKeyError
        logging.error(ex)

    except (httpx.ConnectError, httpx.ReadTimeout, V4VApiError, TimeoutError) as ex:
        logging.error(ex)
        raise

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Exception publishing price feed: {ex}")
        raise


async def keep_publishing_price_feed():
    """
    Publishes a price feed for my witness, this will move to its own project soon
    """
    failure_stop = 20
    errors = 0
    while True:
        try:
            success = await publish_feed(HIVE_WITNESS_NAME)
            errors = 0
            await asyncio.sleep(60 * 15)
        except HiveKeyError:
            errors += 1
            break
        except (httpx.ConnectError, httpx.ReadTimeout, V4VApiError) as ex:
            sleep_time = 10 + 5 * errors**2
            logging.error(
                f"Problem connecting to api.v4v.app: {ex} | "
                f"Failure: {errors+1} | Sleeping: {sleep_time}s"
            )
            errors += 1
            await asyncio.sleep(sleep_time)
        except Exception as ex:
            errors += 1
            logging.exception(ex)
        finally:
            if errors > failure_stop - 1:
                logging.error(f"{failure_stop} Failures, sorry we have to stop.")
                break


async def main_loop():
    logging.info("Main Loop")
    async with asyncio.TaskGroup() as tg:
        publish_feed_task = tg.create_task(keep_publishing_price_feed())


if __name__ == "__main__":
    debug = False
    logging.basicConfig(
        level=logging.INFO if not debug else logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(module)-14s %(lineno) 5d : %(message)s",
        datefmt="%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )
    logging.info(f"-------V4VAPP Hive Pricefeed Version {__version__}  -")
    logging.info(f"Starting at {datetime.now()}")

    if not HIVE_WITNESS_ACTIVE_KEY or not HIVE_WITNESS_NAME:
        logging.error(
            "Hive Witness Active Key or Witness Name not set, check Environment or .env file and try again."
        )
        raise SystemExit(
            "Hive Witness Active Key or Witness Name not set, check Environment or .env file and try again."
        )

    # logging.info(f"Testnet: {os.getenv('TESTNET')}")

    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logging.info("Terminated with Ctrl-C")
    except asyncio.CancelledError:
        logging.info("Asyncio cancelled")

    except Exception as ex:
        logging.exception(ex)
        logging.error(ex)
