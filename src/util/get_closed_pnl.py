"""Script to fetch closed PnL from Bybit for the past week.

This will help with your retrospective review of what went right and wrong.
"""
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from pybit.unified_trading import HTTP as BybitClient

from src.constants.env import BYBIT_API_KEY, BYBIT_API_SECRET, BYBIT_TESTNET

load_dotenv()

end_time = datetime.now()
start_time = end_time - timedelta(days=7)

start_timestamp = int(start_time.timestamp() * 1000)
end_timestamp = int(end_time.timestamp() * 1000)


def get_closed_pnl() -> list[dict[str, Any]]:
    """Fetch closed PnL data from Bybit for the past week.

    Returns:
        list[dict[str, Any]]: List of closed PnL data.
    """
    try:
        session = BybitClient(
            api_key=BYBIT_API_KEY, api_secret=BYBIT_API_SECRET, testnet=BYBIT_TESTNET
        )

        next_cursor = None
        all_pnl_data = []

        while True:
            params = {
                "category": "linear",
                "startTime": start_timestamp,
                "endTime": end_timestamp,
                "limit": 100,
            }

            if next_cursor:
                params["cursor"] = next_cursor

            response = session.get_closed_pnl(**params)

            if response["retCode"] == 0:
                pnl_list = response["result"]["list"]
                if not pnl_list:
                    break

                all_pnl_data.extend(pnl_list)

                next_cursor = response["result"].get("nextPageCursor")
                if not next_cursor:
                    break
            else:
                print(f"Error fetching data: {response['retMsg']}")
                break

        return all_pnl_data

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []
