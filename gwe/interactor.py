# This file is part of gwe.
#
# Copyright (c) 2018 Roberto Leinardi
#
# gwe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwe.  If not, see <http://www.gnu.org/licenses/>.
import json
import logging
from distutils.version import LooseVersion
from typing import Optional

import requests
import rx
from injector import singleton, inject
from rx import Observable

from gwe.conf import SETTINGS_DEFAULTS, APP_VERSION, APP_ID
from gwe.model import Setting
from gwe.repository import NvidiaRepository

LOG = logging.getLogger(__name__)


@singleton
class GetStatusInteractor:
    @inject
    def __init__(self, nvidia_repository: NvidiaRepository, ) -> None:
        self._nvidia_repository = nvidia_repository

    def execute(self) -> Observable:
        # LOG.debug("GetStatusInteractor.execute()")
        return rx.defer(lambda _: rx.just(self._nvidia_repository.get_status()))


@singleton
class SetOverclockInteractor:
    @inject
    def __init__(self, nvidia_repository: NvidiaRepository, ) -> None:
        self._nvidia_repository = nvidia_repository

    def execute(self, gpu_index: int, perf: int, gpu_offset: int, memory_offset: int) -> Observable:
        LOG.debug("SetOverclockInteractor.execute()")
        return rx.defer(
            lambda _: rx.just(self._nvidia_repository.set_overclock(gpu_index, perf, gpu_offset, memory_offset)))


@singleton
class SetPowerLimitInteractor:
    @inject
    def __init__(self, nvidia_repository: NvidiaRepository, ) -> None:
        self._nvidia_repository = nvidia_repository

    def execute(self, gpu_index: int, limit: int) -> Observable:
        LOG.debug("SetPowerLimitInteractor.execute()")
        return rx.defer(lambda _: rx.just(self._nvidia_repository.set_power_limit(gpu_index, limit)))


@singleton
class SetFanSpeedInteractor:
    @inject
    def __init__(self, nvidia_repository: NvidiaRepository, ) -> None:
        self._nvidia_repository = nvidia_repository

    def execute(self, gpu_index: int, speed: int = 100, manual_control: bool = True) -> Observable:
        LOG.debug("SetSpeedProfileInteractor.execute()")
        return rx.defer(
            lambda _: rx.just(self._nvidia_repository.set_fan_speed(gpu_index, speed, manual_control)))


@singleton
class SettingsInteractor:
    @inject
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_bool(key: str, default: Optional[bool] = None) -> bool:
        if default is None:
            default = SETTINGS_DEFAULTS[key]
        setting: Setting = Setting.get_or_none(key=key)
        if setting is not None:
            return bool(setting.value)
        return bool(default)

    @staticmethod
    def set_bool(key: str, value: bool) -> None:
        setting: Setting = Setting.get_or_none(key=key)
        if setting is not None:
            setting.value = value
            setting.save()
        else:
            Setting.create(key=key, value=value)

    @staticmethod
    def get_int(key: str, default: Optional[int] = None) -> int:
        if default is None:
            default = SETTINGS_DEFAULTS[key]
        setting: Setting = Setting.get_or_none(key=key)
        if setting is not None:
            return int(setting.value)
        assert default is not None
        return default

    @staticmethod
    def set_int(key: str, value: int) -> None:
        setting: Setting = Setting.get_or_none(key=key)
        if setting is not None:
            setting.value = value
            setting.save()
        else:
            Setting.create(key=key, value=value)

    @staticmethod
    def get_str(key: str, default: Optional[str] = None) -> str:
        if default is None:
            default = SETTINGS_DEFAULTS[key]
        setting: Setting = Setting.get_or_none(key=key)
        if setting is not None:
            return str(setting.value.decode("utf-8"))
        return str(default)

    @staticmethod
    def set_str(key: str, value: str) -> None:
        setting: Setting = Setting.get_or_none(key=key)
        if setting is not None:
            setting.value = value.encode("utf-8")
            setting.save()
        else:
            Setting.create(key=key, value=value.encode("utf-8"))


@singleton
class CheckNewVersionInteractor:
    URL_PATTERN = 'https://flathub.org/api/v1/apps/{package}'

    @inject
    def __init__(self) -> None:
        pass

    def execute(self) -> Observable:
        LOG.debug("CheckNewVersionInteractor.execute()")
        return rx.defer(lambda _: rx.just(self._check_new_version()))

    def _check_new_version(self) -> Optional[LooseVersion]:
        req = requests.get(self.URL_PATTERN.format(package=APP_ID))
        version = LooseVersion("0")
        if req.status_code == requests.codes.ok:
            j = json.loads(req.text)
            current_release_version = j.get('currentReleaseVersion', "0.0.0")
            version = LooseVersion(current_release_version)
        return version if version > LooseVersion(APP_VERSION) else None
