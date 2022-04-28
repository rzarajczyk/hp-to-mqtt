from apscheduler.schedulers.blocking import BlockingScheduler
from homie_helpers import MqttSettings

from PrinterScanner import PrinterScanner
from bootstrap.bootstrap import start_service

from datetime import datetime

config, logger, timezone = start_service()

scheduler = BlockingScheduler(timezone=timezone)

device = PrinterScanner(config=config['hp'], mqtt_settings=MqttSettings.from_dict(config['mqtt']))

scheduler.add_job(device.refresh, 'interval', seconds=config['fetch-interval-seconds'], next_run_time=datetime.now())

scheduler.start()
