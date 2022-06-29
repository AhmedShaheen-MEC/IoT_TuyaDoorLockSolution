import logging


from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later
from homeassistant.components.lock import SUPPORT_OPEN, LockEntity
from homeassistant.const import ATTR_BATTERY_LEVEL, ATTR_ID, CONF_ACCESS_TOKEN, ATTR_BATTERY_CHARGING, STATE_UNKNOWN

from .const import (DOMAIN,NAME,SCAN_INTERVAL)

from tuya_iot import TuyaOpenAPI, TuyaOpenMQ, TUYA_LOGGER
from threading import Thread
from time import perf_counter

ATTR_CONNECTED = "connected"
ATTR_ENDPOINT = "https://openapi.tuyaeu.com"
ATTR_MQ_ENDPOINT = "wss://mqe.tuyaeu.com:8285/"
ATTR_ALARM = "alarm_notification"
ATTR_UNLOCK_REQUEST = "unlock_requested"
ATTR_WRONG_FINGER_ALARM = "wrong_finger_alarm_status"
ATTR_DYNAMIC_PASSWORD = "dynamic_password_setup"
ATTR_UNLOCKING_WITH_PASSWORD = "unlock_password_setup"
ATTR_ACK_UNLOCK = "ack_unlock"


DOMAIN = "tuya_door_lock"
ATTR_DOMAIN = DOMAIN
EVENT_DOOR_BELL = ATTR_DOMAIN+"_event"

CONF_ACCESS_KEY = "access_key"
CONF_ACCESS_ID = "access_id"

_LOGGER = logging.getLogger(__name__)

# To be corrected:
ATTR_COUNTRY = "DE"
ATTR_APP = "tuyaSmart"
ATTR_USER_NAME = "3estechnologies@gmail.com"
ATT_PASSWORD = "3Es.2020"

async def async_setup_entry(hass, config, async_add_entities):
    id  = config.data.get(CONF_ACCESS_ID)
    key = config.data.get(CONF_ACCESS_KEY)
    id = "nspsumufb9gs5i0317ph"
    key = "ea4dd098102744f986fd510b2a79e077"
    username = ATTR_USER_NAME
    password = ATT_PASSWORD
    country = ATTR_COUNTRY
    app = ATTR_APP
    #_LOGGER.info("Starting Initialization: ID:%s Key:%s",id,key, country , app)
    #try:
    #_LOGGER.info("Calling Tuya client")
    tuya_lock = await hass.async_add_executor_job(lambda : TuyaClient(id, key, password, username, country, app))
    #except :
    #    _LOGGER.error("Tuya Door Lock:: async_setup_entry:: Tuya Lock Was not added")
    #    return
    _LOGGER.debug("available_locks:")
    locks = tuya_lock.getLocks()
    if len(locks) == 0:
        # No locks found; abort setup routine.
        _LOGGER.error("No locks found in your account")
        return

    ## Create thread
   
   # thread.start()
    tuyaLockObj = []
    index = 0
    for lock in locks:
        #await lock.async_updateLock(hass)
        #_LOGGER.info("Update was done")
        tuyaLockObj.append(TuyaLock(lock, hass))

    async_add_entities(tuyaLockObj, True)
    #_LOGGER.info("All Entities has been added")
        


