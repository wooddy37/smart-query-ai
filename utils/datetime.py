import pytz
from datetime import date, datetime
import pandas as pd

kst = pytz.timezone("Asia/Seoul")
utc = pytz.utc

def utc_to_local(utc_input, fmt="%Y-%m-%d %H:%M:%S"):
    """
    UTC 시간을 KST로 변환하여 문자열 반환.
    문자열 또는 pandas.Series 를 인자로 받을 수 있음.
    """
    if isinstance(utc_input, pd.Series):
        # Series 처리
        utc_dt = pd.to_datetime(utc_input, errors="coerce", utc=True)
        kst_dt = utc_dt.dt.tz_convert(kst)
        return kst_dt.dt.strftime(fmt)
    elif isinstance(utc_input, str):
        # 문자열 처리
        utc_dt = datetime.strptime(utc_input, fmt).replace(tzinfo=pytz.utc)
        return utc_dt.astimezone(kst).strftime(fmt)
    elif isinstance(utc_input, datetime):
        # datetime 객체 처리
        if utc_input.tzinfo is None:
            utc_input = utc_input.replace(tzinfo=pytz.utc)
        return utc_input.astimezone(kst).strftime(fmt)
    else:
        raise TypeError("utc_to_local()은 str, datetime 또는 pandas.Series 타입만 지원합니다.")

def local_to_utc(local_input, fmt="%Y-%m-%d %H:%M:%S"):
    """
    KST 시간을 UTC로 변환하여 문자열 반환.
    문자열, datetime, pandas.Series 지원.
    """
    if isinstance(local_input, pd.Series):
        kst_dt = pd.to_datetime(local_input, errors="coerce").dt.tz_localize(kst)
        utc_dt = kst_dt.dt.tz_convert(utc)
        return utc_dt.dt.strftime(fmt)
    elif isinstance(local_input, str):
        kst_dt = datetime.strptime(local_input, fmt).replace(tzinfo=kst)
        return kst_dt.astimezone(utc).strftime(fmt)
    elif isinstance(local_input, datetime):
        if local_input.tzinfo is None:
            local_input = local_input.replace(tzinfo=kst)
        return local_input.astimezone(utc).strftime(fmt)
    else:
        raise TypeError("local_to_utc()은 str, datetime 또는 pandas.Series 타입만 지원합니다.")