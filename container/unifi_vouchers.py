"""
SPDX-License-Identifier: GPL-3.0-or-later

A FastAPI base interface for interacting with the Unifi Controller to generate new guest access vouchers.

This script allows for passing several environmental variables for configuration
MongoDB:
    MONGO_HOST -- The hostname of the mongo instance to connect to
    MONGO_PORT -- The port of the mongo instance to connect to; defaults to 27017
    MONGO_DB -- The mongo database to use
Unifi:
    UNIFI_SITE -- The site for which the vouchers will be associated with.  This can be overridden on the request
    UNIFI_DURATION -- The duration which the voucher is good for
    UNIFI_ADMIN_NAME -- The user that created voucher, it doesn't need to exist
    UNIFI_NOTE -- An opaque note to attach to the voucher
"""

import datetime
import os
import random
import typing

import fastapi
import pydantic
import pymongo

# pull in environment variables used as configuration
env_site: str = os.environ.get("UNIFI_SITE", "")
env_duration: int = int(os.environ.get("UNIFI_DURATION", 480))
env_admin_name: str = os.environ.get("UNIFI_ADMIN_NAME", "")
env_note: str = os.environ.get("UNIFI_NOTE", "")
env_mongo_host: str = os.environ.get("MONGO_HOST", "")
env_mongo_port: int = int(os.environ.get("MONGO_PORT", 27017))
env_mongo_db: str = os.environ.get("MONGO_DB", "")


def gen_timestamp() -> int:
    """
    Returns the current timestamp in seconds
    """
    return int(datetime.datetime.utcnow().strftime("%s"))


def gen_code() -> str:
    """
    Returns a random number between 0 and 9999999999
    """
    # pylint suggests using an f-string but not sure how to do this
    return "{0:0<10}".format(random.randint(0, 9999999999))  # pylint: disable=C0209


class VoucherBase(pydantic.BaseModel):
    """
    Base pydantic model for a `voucher`

    This includes the common fields that would be needed to create a new record

    As of v6.5.55 a db entry looks like the following
    {
        '_id': ObjectId('73c53a551ed7970033b2af52'),
        'site_id': '73ba27e163445900334f0105',
        'create_time': 1640315477,
        'code': '7155729837',
        'for_hotspot': False,
        'admin_name': 'user',
        'quota': 1,
        'duration': 1440,
        'used': 0,
        'qos_overwrite': False,
        'note': 'n'
    }

    _id -- MongoDB generated id field
    site_id -- This is the _id field from the `site` table, there is a helper function to do a lookup
    create_time -- Unix epoch time that the voucher was/is created
    code -- A ten digit string used as the voucher code
    admin_name -- Name of the user that created the voucher; this user doesn't need to exist in the system
    quota -- Number of times this voucher can be used
    duration -- Time in minutes that the client can be active
    note -- An opaque field that can be used to store additional information with/about the voucher
    """

    site_id: typing.Optional[str]
    # These need to be dynamic values, so we need to use a callable, see pydantic #866
    create_time: int = pydantic.Field(default_factory=gen_timestamp)
    code: str = pydantic.Field(default_factory=gen_code)
    for_hotspot: bool = False
    admin_name: str = env_admin_name
    quota: int = 1
    duration: int = env_duration
    used: int = 0
    qos_overwrite: bool = False
    note: str = env_note


class VoucherCreate(VoucherBase):
    """
    Pydantic model for creating a `voucher`

    As of v6.5.55 there are no additional fields when creating an entry
    """


class Voucher(VoucherBase):
    """
    Pydantic model for returning a `voucher`

    As of v6.5.55 there are no additional fields returned from the db for a voucher entry
    """

    # There is a known issue with pydantic and mongo's _id field
    # https://github.com/tiangolo/fastapi/issues/1515
    # that is not handled today
    # id: PyObjectId = pydantic.Field(alias="_id")


def lookup_site_id(site: str) -> typing.Union[None, str]:
    """
    Function looks up a unifi site and returns the id

    This is only used internally and allows sites to be referenced via their description/friendly name
    """
    mongo_client = pymongo.MongoClient(env_mongo_host, env_mongo_port)
    mongo_db = mongo_client[env_mongo_db]
    result = mongo_db["site"].find_one({"desc": site})
    if result is None:
        return None

    return str(result["_id"])


app = fastapi.FastAPI(title="Unifi Vouchers")


@app.post("/voucher/new", response_model=Voucher)
async def voucher_new(voucher: VoucherCreate, site: typing.Optional[str] = None) -> Voucher:
    """
    Creates a new voucher and returns the object

    Optionally, site can be included as a parameter to override the environment variable. This does introduce the
    potential for abuse as someone could try to identify different site names. At this time the risk feels low as this
    shouldn't be exposed directly to the internet or untrusted users.
    """
    site_id = lookup_site_id(env_site)
    if site is not None:
        site_id = lookup_site_id(site)
    if site_id is None:
        raise fastapi.HTTPException(status_code=400, detail="Could not find specified site")

    # remap site_id to the looked up value
    voucher.site_id = str(site_id)

    mongo_client = pymongo.MongoClient(env_mongo_host, env_mongo_port)
    mongo_db = mongo_client[env_mongo_db]
    i_result = mongo_db["voucher"].insert_one(voucher.dict(by_alias=True))
    q_result = mongo_db["voucher"].find_one({"_id": i_result.inserted_id})

    return q_result  # type: ignore