class TuyaLockCloud():
    
    name = "Dummy"
    id = "2189478932579823578"
    battery_level = "High"
    status = False
    alarm_status = False
    features = "UnLock, AlarmNotifications"
    openAPI = "Dummy"
    unlockPasswords = 0
    unlockDynamic = 0
    worngFingerAlarm = "undefined"
    unlcokRequest = 0
    reply = ""
    reply_available = False
    def __init__(self, id, openapi):
        
        self.id      = id
        self.openAPI = openapi
        #_LOGGER.info("Lock was created with ID: %s", self.id)
        #_LOGGER.info("A Lock with Id %s has been update, reply: %s", self.reply)
        
    def getLockName(self):
        # GET Call, get Name
        try:
            if self.reply_available:
                self.name = self.reply["result"]["name"]
        #_LOGGER.info("A Lock has been added named: %s", self.name)
        except:
            pass
        return self.name
    

    def getStatus(self):
        try:
            if self.reply_available:
                _status = self.reply["result"]["online"]
                if (_status == True):
                    self.status = "Online"
                else:
                    self.status = "Offline"
        except:
            pass
        return self.status
    
    def getBatteryLevel(self):
        try:         
            if self.reply_available:
                self.battery_level = self.reply["result"]["status"][7]["value"]
        except:
            pass
        return self.battery_level
        
    def checkUnlockRequiest(self):
        try:
            if self.reply_available:
                self.unlcokRequest = self.reply["result"]["status"][6]["value"]
        except:
            pass
        return self.unlcokRequest     
        
    def checkAlarmLockWrongFinger(self):
        try:        
            if self.reply_available:
                self.worngFingerAlarm = self.reply["result"]["status"][5]["value"]
        except:
            pass
        return self.worngFingerAlarm   
        
    def  getUnlockPasswordSetup(self):
        try:
           if self.reply_available:
                self.unlockPasswords = self.reply["result"]["status"][1]["value"]
        except:
            pass
        return self.unlockPasswords   
        
    def getUnlcokDynamicSetup(self):
        try:
            if self.reply_available:
                self.unlockDynamic = self.reply["result"]["status"][3]["value"]
        except:
            pass        
        return self.unlockDynamic        
        
    async def async_updateLock(self, hass):
        return_code = await hass.async_add_executor_job(self.openAPI.get,"/v1.0/devices/{}".format(self.id))
        self.reply = return_code
        #_LOGGER.info("An Update was done, reply: %s", self.reply)
        self.reply_available = True
        
    def getLockId(self):
        return self.id
    
    async def async_lockUnLock(self, hass):
        """Unlock the door."""
        _LOGGER.warning("The Follwoing Lock was UNLOCKED %s", self.name)
        return_code = await hass.async_add_executor_job(self.openAPI.post,"/v1.0/devices/{}/door-lock/password-ticket".format(self.id))
        try:
            ticket_id    = return_code['result']["ticket_id"]
            ticket_key   = return_code['result']["ticket_key"]
            commands     = {'ticket_id': ticket_id }
            arg = ("/v1.0/devices/{}/door-lock/password-free/open-door".format(self.id), commands)
            return_code  = await hass.async_add_executor_job(self.openAPI.post, arg)
            _LOGGER.warning("Door was unlocked, return code: %s", return_code)
        except:
            pass        
    def isAlarmActivated(self):
        
       return self.alarm_status
       
    def getAvailableFeaturs(self):
        
        return self.features

'''        
def on_message(msg):
    """Handle automation trigger service calls."""
    _LOGGER.info("Tuya Door Lock:: ON MESSAGE:: the follwing msg is received: %s", msg)
    # 1. Door bell:
    #event_data = {
    #    ATTR_ID: self.listOfLockID[0], # Lock
    #    ATTR_ALARM: True
    #}
    #hass.bus.async_fire(EVENT_DOOR_BELL, event_data)     
def msg_listener(self, mq):
    _LOGGER.info("msg_listener Starting Msg Queue")
    
    mq.add_message_listener(on_message)
    mq.start()    
'''
class TuyaClient():
    
    locks = []
    listOfLockID = []
    #openapimq  = []
    def __init__(self, id , key , password, username, country, app):
        self.id    = id
        self.key   = key
        self.username = username
        self.password = password
        self.country = country
        self.app = app
        #_LOGGER.debug("User ID: %s, User Key: %s", self.id, self.key)
        # Call the cloud and parse the comming devices, based devices create objects
        # ID, OPENAPI object
        self.tuyaAPIInitLock()

        
    def getLocks(self):
        return self.locks
      
    def parseResponse(self, attribute):
        pass
    # Should return locks device ID
    # List of dict locks = [ lock_dict, lock2_dict], each dict will contain some attributes
    def tuyaAPIInitLock(self):
        
        openapi = TuyaOpenAPI(ATTR_ENDPOINT, self.id, self.key)
        openapi.connect(self.username, self.password, self.country, self.app)
        openapi.token_info.expire_time = 0
        _LOGGER.info("Creating msg Queue")

        return_code = openapi.get("/v1.0/iot-01/associated-users/devices")
        
        self.listOfLockID = [index["id"] for index in return_code["result"]["devices"] if "WIFI-LOCK" in index["product_name"] or "WIFI智能门锁" in index["product_name"]]
        #_LOGGER.info("List of locks ID: %s", self.listOfLockID)
        for id in self.listOfLockID:
            self.locks.append(TuyaLockCloud(id, openapi))
        #_LOGGER.info("Number of locks: %s", str(len(self.locks)))
        #openapimq = []
        #openapimq.append(self)
        #openapimq.append(TuyaOpenMQ(openapi))
        #thread = Thread(target=msg_listener, args=openapimq)
        #thread.start()
        


