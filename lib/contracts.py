#!/usr/bin/env python3
"""The rules that jobs, validators and tests share, in one place (docs/DATA-PLAN.md step 2).

The numbers live in lib/contracts.json so the Node tests can read them too. Before this, the retry windows were written in photo_registry (180 days) and in each acquire job (90 days), the story limits in the story writer, the place check in build/validate.py and a Node test, and a status list in the code and again in the schema.
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, 'contracts.json'), encoding='utf-8') as _f:
    _C = json.load(_f)

PERMANENT_STATUSES = frozenset(_C['photoPermanentStatuses'])   # a picture that will not appear: kept as a miss for PERMANENT_RETRY_DAYS
PERMANENT_RETRY_DAYS = _C['permanentRetryDays']
TRANSIENT_RETRY_MAX_HOURS = _C['transientRetryMaxHours']   # a failure that may pass (network, quota): tried again after 2^attempts hours, at most this many
SOURCE_RETRY_DAYS = _C['sourceRetryDays']   # a source that found nothing for a place or species is tried again this long after its date

STORY_WORDS = _C['story']['words']; STORY_CHARS = tuple(_C['story']['chars'])
WHY_WORDS = _C['matters']['words']; WHY_CHARS = tuple(_C['matters']['chars'])