class TuyaLock(LockEntity):
    """Representation of a Tuya door  lock."""

    name = ""
    _battery_level = ""
    _available = False
    unlock_requested = 0
    unlock_ack = False
    def __init__(self, tuya_lock, hass):
        _LOGGER.debug("LockEntity: %s", tuya_lock.getLockName())
        """Initialize the lock."""
        self._lock = tuya_lock 
        self.hass = hass

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._lock.getStatus()

    @property
    def name(self):
        """Return the name of the lock."""
        return self._lock.getLockName()

    #@property
    #def battery_level(self):
    #    """Return the name of the lock."""
    #    return self._lock.getBatteryLevel()       
        
    #@property
    #def checkUnlockRequest(self):
    #    """Return the name of the lock."""
    #    return self._lock.checkUnlockRequiest()

    #property
    #def wrong_finger_alarm_status(self):
    #    """Return the name of the lock."""
    #    return self._lock.checkAlarmLockWrongFinger()

    #@property
    #def unlock_password_setup(self):
    #    """Return the name of the lock."""
    #    return self._lock.getUnlockPasswordSetup()
        
    #@property
    #def dynamic_password_setup(self):
    #    """Return the name of the lock."""
    #    return self._lock.getUnlcokDynamicSetup()


    @property
    def extra_state_attributes(self):
#        _LOGGER.info("extra_state_attributes WAStriggered")
        # Call an update to the status first
        return {
            ATTR_BATTERY_LEVEL: self._lock.getBatteryLevel(),
            ATTR_CONNECTED: self._lock.getStatus(),
            ATTR_ALARM: self._lock.isAlarmActivated(),
            ATTR_UNLOCK_REQUEST: self._lock.checkUnlockRequiest(),
            ATTR_WRONG_FINGER_ALARM: self._lock.checkAlarmLockWrongFinger(),
            ATTR_DYNAMIC_PASSWORD: self._lock.getUnlcokDynamicSetup(),
            ATTR_UNLOCKING_WITH_PASSWORD: self._lock.getUnlockPasswordSetup(),
            ATTR_ACK_UNLOCK: self.unlock_ack
        }

    @property
    def is_unlocking(self) -> bool:
        return self.unlock_requested == 1

    @property
    def unique_id(self) -> str:
        return self._lock.getLockId()

    async def async_unlock(self, **kwargs):
        await self._lock.async_lockUnLock(self.hass)

    @property
    def device_info(self):
        # Call an update first
        return {
            "identifiers": {
                (ATTR_DOMAIN, self._lock.getLockId())
            },
            "name": self._lock.getLockName(),
        }

    #def update(self):
        #self._available = self._lock.getStatus()
        #self._battery_level = self._lock.getBatteryLevel()
        #self.name = self._lock.getLockName()
        #self.unlock_requested = 1
    #    if self.unlock_ack:
    #        _LOGGER.info("Unlock was triggered")
    #        self._lock.lockUnLock()
    #        self.unlock_ack = False
    async def async_update(self):

        ''' Perform some update call to the could '''
        await self._lock.async_updateLock(self.hass)
        self.async_schedule_update_ha_state(True)

